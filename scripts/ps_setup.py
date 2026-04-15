#!/usr/bin/env python3
# INPUT: argparse, shutil, json, ps_paths
# OUTPUT: init / reset / import / check operations on PRESALES_HOME directory tree
# POS: physical implementation of ps:setup skill. All filesystem writes go through here.
"""presales-engine user data directory bootstrapper.

Invoked by ps:setup skill (never by the user directly).

Modes:
    --init                  create directory skeleton, write config from --config-json
    --reset                 backup PRESALES_HOME to <parent>/<name>.backup.<ts>
    --import <path>         copy 商机/归档/知识库 from another dir
    --check                 print current state, make no changes
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Local imports from same scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ps_paths import (knowledge_paths, plugin_root, presales_home, presales_home_source, seed_knowledge_dir, seed_templates_dir, write_pointer)  # noqa: E402
from ps_setup_utils import (  # noqa: E402
    DEFAULT_DIRS,
    VERSION,
    _UNSAFE_RESET_PATHS,
    _normalize_highlights,
    _now_iso,
    _write_yaml,
)


def init_skeleton(config: dict, force: bool = False) -> int:
    """Create directory skeleton, write configs and seed templates.

    Idempotent. Writes .version last so partial-init crashes stay recoverable.
    """
    home = presales_home()
    kp = knowledge_paths()

    version_file = home / ".version"
    if home.exists() and version_file.exists() and not force:
        current = version_file.read_text().strip()
        if current == VERSION:
            print(f"✅ 已初始化（版本 {VERSION}），位置：{home}")
            print("   若要重置，使用 --reset；若要从旧目录导入，使用 --import <path>")
            return 0

    try:
        home.mkdir(parents=True, exist_ok=True)
        for sub in DEFAULT_DIRS:
            (home / sub).mkdir(parents=True, exist_ok=True)

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
                "highlights": _normalize_highlights(config.get("highlights")),
            })

        _copy_seed_dir(seed_templates_dir(), kp["templates"], force=force)
        _copy_seed_dir(seed_knowledge_dir(), kp["knowledge"], force=force)

        # .version is written LAST so partial-init failures stay recoverable.
        version_file.write_text(VERSION, encoding="utf-8")
    except OSError as e:
        print(f"❌ 初始化失败：{e}", file=sys.stderr)
        print(f"   PRESALES_HOME: {home}", file=sys.stderr)
        print("   请检查权限和磁盘空间后重跑 --init", file=sys.stderr)
        return 1

    print(f"✅ 初始化完成：{home} (v{VERSION})")
    print(f"   config: {config_path}")
    print(f"   company-profile: {profile_path}")
    print(f"下一步：把 RFP 放到 {home}/商机/<项目名>/招标文件/原件/ 后运行 /ps:rfp-parse <项目名>")
    return 0


def _copy_seed_dir(source: Path, target: Path, force: bool) -> None:
    """Recursively copy a plugin seed dir into the user workspace target."""
    if not source.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(source)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or force:
            shutil.copy2(item, dst)


def reset_home() -> int:
    """Back up PRESALES_HOME and remove it. Refuses unsafe paths (depth<3, $HOME, /)."""
    home = presales_home()
    if not home.exists():
        print(f"ℹ️  {home} 不存在，无需重置")
        return 0

    # Catastrophic-path guard. Refuses to touch shallow paths, $HOME, or any
    # well-known shared directory regardless of depth (e.g. /private/tmp on
    # macOS is depth-3 but still a system shared directory).
    if len(home.parts) < 3 or home == Path.home() or home in _UNSAFE_RESET_PATHS:
        print(f"❌ 拒绝重置：PRESALES_HOME 指向不安全路径 {home}", file=sys.stderr)
        print("   原因：路径过浅、等于 home，或位于系统共享目录列表。", file=sys.stderr)
        print("   请检查 PRESALES_HOME 环境变量后重试。", file=sys.stderr)
        return 1

    # Microsecond-resolution timestamp for collision avoidance; fall back to
    # an incrementing counter if a same-microsecond collision still occurs.
    # Backup name is derived from the home dir name, so it lands next to the
    # source rather than always being called ".presales.backup.*".
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = home.parent / f"{home.name}.backup.{ts}"
    counter = 0
    while backup.exists():
        counter += 1
        backup = home.parent / f"{home.name}.backup.{ts}.{counter}"

    try:
        shutil.move(str(home), str(backup))
    except OSError as e:
        print(f"❌ 备份失败：{e}", file=sys.stderr)
        return 1

    print(f"✅ 已备份到 {backup}")
    print("   下一步：运行 /ps:setup 重新初始化")
    return 0


def import_from(source: Path) -> int:
    """Deep-merge 商机 / 归档 / 知识库 from another presales data dir.

    Walks each sub-tree recursively; skips individual files (not whole subdirs)
    so empty placeholder dirs in target don't drop source files.
    """
    if not source.exists():
        print(f"❌ 源目录不存在：{source}", file=sys.stderr)
        return 1

    home = presales_home()
    if not home.exists() or not (home / ".version").exists():
        print("❌ 请先执行 --init，再执行 --import", file=sys.stderr)
        return 1

    copied = 0
    skipped = 0
    for sub in ("商机", "归档", "知识库"):
        src_root = source / sub
        if not src_root.exists():
            continue
        dst_root = home / sub
        dst_root.mkdir(parents=True, exist_ok=True)

        for src_file in src_root.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(src_root)
            dst_file = dst_root / rel
            if dst_file.exists():
                print(f"⚠️  跳过已存在：{dst_file}")
                skipped += 1
                continue
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_file, dst_file)
            except OSError as e:
                print(f"❌ 复制失败 {src_file}: {e}", file=sys.stderr)
                return 1
            copied += 1

    print(f"✅ 从 {source} 导入完成：复制 {copied} 个文件，跳过 {skipped} 个")
    return 0


def check_status() -> int:
    """Print current state without modifying anything."""
    home = presales_home()
    print(f"PRESALES_HOME: {home}")
    print(f"  source: {presales_home_source()} (env / pointer / default)")
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

    if kp["opportunities"].exists():
        print(f"  商机: {sum(1 for i in kp['opportunities'].iterdir() if i.is_dir())} 个")
    if kp["cases"].exists():
        print(f"  归档: {sum(1 for i in kp['cases'].iterdir() if i.is_dir())} 个")
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
    parser.add_argument("--home", help="指定数据存放路径（持久化到 ~/.config/presales-engine/home）")
    parser.add_argument("--config-json", default="{}", help="初始化配置（JSON 字符串）")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的文件")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if not any([args.init, args.reset, args.import_path, args.check]):
        print("❌ 必须指定操作：--init | --reset | --import <path> | --check", file=sys.stderr)
        return 1

    # --home is only meaningful with --init; persists the path and overrides for this process
    if args.home:
        if not args.init:
            print("❌ --home 只能和 --init 一起使用", file=sys.stderr)
            return 1
        home_path = Path(args.home).expanduser().resolve()
        write_pointer(home_path)
        os.environ["PRESALES_HOME"] = str(home_path)

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
