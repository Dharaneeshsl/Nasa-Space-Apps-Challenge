"""Resolve source links from curated metadata, never from generated model text."""
import csv
from pathlib import Path
from urllib.parse import urlsplit
from core.config import data_path


def source_url_for(doc_id: str):
    path = Path(data_path("paper_meta", "data/paper_meta.csv"))
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("doc_id") != doc_id:
                    continue
                url = (row.get("source_url") or "").strip()
                parsed = urlsplit(url)
                if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
                    return url
                return None
    except (OSError, ValueError, csv.Error):
        return None
    return None
