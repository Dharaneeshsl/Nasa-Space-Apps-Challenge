"""CombustionLens Core: Ingestion Pipeline.

PyMuPDF section-aware chunking preserving:
- doc_id
- title
- authors
- year
- section
- exact page number (1-indexed)

HARD RULE: Only index papers where paper_meta.csv has license_status = 'public_domain_confirmed'.
All others are skipped and logged with explicit reason.
Empty data/pdfs/ exits cleanly with a clear message.
"""
import os
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


def load_paper_meta_lookup(meta_csv_path: str = "data/paper_meta.csv") -> Dict[str, Dict[str, Any]]:
    """Load metadata mapping doc_id -> metadata row from paper_meta.csv."""
    lookup = {}
    p = Path(meta_csv_path)
    if not p.exists():
        return lookup
        
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get("doc_id", "").strip()
            if doc_id:
                lookup[doc_id] = row
    return lookup


def simple_tokenize_words(text: str) -> List[str]:
    """Tokenize text by whitespace and punctuation for approximate token counting."""
    return text.split()


def chunk_text_by_tokens(
    text: str, 
    page_number: int, 
    doc_id: str,
    meta: Dict[str, Any],
    min_tokens: int = 500, 
    max_tokens: int = 800, 
    overlap: int = 100
) -> List[Dict[str, Any]]:
    """Chunk page text into 500-800 token slices with 100 token overlap.
    
    Preserves exact page number, section, and paper metadata.
    """
    words = simple_tokenize_words(text)
    if not words:
        return []
        
    chunks = []
    # If text is small, produce single chunk
    target_chunk_size = (min_tokens + max_tokens) // 2
    step = max(1, target_chunk_size - overlap)
    
    # Simple section detector (e.g. lines that look like headers)
    section_name = f"Page {page_number}"
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line) < 80 and not first_line.endswith("."):
            section_name = first_line
            
    for i in range(0, len(words), step):
        chunk_words = words[i:i + target_chunk_size]
        if not chunk_words:
            continue
        chunk_text = " ".join(chunk_words)
        
        chunk_id = f"{doc_id}_p{page_number}_c{len(chunks) + 1}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "doc_id": doc_id,
            "title": meta.get("title", "Unknown Title"),
            "authors": meta.get("authors", "Unknown Authors"),
            "year": meta.get("year", "Unknown Year"),
            "campaign_or_series": meta.get("campaign_or_series", "unknown"),
            "research_group_label": meta.get("research_group_label", "unknown"),
            "source_type": meta.get("source_type", "unknown"),
            "peer_reviewed": meta.get("peer_reviewed", "unknown"),
            "license_status": meta.get("license_status", "unknown"),
            "section": section_name,
            "page_number": page_number,
            "token_count": len(chunk_words)
        })
        if i + target_chunk_size >= len(words):
            break
            
    return chunks


def load_chunking_config(config_path: str = "config.yaml") -> Tuple[int, int, int]:
    """Load token chunking parameters from config.yaml with model-safe defaults (150-250 tokens)."""
    default_min = 150
    default_max = 250
    default_overlap = 40
    p = Path(config_path)
    if p.exists():
        try:
            import yaml
            with open(p, "r", encoding="utf-8") as f:
                c = yaml.safe_load(f) or {}
                chk = c.get("chunking", {})
                return (
                    int(chk.get("chunk_tokens_min", default_min)),
                    int(chk.get("chunk_tokens_max", default_max)),
                    int(chk.get("chunk_overlap", default_overlap))
                )
        except Exception:
            pass
    return default_min, default_max, default_overlap


def extract_chunks_from_pdf(
    pdf_path: Path, 
    meta: Dict[str, Any],
    min_tokens: int = 150,
    max_tokens: int = 250,
    overlap: int = 40
) -> List[Dict[str, Any]]:
    """Extract text from PDF page by page and chunk with metadata preservation."""
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required for PDF ingestion.")
        
    doc = fitz.open(str(pdf_path))
    doc_id = pdf_path.stem
    all_chunks = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1  # 1-indexed page number
        page_text = page.get_text("text")
        if not page_text or not page_text.strip():
            continue
            
        page_chunks = chunk_text_by_tokens(
            text=page_text,
            page_number=page_num,
            doc_id=doc_id,
            meta=meta,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            overlap=overlap
        )
        all_chunks.extend(page_chunks)
        
    doc.close()
    return all_chunks


def ingest_corpus(
    pdfs_dir: str = "data/pdfs", 
    meta_csv_path: str = "data/paper_meta.csv",
    config_path: str = "config.yaml",
    min_tokens: Optional[int] = None,
    max_tokens: Optional[int] = None,
    overlap: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Ingest license-cleared PDFs, skipping unverified or restricted ones.
    
    Returns:
    - (indexed_chunks, skipped_papers_log)
    """
    # Load chunking parameters from config if not explicitly passed
    cfg_min, cfg_max, cfg_overlap = load_chunking_config(config_path)
    eff_min = min_tokens if min_tokens is not None else cfg_min
    eff_max = max_tokens if max_tokens is not None else cfg_max
    eff_overlap = overlap if overlap is not None else cfg_overlap

    p_dir = Path(pdfs_dir)
    meta_lookup = load_paper_meta_lookup(meta_csv_path)
    
    if not p_dir.exists():
        print(f"PDFs directory '{pdfs_dir}' does not exist.")
        return [], []
        
    pdf_files = list(p_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"Empty PDFs directory '{pdfs_dir}'. No papers to index.")
        return [], []
        
    indexed_chunks = []
    skipped_log = []
    
    for pdf_path in pdf_files:
        doc_id = pdf_path.stem
        meta = meta_lookup.get(doc_id)
        
        if not meta:
            reason = f"No metadata row found in '{meta_csv_path}'"
            print(f"Skipping '{pdf_path.name}': {reason}")
            skipped_log.append({"doc_id": doc_id, "file": pdf_path.name, "reason": reason})
            continue
            
        lic_status = str(meta.get("license_status", "")).strip().lower()
        if lic_status != "public_domain_confirmed":
            reason = f"License status is '{lic_status}' (must be 'public_domain_confirmed')"
            print(f"Skipping '{pdf_path.name}': {reason}")
            skipped_log.append({"doc_id": doc_id, "file": pdf_path.name, "reason": reason})
            continue
            
        print(f"Ingesting license-cleared paper: {pdf_path.name} ({doc_id})")
        chunks = extract_chunks_from_pdf(pdf_path, meta, eff_min, eff_max, eff_overlap)
        indexed_chunks.extend(chunks)
        print(f"  -> Extracted {len(chunks)} chunks across pages.")
        
    return indexed_chunks, skipped_log
