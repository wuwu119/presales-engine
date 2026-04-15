#!/usr/bin/env python3
# INPUT: argparse, shutil, json, ps_paths
# OUTPUT: init / reset / import / check operations on PRESALES_HOME directory tree
# POS: physical implementation of ps:setup skill. All filesystem writes go through here.
"""presales-engine user data directory bootstrapper.

Invoked by ps:setup skill (never by the user directly).

Modes:
    --init                  create directory skeleton, write config from --config-json
    --reset                 backup PRESALES_HOME to ~/.presales.backup.<ts>
    --import <path>         copy opportunities/cases/knowledge from another dir
    --check                 print current state, make no changes
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Local import from same scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ps_paths import knowledge_paths, plugin_root, presales_home, seed_templates_dir  # noqa: E402

VERSION = "0.1.0"

DEFAULT_DIRS: list[str] = [
    "opportunities",
    "cases",
    "knowledge",
    "knowledge/products",
    "knowledge/competitors",
    "templates",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _try_yaml_dump(data: dict) -> str:
    """Serialize to YAML. Prefers PyYAML, falls back to minimal in-house writer."""
    try:
        import yaml  # type: ignore
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    except ImportError:
        return _fallback_yaml(data)


def _fallback_yaml(data, indent: int = 0) -> str:
    """Minimal YAML serializer used when PyYAML isn't installed.

    Supports dict / list / scalars nested reasonably. Not a full YAML writer.
    """
    lines: list[str] = []
    pad = "  " * indent

    if isinstance(data, dict):
        if not data:
            return pad + "{}\n"
        for k, v in data.items():
            if isinstance(v, dict):
                if not v:
                    lines.append(f"{pad}{k}: {{}}")
                else:
                    lines.append(f"{pad}{k}:")
                    lines.append(_fallback_yaml(v, indent + 1).rstrip("\n"))
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{pad}{k}: []")
                else:
                    lines.append(f"{pad}{k}:")
                    for item in v:
                        if isinstance(item, (dict, list)):
                            inner = _fallback_yaml(item, indent + 1).rstrip("\n")
                            first_line_pad = "  " * (indent + 1)
                            inner_lines = inner.split("\n")
                            inner_lines[0] = f"{first_line_pad[:-2]}- {inner_lines[0].lstrip()}"
                            lines.extend(inner_lines)
                        else:
                            lines.append(f"{pad}  - {_fmt_scalar(item)}")
            else:
                lines.append(f"{pad}{k}: {_fmt_scalar(v)}")
        return "\n".join(lines) + "\n"

    if isinstance(data, list):
        if not data:
            return pad + "[]\n"
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(_fallback_yaml(item, indent + 1).rstrip("\n"))
            else:
                lines.append(f"{pad}- {_fmt_scalar(item)}")
        return "\n".join(lines) + "\n"

    return pad + _fmt_scalar(data) + "\n"


def _fmt_scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "":
        return '""'
    needs_quote = any(ch in s for ch in (":", "#", "\n", "'", '"', "{", "}", "[", "]", ",", "&", "*", "!", "|", ">", "%", "@", "`"))
    if needs_quote or s.lstrip() != s:
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_try_yaml_dump(data), encoding="utf-8")


def init_skeleton(config: dict, force: bool = False) -> int:
    """Create directory skeleton, write config and seed templates. Idempotent."""
    home = presales_home()
    kp = knowledge_paths()

    version_file = home / ".version"
    if home.exists() and version_file.exists() and not force:
        current = version_file.read_text().strip()
        if current == VERSION:
            print(f"✅ 已初始化（版本 {VERSION}），位置：{home}")
            print("   若要重置，使用 --reset；若要从旧目录导入，使用 --import <path>")
            return 0

    home.mkdir(parents=True, exist_ok=True)
    for sub in DEFAULT_DIRS:
        (home / sub).mkdir(parents=True, exist_ok=True)

    version_file.write_text(VERSION, encoding="utf-8")

    config_path = kp["config"]
    if not config_path.exists() or force:
        _write_yaml(config_path, {
            "meta": {
                "version": VERSION,
                "initialized_at": _now_iso(),
            },
            "company": {
                "name_zh": config.get("company_name_zh", ""),
                "name_en": config.get("company_name_en", ""),
                "industry": config.get("industry", ""),
                "product_lines": config.get("product_lines", []),
            },
            "preferences": {
                "language": config.get("language", "zh-CN"),
                "currency": config.get("currency", "CNY"),
            },
        })

    profile_path = kp["company_profile"]
    if not profile_path.exists() or force:
        _write_yaml(profile_path, {
            "company": {
                "name_zh": config.get("company_name_zh", ""),
                "name_en": config.get("company_name_en", ""),
                "founded": None,
                "size": None,
                "location": None,
            },
            "qualifications": [],
            "case_references": [],
            "team": [],
            "highlights": config.get("highlights", []) if isinstance(config.get("highlights"), list) else [config.get("highlights")] if config.get("highlights") else [],
        })

    _copy_seed_templates(kp["templates"], force=force)

    print(f"✅ 初始化完成：{home}")
    print(f"   版本：{VERSION}")
    print(f"   config：{config_path}")
    print(f"   company-profile：{profile_path}")
    print("")
    print("下一步：")
    print(f"  1. 把 RFP 文件放到 {home}/opportunities/<项目名>/rfp/original/")
    print("  2. 运行 /ps:rfp-parse <项目名>")
    print(f"  3. 按需补充 {profile_path}（案例、资质、团队）")
    return 0


def _copy_seed_templates(target_dir: Path, force: bool) -> None:
    """Copy plugin's seed templates/ into the user's templates dir."""
    seed = seed_templates_dir()
    if not seed.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in seed.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(seed)
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or force:
            shutil.copy2(item, dst)


def reset_home() -> int:
    """Back up the existing PRESALES_HOME and remove it. Caller should re-run --init."""
    home = presales_home()
    if not home.exists():
        print(f"ℹ️  {home} 不存在，无需重置")
        return 0
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = home.parent / f".presales.backup.{ts}"
    shutil.move(str(home), str(backup))
    print(f"✅ 已备份到 {backup}")
    print("   下一步：运行 /ps:setup 重新初始化")
    return 0


def import_from(source: Path) -> int:
    """Copy opportunities / cases / knowledge from another presales data dir."""
    if not source.exists():
        print(f"❌ 源目录不存在：{source}", file=sys.stderr)
        return 1

    home = presales_home()
    if not home.exists() or not (home / ".version").exists():
        print("❌ 请先执行 --init，再执行 --import", file=sys.stderr)
        return 1

    copied = 0
    skipped = 0
    for sub in ("opportunities", "cases", "knowledge"):
        src = source / sub
        if not src.exists():
            continue
        dst = home / sub
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            target = dst / item.name
            if target.exists():
                print(f"⚠️  跳过已存在：{target}")
                skipped += 1
                continue
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
            copied += 1

    print(f"✅ 从 {source} 导入完成：复制 {copied} 项，跳过 {skipped} 项")
    return 0


def check_status() -> int:
    """Print current state without modifying anything."""
    home = presales_home()
    print(f"PRESALES_HOME: {home}")
    print(f"  exists: {home.exists()}")
    if not home.exists():
        print("  状态: 未初始化（运行 /ps:setup）")
        return 0

    version_file = home / ".version"
    if version_file.exists():
        v = version_file.read_text().strip()
        print(f"  version: {v}")
        if v != VERSION:
            print(f"  ⚠️  插件版本 ({VERSION}) 与数据目录版本 ({v}) 不一致，可能需要迁移")
    else:
        print("  version: <缺失>")

    kp = knowledge_paths()
    for name, path in (("config", kp["config"]), ("company_profile", kp["company_profile"])):
        print(f"  {name}: {'✅' if path.exists() else '❌ 缺失'} {path}")

    opps = kp["opportunities"]
    if opps.exists():
        count = sum(1 for item in opps.iterdir() if item.is_dir())
        print(f"  opportunities: {count} 个")

    cases = kp["cases"]
    if cases.exists():
        count = sum(1 for item in cases.iterdir() if item.is_dir())
        print(f"  cases: {count} 个")

    print(f"  plugin_root: {plugin_root()}")
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ps_setup",
        description="presales-engine 数据目录初始化脚本（由 /ps:setup skill 调用）",
    )
    parser.add_argument("--init", action="store_true", help="初始化目录骨架")
    parser.add_argument("--reset", action="store_true", help="备份并重置数据目录")
    parser.add_argument("--import", dest="import_path", help="从另一个数据目录导入")
    parser.add_argument("--check", action="store_true", help="检查当前状态")
    parser.add_argument("--config-json", default="{}", help="初始化配置（JSON 字符串）")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的文件")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if not any([args.init, args.reset, args.import_path, args.check]):
        print("❌ 必须指定操作：--init | --reset | --import <path> | --check", file=sys.stderr)
        return 1

    if args.check:
        return check_status()

    if args.reset:
        return reset_home()

    if args.init:
        try:
            config = json.loads(args.config_json)
        except json.JSONDecodeError as e:
            print(f"❌ --config-json 不是合法的 JSON: {e}", file=sys.stderr)
            return 1
        rc = init_skeleton(config, force=args.force)
        if rc != 0:
            return rc

    if args.import_path:
        return import_from(Path(args.import_path).expanduser().resolve())

    return 0


if __name__ == "__main__":
    sys.exit(main())
