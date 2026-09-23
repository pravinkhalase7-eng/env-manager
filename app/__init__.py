from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "registry.yaml"
GENERATED_DIR = ROOT / "generated"


def load_registry() -> dict:
    data = yaml.safe_load(REGISTRY_PATH.read_text()) or {}
    data.setdefault("apps", [])
    data.setdefault("edge", {})
    data.setdefault("workspace", str(ROOT.parent))
    return data


def save_registry(data: dict) -> None:
    REGISTRY_PATH.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
