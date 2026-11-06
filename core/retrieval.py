"""CombustionLens Core: Two-Stage Dense Retrieval & Cross-Encoder Reranking Engine.

Pipeline:
1. Dense Bi-Encoder Retrieval (all-MiniLM-L6-v2): top-20 candidate chunks
2. Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2): top-5 candidate chunks
3. RANK ON RAW LOGITS (no loss of dynamic range)
4. Refusal Gate:
   - If top raw logit < tau_ce -> returns status 'INSUFFICIENT'
   - If tau_ce is null/None -> runs in 'uncalibrated' mode (uncalibrated=True)
5. Sigmoid score is computed for UI DISPLAY ONLY, labelled:
   "Normalized Cross-Encoder Relevance Score" (never a probability or confidence).
"""
import os
import math
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import yaml
from core.config import config_file, data_path

# Lazy loaded models to preserve fast startup & memory
_EMBED_MODEL = None
_RERANK_MODEL = None
_CHROMA_CLIENT = None


def sigmoid(z: float) -> float:
    """Logistic sigmoid transformation for UI display only: sigma(z) = 1 / (1 + exp(-z))."""
    try:
        return 1.0 / (1.0 + math.exp(-z))
    except OverflowError:
        return 0.0 if z < 0 else 1.0


def get_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer(model_name)
    return _EMBED_MODEL


def get_cross_encoder_model(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
    global _RERANK_MODEL
    if _RERANK_MODEL is None:
        from sentence_transformers import CrossEncoder
        _RERANK_MODEL = CrossEncoder(model_name)
    return _RERANK_MODEL


get_cross_encoder = get_cross_encoder_model


def load_retrieval_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    env_config = os.environ.get("COMBUSTIONLENS_CONFIG_PATH")
    if env_config:
        config_path = env_config
    default_config = {
        "top_k_bi": 20,
        "top_k_ce": 5,
        "tau_ce": None,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "cross_encoder_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "chroma_dir": os.environ.get("COMBUSTIONLENS_CHROMA_DIR", "data/index")
    }
    p = config_file(config_path)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                ret = cfg.get("retrieval", {})
                mod = cfg.get("model", {})
                paths = cfg.get("paths", {})
                env_chroma = os.environ.get("COMBUSTIONLENS_CHROMA_DIR")
                return {
                    "top_k_bi": int(ret.get("top_k_bi", default_config["top_k_bi"])),
                    "top_k_ce": int(ret.get("top_k_ce", default_config["top_k_ce"])),
                    "tau_ce": ret.get("tau_ce", None),
                    "embedding_model": mod.get("embedding_model", default_config["embedding_model"]),
                    "cross_encoder_model": mod.get("cross_encoder_model", default_config["cross_encoder_model"]),
                    "chroma_dir": data_path("chroma_dir", "data/index", config_path)
                }
        except Exception:
            return default_config
    return default_config


def retrieve_candidates(
    query: str,
    config_path: str = "config.yaml",
    chroma_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Execute dense retrieval -> cross-encoder reranking -> refusal gate.
    
    Returns:
    {
        "status": "answered" | "insufficient" | "no_corpus",
        "uncalibrated": bool,
        "top_logit": Optional[float],
        "tau_ce": Optional[float],
        "refusal_reason": Optional[str],
        "candidates": List[Dict[str, Any]],
        "nearest_documents": List[Dict[str, Any]]
    }
    """
    cfg = load_retrieval_config(config_path)
    index_path = chroma_dir or cfg["chroma_dir"]
    top_k_bi = cfg["top_k_bi"]
    top_k_ce = cfg["top_k_ce"]
    tau_ce = cfg["tau_ce"]
    
    # 1. Connect to ChromaDB
    try:
        import chromadb
        client = chromadb.PersistentClient(path=index_path)
        collections = client.list_collections()
        col_names = [c if isinstance(c, str) else getattr(c, "name", str(c)) for c in collections]
        if "combustion_papers" not in col_names:
            return {
                "status": "no_corpus",
                "uncalibrated": tau_ce is None,
                "top_logit": None,
                "tau_ce": tau_ce,
                "refusal_reason": "Vector index 'combustion_papers' not found. Corpus is empty.",
                "candidates": [],
                "nearest_documents": []
            }
        collection = client.get_collection("combustion_papers", embedding_function=None)
        total_docs = collection.count()
        if total_docs == 0:
            return {
                "status": "no_corpus",
                "uncalibrated": tau_ce is None,
                "top_logit": None,
                "tau_ce": tau_ce,
                "refusal_reason": "Vector index contains 0 documents. Ready for human data drop.",
                "candidates": [],
                "nearest_documents": []
            }
    except Exception as e:
        return {
            "status": "no_corpus",
            "uncalibrated": tau_ce is None,
            "top_logit": None,
            "tau_ce": tau_ce,
            "refusal_reason": f"ChromaDB connection note: {e}",
            "candidates": [],
            "nearest_documents": []
        }

    # 2. Dense retrieval top-k
    bi_encoder = get_embedding_model(cfg["embedding_model"])
    query_emb = bi_encoder.encode([query]).tolist()
    
    actual_k = min(top_k_bi, total_docs)
    res = collection.query(
        query_embeddings=query_emb,
        n_results=actual_k,
        include=["documents", "metadatas", "distances"]
    )
    
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]
    
    if not docs:
        return {
            "status": "insufficient",
            "uncalibrated": tau_ce is None,
            "top_logit": None,
            "tau_ce": tau_ce,
            "refusal_reason": "No candidate chunks retrieved from vector store.",
            "candidates": [],
            "nearest_documents": []
        }

    # 3. Cross-Encoder Reranking
    cross_encoder = get_cross_encoder_model(cfg["cross_encoder_model"])
    pairs = [[query, doc] for doc in docs]
    # Bound attention memory when running the public CPU demo.
    raw_logits = cross_encoder.predict(pairs, batch_size=4)
    
    # Bundle items with raw logit and display sigmoid
    reranked = []
    for doc, meta, logit, dist in zip(docs, metas, raw_logits, distances):
        flt_logit = float(logit)
        p_raw = meta.get("page_number")
        p_num = int(p_raw) if p_raw is not None and str(p_raw).isdigit() else None
        item = {
            "text": doc,
            "doc_id": meta.get("doc_id", "unknown"),
            "title": meta.get("title") or meta.get("doc_id"),
            "authors": meta.get("authors"),
            "year": meta.get("year"),
            "section": meta.get("section", ""),
            "page_number": p_num,
            "campaign_or_series": meta.get("campaign_or_series"),
            "research_group_label": meta.get("research_group_label"),
            "source_type": meta.get("source_type"),
            "peer_reviewed": meta.get("peer_reviewed"),
            "raw_logit": round(flt_logit, 4),
            "normalized_relevance_score": round(sigmoid(flt_logit), 4),
            "cosine_distance": round(float(dist), 4)
        }
        reranked.append(item)
        
    # RANK ON RAW LOGITS descending
    reranked.sort(key=lambda x: x["raw_logit"], reverse=True)
    top_candidates = reranked[:top_k_ce]
    top_logit = top_candidates[0]["raw_logit"] if top_candidates else None

    # 4. Refusal Gate Evaluation
    uncalibrated_mode = (tau_ce is None)
    
    if not uncalibrated_mode and top_logit is not None:
        if top_logit < float(tau_ce):
            return {
                "status": "insufficient",
                "uncalibrated": False,
                "top_logit": top_logit,
                "tau_ce": tau_ce,
                "refusal_reason": (
                    f"Top relevance logit ({top_logit:.4f}) is below calibrated refusal threshold ({tau_ce:.4f}). "
                    "Refusing to generate text without sufficient empirical evidence."
                ),
                "candidates": [],
                "nearest_documents": top_candidates
            }

    return {
        "status": "answered",
        "uncalibrated": uncalibrated_mode,
        "top_logit": top_logit,
        "tau_ce": tau_ce,
        "refusal_reason": None,
        "candidates": top_candidates,
        "nearest_documents": top_candidates
    }
