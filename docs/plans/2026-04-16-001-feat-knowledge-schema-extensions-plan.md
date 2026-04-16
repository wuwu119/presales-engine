---
title: "feat: knowledge-base schema extensions (team certs / competitors / product certs)"
type: feat
status: active
date: 2026-04-16
origin: docs/brainstorms/knowledge-schema-extensions-requirements.md
---

# feat: 知识库 schema 扩展（人员证书 / 竞品对比 / 产品证书）

## Overview

新增 `scripts/ps_knowledge_extract.py`，从投标参考材料 Excel 批量转换为知识库 YAML 文件。已通过手动原型验证：roster.yaml 汇总 + cert-registry 分片、竞品每家一个 YAML、产品证书扩展现有 schema。本计划将原型代码固化为可复用脚本 + 测试。

## Problem Frame

手动原型已产出有效数据（roster.yaml 140 行、5 个 cert 分片、29 个竞品 YAML），但代码散落在会话 inline 脚本中，不可复用。需要固化为 `scripts/` 层的正式脚本，并更新 `knowledge-seed/` README 文档以反映新 schema。（see origin: `docs/brainstorms/knowledge-schema-extensions-requirements.md`）

## Requirements Trace

- R1. 人员证书：roster.yaml 汇总层 + cert-registry-*.yaml 分片明细，LLM 直读（origin §4.1）
- R2. 竞品对比：每家竞品一个 YAML，从矩阵 Excel 自动拆分（origin §4.2）
- R3. 产品证书：扩展产品 YAML schema 加 certifications: 字段（origin §4.3）— 本期只建 schema，不做 Excel 转换（依赖先有产品 YAML 基础文件）
- R4. 所有 YAML 文件 ≤ 1000 行（origin §3）
- R5. 原始 Excel 保留在知识库对应目录作备查（origin §6.6）

## Scope Boundaries

- 非目标：rfp-analyze / bid-draft 对新字段的消费逻辑改造（独立 PR）
- 非目标：自动更新 / 过期提醒（v0.3 knowledge-review）
- 非目标：产品档案从 Excel 完整转换（需要先手工建产品基础文件）

## Key Technical Decisions

- **一个脚本两个子命令**：`ps_knowledge_extract.py team --xlsx <path>` 和 `competitors --xlsx <path>`，与 `ps_knowledge_ingest.py` 的 scan/apply 模式保持一致
- **紧凑格式**：cert-registry 分片用 pipe-delimited 字符串（`姓名|工号|证书类型|编号|有效期`），每条 1 行，手动原型已验证 ≤300 行 / 分片
- **分片策略硬编码在脚本中**：一级类别 → shard 名称的映射表，不做动态推断。实现期根据 Excel 实际分布定最终映射
- **竞品 slug 映射硬编码**：公司名 → slug 字典，从手动原型直接搬入
- **openpyxl 依赖**：`pip install openpyxl`，与 PyYAML 同为可选依赖，运行时 lazy import + 友好报错

## Implementation Units

- [ ] **Unit 1: `ps_knowledge_extract.py team` 子命令**

**Goal:** 从人员资质 Excel 生成 roster.yaml + cert-registry-*.yaml 分片

**Requirements:** R1, R4

**Dependencies:** 无

**Files:**
- Create: `scripts/ps_knowledge_extract.py`
- Test: `tests/test_ps_knowledge_extract.py`

**Approach:**
- 头注释三行 INPUT/OUTPUT/POS
- `team(xlsx_path, output_dir)` 函数：读 "人员资质明细（有效）" sheet → 聚合 cert_summary → 写 roster.yaml；按一级类别分片 → 写 cert-registry-{shard}.yaml
- 分片映射表从手动原型搬入（CISP/PMP/security/it-mgmt/other）
- CLI：`python ps_knowledge_extract.py team --xlsx <path> --output-dir <知识库/团队/>`
- 输出 JSON 摘要：`{"roster_lines": N, "shards": {"cisp": 286, ...}, "total_certs": 1085}`

**Patterns to follow:**
- `scripts/ps_knowledge_ingest.py` 的 argparse + JSON stdout 模式
- `scripts/ps_paths.py` 的路径解析

**Test scenarios:**
- Happy path: 提供 mock Excel（3 行 CISP + 2 行 PMP）→ roster.yaml 有 cert_summary + 2 个分片文件
- Happy path: cert_summary 按类型计数正确
- Edge case: Excel 中某行缺姓名 → 跳过该行，不报错
- Edge case: 有效期列为空 → 分片中该条目 valid_until 为空字符串
- Edge case: 一级类别不在映射表中 → 归入 other 分片
- Error path: xlsx 文件不存在 → 退出码 2
- Error path: sheet 名不匹配 → 退出码 3
- Integration: 生成的每个分片文件行数 ≤ 1000

**Verification:**
- 对真实 Excel 跑一次，输出与手动原型的文件 diff 为零或仅格式差异

---

- [ ] **Unit 2: `ps_knowledge_extract.py competitors` 子命令**

**Goal:** 从公司级资质沙盘 Excel 生成每家竞品一个 YAML

**Requirements:** R2, R4

**Dependencies:** Unit 1（共享 argparse 框架）

**Files:**
- Modify: `scripts/ps_knowledge_extract.py`
- Modify: `tests/test_ps_knowledge_extract.py`

**Approach:**
- `competitors(xlsx_path, output_dir)` 函数：读 "公司级资质竞争分析沙盘" sheet → 解析 category 行（forward-fill 合并单元格）→ 跳过元数据行（发证单位/查询链接/级别说明）→ 跳过我方行（"奇安信网神"）→ 每家生成 `{slug}.yaml`
- slug 映射硬编码（从手动原型搬入）
- 资质值为 "×" 或空 → 不写入该条目
- CLI：`python ps_knowledge_extract.py competitors --xlsx <path> --output-dir <知识库/竞品/>`

**Patterns to follow:**
- Unit 1 的 CLI 模式

**Test scenarios:**
- Happy path: mock Excel 3 家公司 × 5 种资质 → 生成 3 个 YAML（跳过我方）
- Happy path: 某家公司某项资质为 "×" → 该条目不出现在 YAML 中
- Edge case: 公司名不在 slug 映射中 → 自动生成 slug（拼音或 sanitize）
- Edge case: 合并单元格的 category 列正确 forward-fill
- Error path: sheet 名不匹配 → 退出码 3

**Verification:**
- 对真实 Excel 跑一次，输出与手动原型的 29 个文件一致

---

- [ ] **Unit 3: 产品 schema 模板更新 + knowledge-seed README 更新**

**Goal:** 更新产品档案模板加 certifications: 字段，更新知识库各子目录 README 反映新 schema

**Requirements:** R3, R5

**Dependencies:** 无

**Files:**
- Modify: `templates/产品档案/example.yaml`（加 certifications: 字段）
- Modify: `knowledge-seed/团队/README.md`（加 roster.yaml + cert-registry schema 说明）
- Modify: `knowledge-seed/竞品/README.md`（加 per-competitor YAML schema 说明）
- Modify: `knowledge-seed/产品档案/README.md`（加 certifications 字段说明）

**Approach:**
- 产品模板加 `certifications: []` 字段 + 注释示例
- 团队 README 加两层结构说明（汇总 + 分片）+ pipe-delimited 格式约定
- 竞品 README 加 per-company YAML schema + slug 命名约定
- 产品 README 加 certifications 字段说明

**Test scenarios:**
- Test expectation: none — 纯文档变更

**Verification:**
- 模板 YAML 合法可解析
- README 内容与实际生成的文件格式一致

---

- [ ] **Unit 4: 文档同步 + 原始 Excel 归档指引**

**Goal:** 更新 CHANGELOG / progress / skill-catalog 状态

**Dependencies:** Unit 1-3

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `progress.md`
- Modify: `docs/design/skill-catalog.md`

**Approach:**
- CHANGELOG Unreleased 段加 schema 扩展条目
- progress.md 追加 session
- skill-catalog §11 开放决策标注已解决的条目

**Test scenarios:**
- Test expectation: none — 纯文档

**Verification:**
- 文档更新完整

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| openpyxl 未安装 | lazy import + 友好中文报错（与 PyYAML 一致） |
| Excel 格式变化（列名/sheet 名改动） | 硬编码 sheet 名 + 列索引，变化时报错退出，不静默出错 |
| 手动原型已产出数据在 ~/售前/，脚本重跑会覆盖 | apply 前检查 output_dir 是否已有同名文件，有则跳过或 --force 覆盖 |

## Sources & References

- **Origin document:** `docs/brainstorms/knowledge-schema-extensions-requirements.md`
- 手动原型验证：本次会话内 inline 脚本，已产出到 `~/售前/知识库/团队/` 和 `~/售前/知识库/竞品/`
- Related code: `scripts/ps_knowledge_ingest.py`（CLI 模式参考）
