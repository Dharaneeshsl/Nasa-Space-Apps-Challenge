import csv
from unittest.mock import patch
from core.sources import source_url_for


def test_source_links_are_resolved_only_from_curated_metadata(tmp_path):
    path = tmp_path / "meta.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["doc_id", "source_url"])
        writer.writeheader()
        writer.writerows([
            {"doc_id": "valid", "source_url": "https://ntrs.nasa.gov/"},
            {"doc_id": "unsafe", "source_url": "javascript:alert(1)"},
            {"doc_id": "credentials", "source_url": "https://user:secret@example.com/"},
            {"doc_id": "missing", "source_url": ""},
        ])
    with patch("core.sources.data_path", return_value=str(path)):
        assert source_url_for("valid") == "https://ntrs.nasa.gov/"
        for doc_id in ("unsafe", "credentials", "missing", "invented"):
            assert source_url_for(doc_id) is None


def test_missing_metadata_does_not_break_answers(tmp_path):
    with patch("core.sources.data_path", return_value=str(tmp_path / "absent.csv")):
        assert source_url_for("any") is None
