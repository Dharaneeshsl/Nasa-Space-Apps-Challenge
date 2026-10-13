"""Unit tests for core/numcheck.py normalized number checking.

NOTE: Synthetic test fixtures live exclusively inside this test module.
"""
import pytest
from core.numcheck import (
    extract_numbers,
    verify_sentence_numbers,
    filter_verified_sentences
)

SYNTHETIC_CHUNKS = [
    {
        "chunk_id": "SYNTH_C1",
        "text": "The burning rate constant K was measured as 0.65 mm^2/s at 101.3 kPa with 21% O2."
    },
    {
        "chunk_id": "SYNTH_C2",
        "text": "Extinction occurred at 14.5% O2 under quiescent conditions."
    }
]


def test_extract_numbers():
    text = "Initial droplet diameter d0 = 2.0 mm, pressure 101.3 kPa, rate 1.5e-3."
    nums = extract_numbers(text)
    assert 2.0 in nums
    assert 101.3 in nums
    assert 0.0015 in nums


def test_verify_sentence_numbers_valid():
    sentence = "The burning rate constant was 0.65 mm^2/s under 21% oxygen."
    is_valid, matched, unmatched = verify_sentence_numbers(sentence, SYNTHETIC_CHUNKS)
    assert is_valid is True
    assert 0.65 in matched
    assert 21.0 in matched
    assert len(unmatched) == 0


def test_verify_sentence_numbers_hallucinated():
    # 0.95 and 50% are hallucinated (not in synthetic chunks)
    sentence = "The burning rate constant reached 0.95 mm^2/s under 50% oxygen."
    is_valid, matched, unmatched = verify_sentence_numbers(sentence, SYNTHETIC_CHUNKS)
    assert is_valid is False
    assert 0.95 in unmatched
    assert 50.0 in unmatched


def test_filter_verified_sentences():
    sentences = [
        {"text": "Under quiescent conditions, extinction occurred at 14.5% O2.", "citations": []},
        {"text": "The flame reached a high velocity of 99.9 mm/s.", "citations": []}  # Hallucinated number 99.9
    ]
    kept, hidden = filter_verified_sentences(sentences, SYNTHETIC_CHUNKS)
    assert len(kept) == 1
    assert "14.5% O2" in kept[0]["text"]
    assert len(hidden) == 1
    assert 99.9 in hidden[0]["unmatched_numbers"]
