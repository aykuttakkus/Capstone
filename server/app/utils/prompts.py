from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Template
from typing import Any

import yaml


PROMPTS_PATH = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"


@lru_cache(maxsize=1)
def load_prompts() -> dict[str, Any]:
    if not PROMPTS_PATH.exists():
        return {}
    with PROMPTS_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def get_prompt(key: str, default: str = "") -> str:
    current: Any = load_prompts()
    for part in key.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return str(current)


def render_prompt(key: str, default: str = "", **values: str) -> str:
    template = get_prompt(key, default=default)
    return Template(template).safe_substitute(**values)
