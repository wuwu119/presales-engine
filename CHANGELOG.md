# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 变更
- **默认数据目录从 `~/.presales/` 改为 `~/presales/`**（无前导点，可见于 Finder/`ls`）
- **所有用户数据目录名全面中文化**：`~/presales/` → `~/售前/`；`opportunities/` → `商机/`；`cases/` → `归档/`；`knowledge/` → `知识库/`（`about/` → `公司介绍/`、`certs/` → `资质证书/`、`case-studies/` → `客户案例/`、`products/` → `产品档案/`、`competitors/` → `竞品/`、`team/` → `团队/`）；`templates/` → `模板/`；opportunity 子目录 `rfp/` → `招标文件/`、`rfp/original/` → `招标文件/原件/`、`analysis/` → `分析/`、`draft/` → `草稿/`、`draft/chapters/` → `草稿/章节/`。Python dict keys 保留英文作为 API 合约
- `ps:setup` 新增 `--home <path>` 标志，允许首次初始化时指定数据目录
- `ps:setup` 交互问答新增 Q1 "父目录"（默认 `~/`），派生 `<parent>/售前/`
- `ps:setup` URL 驱动流程：只问公司官网 URL，Claude 用 WebFetch 抓主页抽取最小字段，其余字段留给未来独立知识库流程
- 新增三层 resolution：`PRESALES_HOME` 环境变量 > `~/.config/presales-engine/home` 指针文件 > `~/售前/` 默认
- `--reset` 备份命名从硬编码 `.presales.backup.<ts>` 改为 `<home-name>.backup.<ts>`，跟随 home 目录命名
- 新增插件目录 `knowledge-seed/`，包含知识库 7 份填充指南 README（根 + 6 子目录），`ps:setup` 时自动拷贝到 `<home>/知识库/`

## [0.1.0] - 2026-04-15

### 新增
- 初始项目骨架（Claude Code plugin 格式）
- 4 个核心 skill：`ps:setup`、`ps:rfp-parse`、`ps:rfp-analyze`、`ps:bid-draft`
- 用户数据目录 `~/.presales/` 和程序严格分离（由 `PRESALES_HOME` 环境变量覆盖）
- 种子模板：`config.yaml`、`company-profile.yaml`、`products/example.yaml`、`outline-zh-CN.yaml`
- 架构设计文档 `docs/design/architecture-v0.1.md`
- 路径解析工具 `scripts/ps_paths.py`
- 初始化脚本 `scripts/ps_setup.py`（支持 `--init` / `--reset` / `--import` / `--check`）
