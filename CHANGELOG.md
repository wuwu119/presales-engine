# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 变更
- **默认数据目录从 `~/.presales/` 改为 `~/presales/`**（无前导点，可见于 Finder/`ls`）
- `ps:setup` 新增 `--home <path>` 标志，允许首次初始化时指定数据目录
- 新增三层 resolution：`PRESALES_HOME` 环境变量 > `~/.config/presales-engine/home` 指针文件 > `~/presales/` 默认
- `--reset` 备份命名从硬编码 `.presales.backup.<ts>` 改为 `<home-name>.backup.<ts>`，跟随 home 目录命名

## [0.1.0] - 2026-04-15

### 新增
- 初始项目骨架（Claude Code plugin 格式）
- 4 个核心 skill：`ps:setup`、`ps:rfp-parse`、`ps:rfp-analyze`、`ps:bid-draft`
- 用户数据目录 `~/.presales/` 和程序严格分离（由 `PRESALES_HOME` 环境变量覆盖）
- 种子模板：`config.yaml`、`company-profile.yaml`、`products/example.yaml`、`outline-zh-CN.yaml`
- 架构设计文档 `docs/design/architecture-v0.1.md`
- 路径解析工具 `scripts/ps_paths.py`
- 初始化脚本 `scripts/ps_setup.py`（支持 `--init` / `--reset` / `--import` / `--check`）
