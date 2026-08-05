"""Company list loading. Prefers the ATS-resolved file when present."""
from pathlib import Path

import yaml

RESOLVED_PATH = Path("config/companies.resolved.yaml")
DEFAULT_PATH = Path("config/companies.yaml")


def load_companies() -> list:
    path = RESOLVED_PATH if RESOLVED_PATH.exists() else DEFAULT_PATH
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("companies", [])
