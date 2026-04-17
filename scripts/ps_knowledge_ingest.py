#!/usr/bin/env python3
# INPUT: ps_paths, yaml (lazy), json, argparse
# OUTPUT: scan/apply subcommands for ps:knowledge-ingest skill
# POS: scripts layer for knowledge-ingest; file IO + YAML merge only, no LLM calls
"""scan: diff knowledge base against registered entries, list unregistered files.
apply: write approved payload entries into knowledge base.

v0.2: --type certs (qualifications in company-profile.yaml)
v0.3: --type products (product factsheets in 知识库/产品档案/{slug}/)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ps_paths  # noqa: E402

SCAN_LIMIT = 20
CERT_EXTENSIONS = {".pdf", ".png", ".jpeg", ".jpg", ".tiff", ".tif"}
PRODUCT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".md"}
QUAL_ID_PATTERN = re.compile(r"^QUAL-(\d+)$")
SUPPORTED_TYPES = {"certs", "products"}

EXIT_HOME_NOT_SET = 2
EXIT_DIR_MISSING = 3
EXIT_YAML_CORRUPT = 4
EXIT_PAYLOAD_INVALID = 5


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


def _dump_yaml_atomic(path: Path, data: dict) -> None:
    yaml = _require_yaml()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _registered_basenames(profile: dict) -> set[str]:
    """Lowercased basenames already referenced by qualifications[].evidence_file."""
    quals = profile.get("qualifications") or []
    registered: set[str] = set()
    if not isinstance(quals, list):
        return registered
    for q in quals:
        if not isinstance(q, dict):
            continue
        ef = q.get("evidence_file")
        if not ef:
            continue
        registered.add(Path(str(ef)).name.lower())
    return registered


def _max_qual_id(quals: list) -> int:
    max_n = 0
    for q in quals:
        if not isinstance(q, dict):
            continue
        m = QUAL_ID_PATTERN.match(str(q.get("id", "")))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n


def cmd_scan(args: argparse.Namespace) -> int:
    if args.type not in SUPPORTED_TYPES:
        _die(EXIT_PAYLOAD_INVALID, f"不支持的知识类型: {args.type}，可选: {', '.join(sorted(SUPPORTED_TYPES))}")

    paths = ps_paths.knowledge_paths()
    certs_dir: Path = paths["certs"]

    if not certs_dir.exists():
        _die(
            EXIT_DIR_MISSING,
            f"资质证书目录不存在: {certs_dir}\n请先运行 /ps:setup 初始化知识库。",
        )

    profile = _load_yaml(paths["company_profile"])
    registered = _registered_basenames(profile)

    candidates: list[Path] = []
    for p in sorted(certs_dir.iterdir()):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        if p.name == "README.md":
            continue
        if p.suffix.lower() not in CERT_EXTENSIONS:
            continue
        candidates.append(p)

    new_files: list[str] = []
    already = 0
    for p in candidates:
        if p.name.lower() in registered:
            already += 1
        else:
            new_files.append(p.name)

    over_limit = len(new_files) > SCAN_LIMIT
    truncated = new_files[:SCAN_LIMIT] if over_limit else new_files

    result = {
        "type": "certs",
        "certs_dir": str(certs_dir),
        "new_files": truncated,
        "already_registered": already,
        "over_limit": over_limit,
        "limit": SCAN_LIMIT,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


REQUIRED_PAYLOAD_FIELDS = ("file", "name", "issuer", "valid_until")


def _validate_payload(payload) -> list[dict]:
    if not isinstance(payload, list):
        _die(EXIT_PAYLOAD_INVALID, "payload 根必须是 list")
    for i, item in enumerate(payload):
        if not isinstance(item, dict):
            _die(EXIT_PAYLOAD_INVALID, f"payload[{i}] 必须是 dict")
        for field in REQUIRED_PAYLOAD_FIELDS:
            if not item.get(field):
                _die(EXIT_PAYLOAD_INVALID, f"payload[{i}] 缺必填字段: {field}")
    return payload


def cmd_apply(args: argparse.Namespace) -> int:
    if args.payload_file == "-":
        raw = sys.stdin.read()
    else:
        payload_path = Path(args.payload_file)
        if not payload_path.exists():
            _die(EXIT_PAYLOAD_INVALID, f"payload 文件不存在: {payload_path}")
        raw = payload_path.read_text(encoding="utf-8")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        _die(EXIT_PAYLOAD_INVALID, f"payload JSON 解析失败: {e}")

    payload = _validate_payload(payload)

    paths = ps_paths.knowledge_paths()
    profile_path: Path = paths["company_profile"]

    if len(payload) == 0:
        print(json.dumps({"added": 0, "ids": []}, ensure_ascii=False, indent=2))
        return 0

    profile = _load_yaml(profile_path)

    quals = profile.get("qualifications")
    if not isinstance(quals, list):
        quals = []

    next_id = _max_qual_id(quals) + 1
    today = date.today().isoformat()
    added_ids: list[str] = []

    for item in payload:
        qual_id = f"QUAL-{next_id:03d}"
        next_id += 1
        entry = {
            "id": qual_id,
            "name": item["name"],
            "issuer": item["issuer"],
            "cert_no": item.get("cert_no") or None,
            "valid_from": item.get("valid_from") or None,
            "valid_until": item["valid_until"],
            "subject": item.get("subject") or None,
            "evidence_file": f"知识库/资质证书/{item['file']}",
            "ingested_at": today,
            "confidence": item.get("confidence") or "high",
        }
        quals.append(entry)
        added_ids.append(qual_id)

    profile["qualifications"] = quals

    if profile_path.exists():
        bak = profile_path.with_suffix(profile_path.suffix + ".bak")
        bak.write_bytes(profile_path.read_bytes())

    _dump_yaml_atomic(profile_path, profile)

    print(json.dumps({"added": len(added_ids), "ids": added_ids}, ensure_ascii=False, indent=2))
    return 0


def _slugify(name: str) -> str:
    """Convert a directory name to a kebab-case slug.

    Lowercase, replace spaces/underscores with hyphens, strip non-ascii-friendly chars,
    collapse consecutive hyphens, strip leading/trailing hyphens.
    """
    s = name.lower().strip()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff\-]", "", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def _write_text_atomic(path: Path, content: str) -> None:
    """Write text content to path atomically via .tmp + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def cmd_scan_products(args: argparse.Namespace) -> int:
    """Scan an external source directory for product material files."""
    source_dir = Path(args.source)
    if not source_dir.exists():
        _die(EXIT_DIR_MISSING, f"产品材料目录不存在: {source_dir}")

    slug = args.slug if args.slug else _slugify(source_dir.name)

    paths = ps_paths.knowledge_paths()
    products_dir: Path = paths["products"]
    slug_dir = products_dir / slug

    status = "new"
    if slug_dir.exists() and (slug_dir / "facts.yaml").exists():
        if not args.force:
            status = "exists"
        # with --force, status stays "new"

    files: list[dict] = []
    for p in sorted(source_dir.iterdir()):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        if p.suffix.lower() not in PRODUCT_EXTENSIONS:
            continue
        files.append({
            "name": p.name,
            "format": p.suffix.lower().lstrip("."),
            "size": p.stat().st_size,
        })

    result = {
        "slug": slug,
        "source_dir": str(source_dir),
        "files": files,
        "status": status,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


REQUIRED_PRODUCT_PAYLOAD_KEYS = ("facts_yaml", "facts_md", "evidence_yaml", "evidence_md")


def cmd_apply_products(args: argparse.Namespace) -> int:
    """Create product directory with facts + evidence files from payload."""
    if not args.slug:
        _die(EXIT_PAYLOAD_INVALID, "--slug is required for products apply")

    # Read payload
    if args.payload_file == "-":
        raw = sys.stdin.read()
    else:
        payload_path = Path(args.payload_file)
        if not payload_path.exists():
            _die(EXIT_PAYLOAD_INVALID, f"payload 文件不存在: {payload_path}")
        raw = payload_path.read_text(encoding="utf-8")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        _die(EXIT_PAYLOAD_INVALID, f"payload JSON 解析失败: {e}")

    if not isinstance(payload, dict):
        _die(EXIT_PAYLOAD_INVALID, "products payload 根必须是 dict")

    for key in REQUIRED_PRODUCT_PAYLOAD_KEYS:
        if key not in payload:
            _die(EXIT_PAYLOAD_INVALID, f"payload 缺必填字段: {key}")

    paths = ps_paths.knowledge_paths()
    products_dir: Path = paths["products"]
    slug_dir = products_dir / args.slug

    if slug_dir.exists() and not args.force:
        _die(EXIT_PAYLOAD_INVALID, "产品已存在")

    slug_dir.mkdir(parents=True, exist_ok=True)

    _write_text_atomic(slug_dir / "facts.yaml", payload["facts_yaml"])
    _write_text_atomic(slug_dir / "facts.md", payload["facts_md"])
    _write_text_atomic(slug_dir / "evidence.yaml", payload["evidence_yaml"])
    _write_text_atomic(slug_dir / "evidence.md", payload["evidence_md"])

    result = {
        "slug": args.slug,
        "dir": str(slug_dir),
        "files_written": ["facts.yaml", "facts.md", "evidence.yaml", "evidence.md"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ps_knowledge_ingest",
        description="ps:knowledge-ingest scripts layer (scan / apply)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="扫描待入库文件")
    p_scan.add_argument("--type", default="certs", help="知识类型 (certs | products)")
    p_scan.add_argument("--source", default=None, help="产品材料目录路径 (type=products 时必填)")
    p_scan.add_argument("--slug", default=None, help="产品 slug (type=products 时可选，默认从 source 目录名推导)")
    p_scan.add_argument("--force", action="store_true", help="忽略已存在的产品目录")
    p_scan.set_defaults(func=cmd_scan)

    p_apply = sub.add_parser("apply", help="应用批准 payload 写入知识库")
    p_apply.add_argument(
        "--payload-file",
        required=True,
        help="payload JSON 路径，使用 - 表示 stdin",
    )
    p_apply.add_argument("--type", default="certs", help="知识类型 (certs | products)")
    p_apply.add_argument("--slug", default=None, help="产品 slug (type=products 时必填)")
    p_apply.add_argument("--force", action="store_true", help="强制覆盖已存在的产品")
    p_apply.set_defaults(func=cmd_apply)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Route scan/apply by --type
    if args.cmd == "scan":
        if args.type == "products":
            if not args.source:
                _die(EXIT_PAYLOAD_INVALID, "--source is required when --type=products")
            return cmd_scan_products(args)
        return cmd_scan(args)
    elif args.cmd == "apply":
        if args.type == "products":
            return cmd_apply_products(args)
        return cmd_apply(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
