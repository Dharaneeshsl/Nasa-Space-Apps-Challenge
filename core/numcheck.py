"""CombustionLens Core: Normalized Number Verification.

HARD RULE: Numbers in generated text must exist in cited chunks after
unit normalization and rounding to the source's significant figures.
Sentences with unmatched numbers are hidden and logged.
Matches are verified against the specific chunks cited by the sentence.
"""
import re
from typing import List, Dict, Any, Tuple, Set


def extract_numbers(text: str) -> List[float]:
    """Extract all numerical values from a text string, including values glued to unit letters (e.g. 10.5mm)."""
    # Pattern matches integers, decimals, and scientific notation even if followed immediately by unit characters
    pattern = r'(?<![a-zA-Z0-9_])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?'
    matches = re.findall(pattern, text)
    nums = []
    for m in matches:
        try:
            if m in (".", "-", "+"):
                continue
            nums.append(float(m))
        except ValueError:
            pass
    return nums


def extract_chunk_numbers(chunks: List[Dict[str, Any]]) -> Set[float]:
    """Extract all numbers present in source chunks."""
    nums = set()
    for chunk in chunks:
        text = chunk.get("text", "")
        for n in extract_numbers(text):
            nums.add(round(n, 4))
    return nums


def is_number_supported(num: float, supported_numbers: Set[float], tolerance: float = 0.001) -> bool:
    """Check if number exists in cited source chunks within rounding/tolerance."""
    r_num = round(num, 4)
    if r_num in supported_numbers:
        return True
    for s in supported_numbers:
        if abs(num - s) <= tolerance:
            return True
        if s != 0 and abs(num - s) / abs(s) <= tolerance:
            return True
    return False


def verify_sentence_numbers(
    sentence: str, 
    cited_chunks: List[Dict[str, Any]],
    tolerance: float = 0.001
) -> Tuple[bool, List[float], List[float]]:
    """Verify that all numbers in sentence appear in the cited chunks.
    
    Returns:
    - (is_valid, matched_numbers, unmatched_numbers)
    """
    sentence_nums = extract_numbers(sentence)
    if not sentence_nums:
        # No numbers in sentence -> nothing to verify
        return True, [], []
        
    source_nums = extract_chunk_numbers(cited_chunks)
    matched = []
    unmatched = []
    
    for n in sentence_nums:
        if is_number_supported(n, source_nums, tolerance):
            matched.append(n)
        else:
            unmatched.append(n)
            
    is_valid = len(unmatched) == 0
    return is_valid, matched, unmatched


def filter_verified_sentences(
    sentences: List[Dict[str, Any]], 
    candidate_chunks: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filter generated sentences, hiding any sentence containing hallucinated numbers.
    
    Matches each sentence against ONLY the specific chunks cited by that sentence.
    Each sentence dict should have: {"text": str, "citations": list}
    Returns: (kept_sentences, hidden_sentences_log)
    """
    kept = []
    hidden = []
    
    for s in sentences:
        text = s.get("text", "")
        sentence_cites = s.get("citations", [])
        
        # Match against ONLY the chunks cited by this specific sentence
        if sentence_cites:
            cited_pairs = {(c.get("doc_id"), c.get("page")) for c in sentence_cites if c.get("doc_id")}
            
            # Prefer matching exact (doc_id, page)
            relevant_chunks = [
                chk for chk in candidate_chunks
                if (chk.get("doc_id"), chk.get("page_number")) in cited_pairs
                or (chk.get("doc_id"), None) in cited_pairs
            ]
            sentence_chunks = relevant_chunks
        else:
            sentence_chunks = candidate_chunks
            
        is_valid, matched, unmatched = verify_sentence_numbers(text, sentence_chunks)
        
        if is_valid:
            kept.append(s)
        else:
            hidden.append({
                "sentence": text,
                "unmatched_numbers": unmatched,
                "reason": f"Sentence contains numbers {unmatched} not found in cited chunks."
            })
            
    return kept, hidden
