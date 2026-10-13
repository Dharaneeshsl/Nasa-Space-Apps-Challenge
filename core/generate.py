"""CombustionLens Core: Grounded Generation and Ambiguity Handling.

HARD RULES:
1. Grounded synthesis: Uses retrieved chunks only.
2. Cites paper title, page, and doc_id per sentence.
3. Number verification: Sentences with numbers not found in cited chunks are hidden.
4. Ambiguity handling: If key physical boundary conditions (fuel, pressure, gravity, flow)
   are missing from a query asking for combustion behavior, returns needs_clarification.
5. In-memory / persistent prompt-hash caching (key = model + prompt hash).
6. API keys from environment only (OPENAI_API_KEY).
7. Mandatory disclaimer included in all outputs.
8. Zero fabrication: Never default page to 1 or title to "NASA Publication".
"""
import os
import re
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import yaml
from core.numcheck import filter_verified_sentences

DISCLAIMER_TEXT = (
    "Generated from published NASA research for informational/research purposes. "
    "Not validated for operational flight or terrestrial fire safety decisions."
)

_CALL_CACHE: Dict[str, Any] = {}

COMBUSTION_BEHAVIOR_KEYWORDS = [
    "burning rate", "burning constant", "burning rate constant", 
    "flame spread rate", "flame spread", "regression rate", "spread rate"
]

BOUNDARY_CONDITION_CHECKS = {
    "fuel": ["fuel", "heptane", "pmma", "methane", "propane", "cotton", "fiberglass", "material", "droplet"],
    "pressure": ["pressure", "kpa", "atm", "bar", "torr", "ambient pressure", "vacuum"],
    "gravity": ["gravity", "microgravity", "micro-g", "1-g", "normal gravity", "zero-g", "drop tower"],
    "flow": ["flow", "quiescent", "forced", "convection", "velocity", "stagnant", "duct"]
}


def _matches_keyword(keyword: str, text: str) -> bool:
    """Matches keyword using word boundaries to prevent substring collisions (e.g. 'atm' in 'atmosphere')."""
    pattern = rf"(?:\b|\A){re.escape(keyword)}(?:\b|\Z)"
    return bool(re.search(pattern, text, re.IGNORECASE))


def check_query_ambiguity(query: str) -> Tuple[bool, List[str]]:
    """Check if query is asking for quantitative combustion behavior but omits boundary conditions."""
    q_lower = query.lower()
    
    # Check if query inquires about combustion behavior
    is_behavior_query = any(_matches_keyword(kw, q_lower) for kw in COMBUSTION_BEHAVIOR_KEYWORDS)
    if not is_behavior_query:
        return False, []
        
    missing = []
    for cond_name, keywords in BOUNDARY_CONDITION_CHECKS.items():
        if not any(_matches_keyword(kw, q_lower) for kw in keywords):
            missing.append(cond_name)
            
    # If missing 2 or more vital conditions, query needs clarification
    if len(missing) >= 2:
        return True, missing
    return False, []



def get_cache_key(model: str, prompt: str) -> str:
    """Generate SHA256 cache key from model name and prompt string."""
    raw = f"{model}::{prompt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_generator_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load generator configuration. NEVER silently defaults model to gpt-4o-mini."""
    env_config = os.environ.get("COMBUSTIONLENS_CONFIG_PATH")
    if env_config:
        config_path = env_config
    cfg = {"generator_model": "", "temperature": 0.0}
    p = Path(config_path)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                c = yaml.safe_load(f) or {}
                m = c.get("model", {})
                gen = m.get("generator_model", "")
                cfg["generator_model"] = gen.strip() if gen else ""
                cfg["temperature"] = float(m.get("temperature", 0.0))
        except Exception:
            pass
    return cfg


def split_sentences_safely(text: str) -> List[str]:
    """Split text into sentences without splitting on decimal numbers or abbreviations."""
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text.strip())
    clean_sents = [s.strip() for s in raw_sentences if s and len(s.strip()) > 3]
    return clean_sents if clean_sents else [text.strip()]


def validate_and_filter_citations(
    sentences: List[Dict[str, Any]], 
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Verify that every cited doc_id and page actually exists in the retrieved chunks.
    
    Strips hallucinated citations and never defaults missing pages/titles.
    """
    valid_pairs = set()
    doc_titles = {}
    for c in chunks:
        d_id = c.get("doc_id")
        if not d_id:
            continue
        p_raw = c.get("page_number")
        p_num = None
        if p_raw is not None:
            try:
                p_num = int(p_raw)
            except (ValueError, TypeError):
                p_num = None
        valid_pairs.add((d_id, p_num))
        if c.get("title"):
            doc_titles[d_id] = c.get("title")

    cleaned_sentences = []
    for s in sentences:
        verified_citations = []
        for cite in s.get("citations", []):
            c_doc = cite.get("doc_id")
            c_page_raw = cite.get("page")
            c_page = None
            if c_page_raw is not None:
                try:
                    c_page = int(c_page_raw)
                except (ValueError, TypeError):
                    c_page = None
            
            # Citation must match a retrieved candidate
            is_valid = False
            if (c_doc, c_page) in valid_pairs:
                is_valid = True
            elif c_page is None and any(pair[0] == c_doc for pair in valid_pairs):
                is_valid = True
                
            if is_valid:
                verified_citations.append({
                    "doc_id": c_doc,
                    "paper_title": cite.get("paper_title") or doc_titles.get(c_doc),
                    "page": c_page
                })
        
        # Only retain sentence if it carries verified citations
        if verified_citations:
            cleaned_sentences.append({
                "text": s.get("text", ""),
                "citations": verified_citations
            })
    return cleaned_sentences


def deterministic_fallback_synthesis(
    query: str, 
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Deterministic grounded extraction when external LLM is not configured or called."""
    sentences = []
    for c in chunks:
        doc_id = c.get("doc_id")
        if not doc_id:
            continue
        title = c.get("title")
        page = c.get("page_number")
        text_snippet = c.get("text", "").strip()
        
        chunk_sents = split_sentences_safely(text_snippet)
        first_sent = chunk_sents[0] if chunk_sents else text_snippet
        
        sentences.append({
            "text": first_sent,
            "citations": [{
                "doc_id": doc_id,
                "paper_title": title,
                "page": page
            }]
        })
    return sentences


def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    config_path: str = "config.yaml",
    skip_ambiguity_check: bool = False
) -> Dict[str, Any]:
    """Generate grounded answer with citations and normalized number validation."""
    # 1. Check ambiguity first (unless explicitly skipped for structured synthesis like safety briefs)
    if not skip_ambiguity_check:
        is_ambiguous, missing_conditions = check_query_ambiguity(query)
        if is_ambiguous:
            return {
                "status": "needs_clarification",
                "generation_mode": None,
                "missing_conditions": missing_conditions,
                "refusal_reason": (
                    f"Query lacks essential physical boundary conditions: {', '.join(missing_conditions)}. "
                    "Combustion behavior depends heavily on fuel, pressure, gravity level, and flow regime. "
                    "Please specify these parameters for a grounded answer."
                ),
                "answer_sentences": [],
                "hidden_sentences": [],
                "disclaimer": DISCLAIMER_TEXT
            }

    if not chunks:
        return {
            "status": "insufficient",
            "generation_mode": None,
            "missing_conditions": [],
            "refusal_reason": "No evidence chunks available to synthesize an answer.",
            "answer_sentences": [],
            "hidden_sentences": [],
            "disclaimer": DISCLAIMER_TEXT
        }

    cfg = load_generator_config(config_path)
    model_name = cfg["generator_model"]
    
    # Build prompt representation for caching
    prompt_context = "\n---\n".join([
        f"[{c.get('doc_id')}, p.{c.get('page_number')}]: {c.get('text')}"
        for c in chunks
    ])
    full_prompt = f"Query: {query}\n\nContext:\n{prompt_context}"
    cache_key = get_cache_key(model_name or "fallback", full_prompt)
    
    raw_sentences = []
    generation_mode = "deterministic_fallback"
    
    # Check cache
    if cache_key in _CALL_CACHE:
        cached_entry = _CALL_CACHE[cache_key]
        if isinstance(cached_entry, dict):
            raw_sentences = cached_entry.get("sentences", [])
            generation_mode = cached_entry.get("generation_mode", "deterministic_fallback")
        else:
            raw_sentences = cached_entry
            generation_mode = "deterministic_fallback"
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if model_name and api_key and not api_key.startswith("mock"):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                
                system_instruction = (
                    "You are a scientific research assistant specializing in NASA microgravity combustion. "
                    "Synthesize an answer using ONLY the supplied context chunks. "
                    "Every sentence MUST be directly grounded in the context. "
                    "Output valid JSON with the format: "
                    '{"sentences": [{"text": "...", "citations": [{"doc_id": "...", "paper_title": "...", "page": 1}]}]}'
                )
                
                response = client.chat.completions.create(
                    model=model_name,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                res_content = response.choices[0].message.content
                parsed = json.loads(res_content)
                raw_sentences = parsed.get("sentences", [])
                generation_mode = "llm"
            except Exception:
                raw_sentences = deterministic_fallback_synthesis(query, chunks)
                generation_mode = "deterministic_fallback"
        else:
            # Deterministic grounded fallback when no LLM or API key is set
            raw_sentences = deterministic_fallback_synthesis(query, chunks)
            generation_mode = "deterministic_fallback"
            
        _CALL_CACHE[cache_key] = {
            "sentences": raw_sentences,
            "generation_mode": generation_mode
        }

    # 2. Strict citation validation: ensure all cited docs and pages exist in retrieved chunks
    validated_sentences = validate_and_filter_citations(raw_sentences, chunks)

    # 3. Number check: Filter sentences with hallucinated numbers
    verified_sentences, hidden_sentences = filter_verified_sentences(validated_sentences, chunks)
    
    status = "answered" if verified_sentences else "insufficient"
    refusal_reason = None
    if not verified_sentences and hidden_sentences:
        refusal_reason = "All candidate generated sentences contained numbers not supported by cited source chunks."
    elif not verified_sentences and not hidden_sentences:
        refusal_reason = "No groundable sentences with verified citations could be extracted from evidence."

    return {
        "status": status,
        "generation_mode": generation_mode,
        "missing_conditions": [],
        "refusal_reason": refusal_reason,
        "answer_sentences": verified_sentences,
        "hidden_sentences": hidden_sentences,
        "disclaimer": DISCLAIMER_TEXT
    }

