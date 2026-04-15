#!/usr/bin/env python3
# INPUT: os.environ, pathlib
# OUTPUT: PRESALES_HOME / CLAUDE_PLUGIN_ROOT / opportunity / knowledge path resolution
# POS: path resolution utility shared by all presales-engine scripts. Forbidden to hardcode any presales home path.
"""Unified path resolution for presales-engine.

Resolution order for the user data root:
    1. PRESALES_HOME env var (highest priority — for CI / one-shot overrides)
    2. Pointer file at ~/.config/presales-engine/home (set during ps:setup --init)
    3. Default ~/presales/ (visible, not hidden, intended for daily user editing)

Environment variables:
    PRESALES_HOME:      user data root override
    CLAUDE_PLUGIN_ROOT: plugin root (injected by Claude Code at runtime)
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _config_pointer_path() -> Path:
    """Path of the persistent home-pointer file. Set by ps:setup --init."""
    return Path.home() / ".config" / "presales-engine" / "home"


def _read_pointer() -> Path | None:
    """Read the pointer file. Returns None if missing or empty."""
    pointer = _config_pointer_path()
    if not pointer.exists():
        return None
    content = pointer.read_text(encoding="utf-8").strip()
    if not content:
        return None
    return Path(content).expanduser().resolve()


def write_pointer(path: Path) -> None:
    """Persist the user's chosen presales home to the pointer file."""
    pointer = _config_pointer_path()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(Path(path).expanduser().resolve()), encoding="utf-8")


def presales_home() -> Path:
    """Return the user data root via the documented 3-layer resolution."""
    env = os.environ.get("PRESALES_HOME")
    if env:
        return Path(env).expanduser().resolve()
    pointer = _read_pointer()
    if pointer is not None:
        return pointer
    return (Path.home() / "presales").resolve()


def presales_home_source() -> str:
    """Return which resolution layer produced presales_home(): env / pointer / default."""
    if os.environ.get("PRESALES_HOME"):
        return "env"
    if _read_pointer() is not None:
        return "pointer"
    return "default"


def plugin_root() -> Path:
    """Return plugin root directory (read-only, used to read seed templates).

    Prefers CLAUDE_PLUGIN_ROOT (set by Claude Code). Falls back to walking
    up from this script's location (scripts/ps_paths.py -> plugin root).
    """
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def opportunity_root(slug: str) -> Path:
    """Return root directory for a given opportunity slug."""
    return presales_home() / "opportunities" / slug


def opportunity_paths(slug: str) -> dict[str, Path]:
    """Return all key paths for a given opportunity slug."""
    root = opportunity_root(slug)
    return {
        "root": root,
        "meta": root / "meta.yaml",
        "rfp_dir": root / "rfp",
        "rfp_original": root / "rfp" / "original",
        "rfp_extracted": root / "rfp" / "extracted.md",
        "analysis_dir": root / "analysis",
        "rfp_yaml": root / "analysis" / "rfp.yaml",
        "analysis_md": root / "analysis" / "analysis.md",
        "draft_dir": root / "draft",
        "outline": root / "draft" / "outline.md",
        "chapters": root / "draft" / "chapters",
        "coverage_report": root / "draft" / "coverage-report.md",
        "review": root / "review.md",
    }


def knowledge_paths() -> dict[str, Path]:
    """Return knowledge base paths under PRESALES_HOME."""
    home = presales_home()
    return {
        "home": home,
        "config": home / "config.yaml",
        "version": home / ".version",
        "knowledge": home / "knowledge",
        "company_profile": home / "knowledge" / "company-profile.yaml",
        "products": home / "knowledge" / "products",
        "competitors": home / "knowledge" / "competitors",
        "templates": home / "templates",
        "cases": home / "cases",
        "opportunities": home / "opportunities",
    }


def seed_templates_dir() -> Path:
    """Return the plugin's seed templates directory (read-only)."""
    return plugin_root() / "templates"


if __name__ == "__main__":
    # CLI debug entry: prints resolved paths as JSON.
    print(json.dumps({
        "presales_home": str(presales_home()),
        "presales_home_source": presales_home_source(),
        "pointer_file": str(_config_pointer_path()),
        "plugin_root": str(plugin_root()),
        "seed_templates": str(seed_templates_dir()),
        "knowledge": {k: str(v) for k, v in knowledge_paths().items()},
    }, indent=2, ensure_ascii=False))
