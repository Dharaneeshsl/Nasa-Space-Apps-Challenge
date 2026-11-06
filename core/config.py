"""Shared configuration paths, relative to the selected configuration file."""
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


def config_file(path="config.yaml"):
    selected = os.environ.get("COMBUSTIONLENS_CONFIG_PATH", str(path))
    return (ROOT / selected).resolve()


def data_path(key, default, config_path="config.yaml"):
    config = config_file(config_path)
    settings = yaml.safe_load(config.read_text(encoding="utf-8")) or {} if config.exists() else {}
    value = settings.get("paths", {}).get(key, default)
    if key == "chroma_dir":
        value = os.environ.get("COMBUSTIONLENS_CHROMA_DIR") or value
    return str((config.parent / value).resolve())
