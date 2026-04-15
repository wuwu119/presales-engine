#!/usr/bin/env python3
# INPUT: os.environ, pathlib
# OUTPUT: PRESALES_HOME / CLAUDE_PLUGIN_ROOT / opportunity / knowledge path resolution
# POS: path resolution utility shared by all presales-engine scripts. Forbidden to hardcode ~/.presales/.
"""Unified path resolution for presales-engine.

Environment variables:
    PRESALES_HOME:      user data root, default ~/.presales/
    CLAUDE_PLUGIN_ROOT: plugin root (injected by Claude Code at runtime)
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def presales_home() -> Path:
    """Return user data root. Respects PRESALES_HOME, defaults to ~/.presales/."""
    home = os.environ.get("PRESALES_HOME")
    if home:
        return Path(home).expanduser().resolve()
    return (Path.home() / ".presales").resolve()


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


def _as_str_dict(paths: dict[str, Path]) -> dict[str, str]:
    return {k: str(v) for k, v in paths.items()}


if __name__ == "__main__":
    # CLI debug entry: prints resolved paths as JSON.
    print(json.dumps({
        "presales_home": str(presales_home()),
        "plugin_root": str(plugin_root()),
        "seed_templates": str(seed_templates_dir()),
        "knowledge": _as_str_dict(knowledge_paths()),
    }, indent=2, ensure_ascii=False))
