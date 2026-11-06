"""Script: Build ChromaDB vector index from license-cleared PDFs.

Saves persistent ChromaDB index to data/index.
Exits cleanly if no license-cleared PDFs exist.
"""
import os
import sys
from pathlib import Path
import yaml

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ingest import ingest_corpus
from core.config import data_path, config_file


def prune_stale_chunks(collection, current_ids):
    stale = sorted(set(collection.get(include=[])["ids"]) - set(current_ids))
    for start in range(0, len(stale), 64):
        collection.delete(ids=stale[start:start + 64])


def build_vector_index(
    config_path: str = "config.yaml",
    persist_dir: str = None,
    pdfs_dir: str = None,
    meta_path: str = None
):
    """Build or update ChromaDB vector store with chunk embeddings."""
    print("=" * 60)
    print("COMBUSTIONLENS: VECTOR INDEX BUILD PIPELINE")
    print("=" * 60)
    
    config_path = str(config_file(config_path))
    persist_dir = persist_dir or data_path("chroma_dir", "data/index", config_path)
    pdfs_dir = pdfs_dir or data_path("corpus_dir", "data/pdfs", config_path)
    meta_path = meta_path or data_path("paper_meta", "data/paper_meta.csv", config_path)
    # Ingest chunks
    chunks, skipped = ingest_corpus(pdfs_dir=pdfs_dir, meta_csv_path=meta_path, config_path=config_path)
    
    if skipped:
        print(f"\nSkipped {len(skipped)} papers due to license or metadata requirements:")
        for s in skipped:
            print(f"  - [{s['doc_id']}] {s['reason']}")
            
    if not chunks:
        if Path(persist_dir).exists():
            import chromadb
            client = chromadb.PersistentClient(path=persist_dir)
            names = [c if isinstance(c, str) else c.name for c in client.list_collections()]
            if "combustion_papers" in names:
                prune_stale_chunks(client.get_collection("combustion_papers", embedding_function=None), [])
        print("\nNo license-cleared chunks found to index.")
        print(f"Empty state verified. ChromaDB index at '{persist_dir}' is ready for human data drop.")
        print("=" * 60)
        return
        
    print(f"\nEmbedding {len(chunks)} chunks into ChromaDB at '{persist_dir}'...")
    
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        
        # Load embedding model name from config
        emb_model = "sentence-transformers/all-MiniLM-L6-v2"
        if Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                emb_model = cfg.get("model", {}).get("embedding_model", emb_model)
                
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=emb_model)
        
        os.makedirs(persist_dir, exist_ok=True)
        client = chromadb.PersistentClient(path=persist_dir)
        collection = client.get_or_create_collection(
            name="combustion_papers",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )
        
        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [{
            "doc_id": c["doc_id"],
            "title": c["title"],
            "authors": c["authors"],
            "year": str(c["year"]),
            "section": c["section"],
            "page_number": int(c["page_number"]),
            "campaign_or_series": c["campaign_or_series"],
            "research_group_label": c["research_group_label"],
            "source_type": c["source_type"],
            "peer_reviewed": str(c["peer_reviewed"]),
            "license_status": c["license_status"]
        } for c in chunks]
        
        # Batch insert
        batch_size = 64
        for i in range(0, len(ids), batch_size):
            collection.upsert(
                ids=ids[i:i + batch_size],
                documents=texts[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )
            
        prune_stale_chunks(collection, ids)
        print(f"Successfully indexed {len(ids)} chunks in ChromaDB collection 'combustion_papers'.")
        print("=" * 60)
    except Exception as e:
        print(f"Error building vector index: {e}")
        raise e


if __name__ == "__main__":
    build_vector_index()
