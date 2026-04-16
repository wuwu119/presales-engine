#!/usr/bin/env python3
# INPUT: ps_paths, yaml (lazy), json, argparse, datetime
# OUTPUT: diagnose subcommand — scan knowledge base completeness across 9 dimensions, output JSON
# POS: scripts layer for ps:knowledge-doctor; file counting + YAML reading only, no LLM calls
"""Diagnose knowledge base completeness across 9 dimensions.

Each dimension has a minimum baseline and a sufficient threshold.
Output is a JSON object consumed by the SKILL.md layer to render
a human-readable health report with actionable gap guidance.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ps_paths  # noqa: E402

EXIT_HOME_NOT_SET = 2
EXIT_DIR_MISSING = 3
EXIT_YAML_CORRUPT = 4


def _die(code: int, msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def _require_yaml():
    try:
        import yaml  # type: ignore

        return yaml
    except ImportError:
        _die(
            EXIT_YAML_CORRUPT,
            "presales-engine 需要 PyYAML，请运行 `pip install pyyaml` 后重试。",
        )


def _load_yaml(path: Path) -> dict:
    yaml = _require_yaml()
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        _die(EXIT_YAML_CORRUPT, f"{path.name} YAML 解析失败: {e}")
    if data is None:
        return {}
    if not isinstance(data, dict):
        _die(EXIT_YAML_CORRUPT, f"{path.name} 根必须是 mapping，实际为 {type(data).__name__}")
    return data


def _count_files(directory: Path, *, exclude_readme: bool = True) -> int:
    """Count non-hidden files in a directory. Optionally exclude README.md."""
    if not directory.exists():
        return 0
    count = 0
    for p in directory.iterdir():
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        if exclude_readme and p.name == "README.md":
            continue
        count += 1
    return count


def _count_yaml_files(directory: Path, *, exclude_example: bool = False) -> int:
    """Count .yaml/.yml files in a directory, optionally excluding example files."""
    if not directory.exists():
        return 0
    count = 0
    for p in directory.iterdir():
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        if p.name == "README.md":
            continue
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if exclude_example and "example" in p.stem.lower():
            continue
        count += 1
    return count


def _diagnose_company_certs(profile: dict, today: str) -> dict:
    """Dimension: company qualifications from company-profile.yaml."""
    quals = profile.get("qualifications") or []
    if not isinstance(quals, list):
        quals = []

    total = len(quals)
    valid = 0
    expired = 0
    for q in quals:
        if not isinstance(q, dict):
            continue
        vu = str(q.get("valid_until") or "")
        if vu and vu < today:
            expired += 1
        else:
            valid += 1

    return {
        "dimension": "company_certs",
        "label": "公司资质",
        "total": total,
        "valid": valid,
        "expired": expired,
        "min_baseline": 5,
        "sufficient": 15,
        "value": valid,
        "data_location": "company-profile.yaml.qualifications[]",
    }


def _diagnose_team_roster(paths: dict[str, Path]) -> dict:
    """Dimension: team roster.yaml existence + cert_summary."""
    team_dir = paths["team"]
    roster_path = team_dir / "roster.yaml"

    roster_exists = roster_path.exists()
    cert_summary_populated = False
    total_certs = 0
    total_people = 0

    if roster_exists:
        yaml = _require_yaml()
        try:
            data = yaml.safe_load(roster_path.read_text(encoding="utf-8"))
        except Exception:
            data = None

        if isinstance(data, dict):
            summary = data.get("cert_summary_by_type") or {}
            cert_summary_populated = len(summary) > 0
            meta = data.get("meta") or {}
            total_certs = meta.get("total_valid_certs", 0)
            total_people = meta.get("total_people", 0)

    return {
        "dimension": "team_roster",
        "label": "团队汇总",
        "roster_exists": roster_exists,
        "cert_summary_populated": cert_summary_populated,
        "total_certs": total_certs,
        "total_people": total_people,
        "min_baseline_desc": "roster.yaml 存在 + cert_summary 非空",
        "sufficient": 100,
        "value": total_certs if (roster_exists and cert_summary_populated) else 0,
        "data_location": "团队/roster.yaml",
    }


def _diagnose_team_registry(paths: dict[str, Path]) -> dict:
    """Dimension: team cert-registry shard count."""
    team_dir = paths["team"]
    shard_count = 0
    if team_dir.exists():
        for p in team_dir.iterdir():
            if p.is_file() and p.name.startswith("cert-registry-") and p.suffix in {".yaml", ".yml"}:
                shard_count += 1

    return {
        "dimension": "team_registry",
        "label": "团队明细",
        "shard_count": shard_count,
        "min_baseline": 1,
        "sufficient": 3,
        "value": shard_count,
        "data_location": "团队/cert-registry-*.yaml",
    }


def _diagnose_products(paths: dict[str, Path]) -> dict:
    """Dimension: product YAML files."""
    count = _count_yaml_files(paths["products"], exclude_example=True)
    return {
        "dimension": "products",
        "label": "产品档案",
        "count": count,
        "min_baseline": 1,
        "sufficient": 3,
        "value": count,
        "data_location": "产品档案/*.yaml（排除 example）",
    }


def _diagnose_competitors(paths: dict[str, Path]) -> dict:
    """Dimension: competitor YAML files."""
    count = _count_yaml_files(paths["competitors"])
    return {
        "dimension": "competitors",
        "label": "竞品对比",
        "count": count,
        "min_baseline": 3,
        "sufficient": 10,
        "value": count,
        "data_location": "竞品/*.yaml（排除 README）",
    }


def _diagnose_about(paths: dict[str, Path]) -> dict:
    """Dimension: company introduction files."""
    count = _count_files(paths["about"])
    return {
        "dimension": "about",
        "label": "公司介绍",
        "count": count,
        "min_baseline": 1,
        "sufficient": 3,
        "value": count,
        "data_location": "公司介绍/*（排除 README）",
    }


def _diagnose_case_studies(paths: dict[str, Path]) -> dict:
    """Dimension: case study files."""
    count = _count_files(paths["case_studies"])
    return {
        "dimension": "case_studies",
        "label": "客户案例",
        "count": count,
        "min_baseline": 3,
        "sufficient": 10,
        "value": count,
        "data_location": "客户案例/*（排除 README）",
    }


def _diagnose_case_references(profile: dict) -> dict:
    """Dimension: case_references in company-profile.yaml."""
    refs = profile.get("case_references") or []
    if not isinstance(refs, list):
        refs = []
    count = len(refs)
    return {
        "dimension": "case_references",
        "label": "案例引用",
        "count": count,
        "min_baseline": 1,
        "sufficient": 5,
        "value": count,
        "data_location": "company-profile.yaml.case_references[]",
    }


def _diagnose_highlights(profile: dict) -> dict:
    """Dimension: highlights in company-profile.yaml."""
    hl = profile.get("highlights") or []
    if not isinstance(hl, list):
        hl = []
    count = len(hl)
    return {
        "dimension": "highlights",
        "label": "差异化亮点",
        "count": count,
        "min_baseline": 1,
        "sufficient": 3,
        "value": count,
        "data_location": "company-profile.yaml.highlights[]",
    }


def _classify(dim: dict) -> str:
    """Classify a dimension as 'sufficient', 'insufficient', or 'empty'."""
    value = dim["value"]
    if value <= 0:
        return "empty"

    # team_roster has a special baseline check
    if dim["dimension"] == "team_roster":
        if not dim.get("roster_exists") or not dim.get("cert_summary_populated"):
            return "empty"

    sufficient = dim.get("sufficient", 0)
    min_baseline = dim.get("min_baseline", 0)

    if value >= sufficient:
        return "sufficient"
    if min_baseline > 0 and value >= min_baseline:
        return "insufficient"

    # team_roster: baseline = roster exists + summary non-empty, already checked above
    if dim["dimension"] == "team_roster":
        return "insufficient"

    return "empty"


def cmd_diagnose(args: argparse.Namespace) -> int:
    paths = ps_paths.knowledge_paths()
    kb_dir = paths["knowledge"]

    if not kb_dir.exists():
        _die(
            EXIT_DIR_MISSING,
            f"知识库目录不存在: {kb_dir}\n请先运行 /ps:setup 初始化知识库。",
        )

    profile = _load_yaml(paths["company_profile"])
    today = date.today().isoformat()

    dimensions = [
        _diagnose_company_certs(profile, today),
        _diagnose_team_roster(paths),
        _diagnose_team_registry(paths),
        _diagnose_products(paths),
        _diagnose_competitors(paths),
        _diagnose_about(paths),
        _diagnose_case_studies(paths),
        _diagnose_case_references(profile),
        _diagnose_highlights(profile),
    ]

    for dim in dimensions:
        dim["status"] = _classify(dim)

    sufficient_count = sum(1 for d in dimensions if d["status"] == "sufficient")
    insufficient_count = sum(1 for d in dimensions if d["status"] == "insufficient")
    empty_count = sum(1 for d in dimensions if d["status"] == "empty")
    total_dims = len(dimensions)
    passing = sufficient_count + insufficient_count  # at least baseline
    completeness_pct = round(passing / total_dims * 100) if total_dims else 0

    result = {
        "completeness_pct": completeness_pct,
        "total_dimensions": total_dims,
        "passing_dimensions": passing,
        "sufficient_count": sufficient_count,
        "insufficient_count": insufficient_count,
        "empty_count": empty_count,
        "dimensions": dimensions,
        "diagnosed_at": today,
        "knowledge_base": str(kb_dir),
    }

    if args.mode == "mini":
        # Mini mode: only dimensions that are not sufficient
        result["dimensions"] = [d for d in dimensions if d["status"] != "sufficient"]

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ps_knowledge_doctor",
        description="ps:knowledge-doctor scripts layer — 知识库完整度诊断",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_diag = sub.add_parser("diagnose", help="扫描知识库完整度，输出 JSON 诊断")
    p_diag.add_argument(
        "--mode",
        choices=["full", "mini"],
        default="full",
        help="full = 完整报告，mini = 只输出非充足维度（入库后用）",
    )
    p_diag.set_defaults(func=cmd_diagnose)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
