#!/usr/bin/env python3
# INPUT: datetime, pathlib, yaml (lazy)
# OUTPUT: VERSION constant, DEFAULT_DIRS list, _now_iso, _write_yaml, _normalize_highlights helpers
# POS: pure utility helpers shared by ps_setup.py. No filesystem state, no business logic.
"""Pure helpers extracted from ps_setup.py to keep that file under the 300-line ceiling.

Nothing in this module depends on PRESALES_HOME or any project state. Helpers
are safe to unit-test in isolation once the v0.2 pytest harness lands.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"

DEFAULT_DIRS: list[str] = [
    "opportunities",
    "cases",
    "knowledge",
    "knowledge/products",
    "knowledge/competitors",
    "templates",
]

# Paths that reset_home() refuses to touch even at depth >= 3.
# macOS resolves /tmp to /private/tmp (depth 3) so a pure depth check is insufficient.
_UNSAFE_RESET_PATHS: set[Path] = {
    Path("/"),
    Path("/tmp"),
    Path("/private/tmp"),
    Path("/var"),
    Path("/private/var"),
    Path("/Users"),
    Path("/home"),
}


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string ending in Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_yaml(path: Path, data: dict) -> None:
    """Serialize data as YAML and write to path. Requires PyYAML."""
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "presales-engine 需要 PyYAML 来写入 YAML 配置。请运行 `pip install pyyaml` 后重试。"
        ) from e
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _normalize_highlights(value) -> list:
    """Coerce highlights config field into a list. None/empty → []; scalar → [scalar]."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]
