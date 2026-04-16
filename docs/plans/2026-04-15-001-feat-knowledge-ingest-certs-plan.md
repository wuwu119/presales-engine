---
title: "feat: ps:knowledge-ingest MVP (certs)"
type: feat
status: active
date: 2026-04-15
origin: docs/brainstorms/knowledge-ingest-requirements.md
---

# feat: ps:knowledge-ingest MVP (certs)

## Overview

新增 `ps:knowledge-ingest` skill，MVP 只处理 `知识库/资质证书/` 目录。用户把证书 PDF 扔进目录，skill 扫描未登记的文件，由 Claude（skill 宿主 LLM）用 Read 工具读 PDF 抽取元数据，展示确认表格，用户批准后 append 进 `company-profile.yaml.qualifications[]`。原 PDF 不移动，登记状态以 YAML 引用为唯一真相源。

## Problem Frame

v0.1 的 `company-profile.yaml` 中 `qualifications: []` 需要用户手写 YAML + 手填有效期 + 手贴文件路径。没人会填 → `rfp-analyze` 的"是否满足资质"判断退化为瞎猜。ingest 是打破死锁的第一把钥匙。（see origin: `docs/brainstorms/knowledge-ingest-requirements.md` §2）

## Requirements Trace

- R1. 零配置：用户只扔 PDF，不写 YAML / manifest（origin §1, §3.1）
- R2. 只处理 certs/，其他 5 个子目录属于 v0.3 非纳入项（origin §3.2）
- R3. 原地扫描，不移动 / 拷贝文件（origin §4 step 3, §5.4）
- R4. 已登记判定以 `qualifications[].evidence_file` 为唯一真相源（origin §5.2）
- R5. LLM 抽取 → 表格确认 → 批量 append；低置信度行 ⚠️ 强制用户决策（origin §5.3, §5.4）
- R6. qualification 条目新增 `cert_no / ingested_at / confidence` 字段，向后兼容既有读取方（origin §6.1）
- R7. 幂等：重复运行无副作用（origin §7 验收 #2）
- R8. 单次上限 20 个新文件，超出先警告分批（origin §8）
- R9. LLM 不可用直接报错，不走用户手填兜底（origin §8）

## Scope Boundaries

- 非目标：cases/ products/ about/ competitors/ team/ 五类子目录
- 非目标：DOCX / PPTX / 图片扫描件、OCR 能力
- 非目标：证书到期提醒、rollback、跨公司 profile
- 非目标：LLM 不可用时的手填兜底

### Deferred to Separate Tasks

- 其他 5 类知识子目录的 ingest 流程 → v0.3 复用同一套"扫描 + 抽取 + 表格"模板
- 证书到期提醒 skill → v0.3+，独立 `ps:knowledge-review`

## Context & Research

### Relevant Code and Patterns

- `scripts/ps_paths.py:108` `knowledge_paths()` 已返回 `certs` / `company_profile` 路径，无需新增路径常量
- `skills/rfp-parse/SKILL.md` — 最相近的模式：skill 用 Claude 原生 Read 工具读 PDF、LLM 决策抽取、调 script 做文件 IO。直接照搬结构
- `skills/setup/SKILL.md` + `scripts/ps_setup.py` — script 承担所有文件 IO、skill 只编排；script CLI 用 argparse + JSON 输出
- `templates/company-profile.yaml` — `qualifications` 当前 schema，新字段附加式扩展
- `CLAUDE.md` §Skill 间零 import + Python 头注释（INPUT/OUTPUT/POS）规范必须遵守

### Institutional Learnings

- 无独立 `docs/solutions/` 条目。项目自身约束已沉淀在 `CLAUDE.md` 架构约束章节
- Memory: `feedback_skill_md_lean.md` — SKILL.md ≤ 定量上限，行为约束用 script 实现而非文本要求
- Memory: `feedback_design_doc_no_code.md` — 设计文档只写契约；本计划遵守

### External References

本次跳过外部研究。本地模式（rfp-parse / setup）≥ 2 个直接参考，技术栈（Python 3.10 stdlib + YAML + Claude Read 工具）全部在已验证范围内。

## Key Technical Decisions

- **LLM 抽取在 skill 宿主（Claude）里完成，不在 Python 层调 API**：SKILL.md 指令 Claude 用 Read 读 PDF、直接输出 JSON，Python 脚本只做扫描 / 对比 / 写入。理由：零额外依赖，与 rfp-parse 一致
- **Script CLI 模式 = 子命令**：`ps_knowledge_ingest.py scan` / `apply`，而非多个脚本。scan 输出待处理文件 JSON 供 skill 读取，apply 接收批准条目 JSON 写 YAML
- **YAML 写入走最小 diff**：读 → 修改内存对象 → 全文写回，不做 in-place 部分替换。容忍 YAML 注释丢失（种子模板里的示例注释已经被 setup 覆盖，用户版不期望保留注释）。写前备份 `company-profile.yaml.bak`
- **id 生成策略**：扫描现有 `qualifications[].id`，匹配 `^QUAL-(\d+)$`，取最大值 +1，3 位 zero-pad。非该格式的 id 忽略
- **置信度字段由 Claude 自评**：skill prompt 要求每个字段标 high/medium/low，任一关键字段为 medium/low → 整条 confidence=low，UI 标 ⚠️
- **单次上限 20**：在 scan 阶段就截断并报错，不让后续流程处理半截数据

## Open Questions

### Resolved During Planning

- Q: LLM 抽取放哪一层？→ skill 宿主 Claude，Python 不调 API
- Q: YAML 写入策略？→ 全文重写 + .bak 备份
- Q: id 生成规则？→ QUAL-NNN，按现有最大值 +1
- Q: 登记状态存哪？→ 仅存于 `company-profile.yaml.qualifications[].evidence_file`

### Deferred to Implementation

- PDF 抽取 prompt 的 few-shot 样本选哪几张（需要用户在实现期提供 2-3 个真实证书）
- 表格渲染用 Markdown 表 vs Rich 库 — Markdown 更简单且与现有 skill 输出一致，倾向直接用；最终由实现验证观感
- `rfp-analyze` / `bid-draft` 对 `qualifications` 字段的现有读取点审计 — 确认新字段不破坏读取，实现期用 grep 核一次
- 扫描件 PDF 检测策略 — Read 工具返回图像时如何判定。实现时试真实扫描件再定

## Output Structure

    presales-engine/
    ├── skills/
    │   └── knowledge-ingest/
    │       ├── SKILL.md                    ← 新增
    │       └── references/
    │           └── cert-extraction-prompt.md   ← 新增（抽取 prompt + schema）
    ├── scripts/
    │   └── ps_knowledge_ingest.py          ← 新增
    └── tests/
        └── test_ps_knowledge_ingest.py     ← 新增

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
User: /ps:knowledge-ingest certs
│
├── skill Phase 0: 前置检查
│       └─ python scripts/ps_knowledge_ingest.py scan --type certs
│          → stdout JSON: {"new_files": [...], "already_registered": N, "over_limit": false}
│
├── skill Phase 1: LLM 抽取（Claude 自己执行）
│       └─ 对每个 new_file：
│            Read(path) → 读 PDF 文本
│            参照 references/cert-extraction-prompt.md schema 输出 JSON
│            每字段自评 confidence
│
├── skill Phase 2: 表格呈现 + 用户确认
│       └─ Markdown 表：# / 文件 / 证书名 / 发证机构 / 有效期至 / 置信度
│          低置信度行 ⚠️，AskUserQuestion 批量确认 / 勾选
│
└── skill Phase 3: 写入
        └─ python scripts/ps_knowledge_ingest.py apply --payload <json>
           → 读取 company-profile.yaml
           → 分配 QUAL-NNN id，append 到 qualifications[]
           → 写 .bak，原子覆盖写回
           → stdout JSON: {"added": N, "skipped": M}
```

## Implementation Units

- [ ] **Unit 1: 抽取 prompt + schema 参考文档**

**Goal:** 定义 Claude 抽取证书元数据时的输出契约和 few-shot 指引

**Requirements:** R1, R5, R6

**Dependencies:** 无

**Files:**
- Create: `skills/knowledge-ingest/references/cert-extraction-prompt.md`

**Approach:**
- 文档声明 JSON 输出 schema（`name / issuer / cert_no / valid_from / valid_until / subject / per_field_confidence`）
- 列举字段的识别规则（"发证机构"常见关键词、有效期的日期格式兜底、subject 与公司名匹配注意事项）
- 留 2-3 个 few-shot 占位符，实现期用真实样本填充
- 文档内明确"low/medium 任一关键字段 → 整条 confidence=low"

**Patterns to follow:**
- 参考 `skills/rfp-parse/references/`（若存在）的文档语言风格
- SKILL.md 外的细节进 references/，符合 memory `feedback_skill_md_lean.md`

**Test scenarios:**
- Test expectation: none — 纯文档，无行为代码

**Verification:**
- 文档能被 SKILL.md Phase 1 通过相对路径链接引用

---

- [ ] **Unit 2: `ps_knowledge_ingest.py scan` 子命令**

**Goal:** 扫描 `知识库/资质证书/` 与 `company-profile.yaml` 差分，输出待处理文件 JSON

**Requirements:** R2, R3, R4, R7, R8

**Dependencies:** Unit 1（schema 参考）

**Files:**
- Create: `scripts/ps_knowledge_ingest.py`
- Test: `tests/test_ps_knowledge_ingest.py`

**Approach:**
- 头注释三行：INPUT / OUTPUT / POS
- `scan(type: str) -> dict` 函数：
  - 用 `ps_paths.knowledge_paths()` 拿 `certs` 和 `company_profile` 路径
  - 枚举 `certs/*.pdf`（大小写不敏感，忽略 README.md、隐藏文件）
  - 读 `company_profile`（不存在 → 空 qualifications），把 `qualifications[].evidence_file` 收集到 set（路径规范化为相对 PRESALES_HOME）
  - 差分得到 new_files 列表
  - 超过 20 个 → `over_limit: true` + 截断到前 20
- CLI：`python ps_knowledge_ingest.py scan --type certs` → stdout JSON
- 错误退出码：PRESALES_HOME 未初始化 = 2；certs 目录不存在 = 3；YAML 损坏 = 4

**Patterns to follow:**
- `scripts/ps_setup.py` 的 argparse + JSON stdout + 非零退出码模式
- `scripts/ps_paths.py` 的路径解析，禁止硬编码

**Test scenarios:**
- Happy path: 3 个 PDF 全部未登记 → 返回 3 个 new_files，已登记计数 = 0
- Happy path: 3 个 PDF 中 1 个已登记（evidence_file 指向它）→ 返回 2 new，已登记 = 1
- Edge case: certs/ 为空 → 返回空 new_files，退出码 0
- Edge case: 25 个新 PDF → `over_limit: true`，new_files 长度 = 20
- Edge case: certs/ 里混有 README.md 和 .DS_Store → 被忽略
- Edge case: company-profile.yaml 缺失 → 空 qualifications 兜底，不报错
- Error path: PRESALES_HOME 未设置且指针文件不存在 → 退出码 2，stderr 有可读提示
- Error path: company-profile.yaml 存在但 YAML 语法错误 → 退出码 4，不产生半截输出
- Edge case: 已登记 evidence_file 路径大小写 / 斜杠风格差异（`知识库/资质证书/A.pdf` vs 实际 `A.PDF`）→ 匹配策略在测试里固化（建议：文件名大小写不敏感对比）

**Verification:**
- 上述 9 个场景测试通过
- 手工在临时 PRESALES_HOME 下跑一次，stdout 是合法 JSON，能 `python -c "import json,sys; json.load(sys.stdin)"` 解析

---

- [ ] **Unit 3: `ps_knowledge_ingest.py apply` 子命令**

**Goal:** 接收批准条目 JSON，写入 `company-profile.yaml.qualifications[]`，生成 .bak 备份

**Requirements:** R4, R5, R6, R7

**Dependencies:** Unit 2

**Files:**
- Modify: `scripts/ps_knowledge_ingest.py`
- Modify: `tests/test_ps_knowledge_ingest.py`

**Approach:**
- `apply(payload: list[dict]) -> dict`：
  - 输入 schema：`[{file, name, issuer, cert_no, valid_from, valid_until, confidence}, ...]`
  - 读 `company_profile`，找出现有最大 `QUAL-NNN` id，分配新 id
  - 为每条补 `ingested_at: <today>`、`evidence_file: 知识库/资质证书/<basename>`
  - 写 `company-profile.yaml.bak`（复制原文件）
  - 原子写回：tmp file → `os.replace`
  - 返回 `{"added": N, "ids": [...]}`
- CLI：`python ps_knowledge_ingest.py apply --payload-file <path>` 或 `--payload -`（stdin）
- 绝不删除或重排已有 qualifications

**Patterns to follow:**
- PyYAML `safe_load` / `safe_dump` + `allow_unicode=True`（中文字段不转义）
- `os.replace` 原子写入

**Test scenarios:**
- Happy path: 空 qualifications + 2 条 payload → 生成 QUAL-001 / QUAL-002，YAML 写入成功，.bak 文件存在
- Happy path: 已存在 QUAL-005 + 1 条 payload → 新条目 id = QUAL-006
- Edge case: 已存在非标准 id（`CERT-ABC`）+ 1 条 payload → 忽略非标准 id，从 QUAL-001 开始或继续最大数字 id +1
- Edge case: 中文字段（`name: 信息安全管理体系认证`）→ 写入后 YAML 里保持 UTF-8 不转义
- Edge case: payload 为空列表 → 不写 YAML、不生成 .bak、退出码 0、`added: 0`
- Error path: payload 缺必填字段（如 `name`）→ 退出码 5，原 YAML 未被修改
- Error path: company-profile.yaml 写入过程中失败（模拟磁盘满）→ 原文件未损坏，.bak 可用
- Integration: 先跑 scan 得到 new_files，构造 payload 跑 apply，再跑 scan → 第二次 scan 的 new_files 为空，幂等验证
- Integration: apply 写入后，YAML 中 `qualifications[].evidence_file` 路径与 Unit 2 的已登记判定逻辑一致，不会被下一次 scan 误判为新文件

**Verification:**
- 9 个场景测试通过
- 端到端集成测试（scan → 构造 payload → apply → 再 scan）确认幂等

---

- [ ] **Unit 4: `skills/knowledge-ingest/SKILL.md` 编排文档**

**Goal:** 定义 skill 触发 / 前置检查 / 四阶段编排，串起 scan、LLM 抽取、表格确认、apply

**Requirements:** R1, R5, R8, R9

**Dependencies:** Unit 1, 2, 3

**Files:**
- Create: `skills/knowledge-ingest/SKILL.md`

**Approach:**
- ≤ 150 行，结构对齐 `skills/rfp-parse/SKILL.md`
- Frontmatter：name / description / argument-hint（`certs`，v0.2 唯一合法值）
- Sections：前置条件 / 输入 / 输出 / 行为流程（Phase 0-3 对应 HLD）/ 失败模式 / 非 v0.2 的边界声明
- Phase 1 明确指令："对每个 new_file，用 Read 工具读 PDF，按 `references/cert-extraction-prompt.md` 输出 JSON，自评 per-field confidence"
- Phase 2 明确："用 AskUserQuestion 批量展示表格，低置信度行标 ⚠️，用户可勾选 / 全部放行 / 全部跳过"
- Phase 3 明确："构造 payload JSON，调 `python scripts/ps_knowledge_ingest.py apply --payload -`，打印返回摘要"
- 失败模式段：LLM Read 不可用 / payload 为空 / over_limit 分别怎么提示

**Patterns to follow:**
- `skills/rfp-parse/SKILL.md` 的 Phase 编号和章节格式
- CLAUDE.md §SKILL.md 规范（≤ 300 行，只写 agent 推断不出的信息）

**Test scenarios:**
- Test expectation: none — SKILL.md 是 prompt 文档，行为验证走手工 smoke test（见 Unit 5）

**Verification:**
- `wc -l` ≤ 150
- 所有用到的 script 命令都真实存在（与 Unit 2/3 的 CLI 签名一致）
- frontmatter 通过 `ps:setup` 已有的 skill 发现机制能被 Claude Code 加载

---

- [ ] **Unit 5: 端到端 smoke test + 文档同步**

**Goal:** 用真实 PDF 跑通一次完整流程，把 skill 登记进路线图文档

**Requirements:** R1-R9 全量验收

**Dependencies:** Unit 1-4 全部完成

**Files:**
- Modify: `docs/design/skill-catalog.md`（§3.1 ingest 状态从 🚧 改 ✅ v0.2-MVP）
- Modify: `docs/design/architecture-v0.1.md`（如 §8 有 v0.2 清单）
- Modify: `README.md`（开发路线段 v0.2 勾选）
- Modify: `progress.md`（追加 session 记录）
- Modify: `CHANGELOG.md`（Unreleased 段）

**Approach:**
- 用户提供 2-3 张真实证书 PDF → 放进临时 PRESALES_HOME 的 `知识库/资质证书/`
- 执行 `/ps:knowledge-ingest certs`，按 origin §7 的 5 条验收清单逐条验证：
  1. 冷启动 3 条全进
  2. 立刻再跑 = 跳过 3
  3. 扫描件 PDF 整行 ⚠️ 并可跳过
  4. `evidence_file` 路径真实存在
  5. `知识库/` 下无 `.ingest-state.json` 等隐藏文件
- 验收过程中发现的 prompt 缺陷回填进 Unit 1 的 few-shot

**Patterns to follow:**
- `progress.md` 历史 session 的格式

**Test scenarios:**
- Integration: 跑完 5 条验收 → 逐条勾选结果记录进 progress.md
- Integration: 抽取置信度低的真实样本 → prompt 需要调参时记录决策

**Verification:**
- origin §7 的 5 条全部通过
- 路线图文档状态已更新
- progress.md 有本次 session 完整记录

## System-Wide Impact

- **Interaction graph:** skill 只写 `company-profile.yaml`，不碰 `商机/*` 子树。`rfp-analyze` / `bid-draft` 是下游读者，新增字段是附加式 → 零破坏
- **Error propagation:** script 错误用退出码 + stderr 传递；skill 捕获后中文化提示用户。LLM 不可用时直接报错退出，不吞异常
- **State lifecycle risks:** `.bak` 与原文件的竞争（如 apply 中途 Ctrl-C）→ 原子写入 + 先备份再写确保至少 .bak 可用
- **API surface parity:** v0.3 其余 5 类子目录的 ingest 会复用 scan/apply 接口，子命令第一个参数 `--type` 是扩展点
- **Integration coverage:** Unit 5 smoke test 覆盖 scan + LLM + apply 的真实链路
- **Unchanged invariants:** `qualifications[]` 既有 `id / name / valid_until / evidence_file` 字段语义不变；rfp-analyze 现有读取点不改

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| PDF 抽取 prompt 质量不稳定，不同证书格式差异大 | Unit 1 设计 schema + few-shot，Unit 5 用真实样本调参；置信度字段作为用户层兜底 |
| 扫描件 PDF 返回图像，Read 抽取失败 | skill Phase 1 明确检测策略并整行标 ⚠️，用户跳过即可；不强行 OCR |
| YAML 写入丢注释 | 容忍（种子注释在 setup 阶段即被用户内容覆盖，非用户期望保留） + `.bak` 兜底 |
| 用户误删 `evidence_file` 引用后原文件成孤儿 | 超出 MVP 范围，v0.3 加 `ps:knowledge-doctor` 做孤儿扫描 |
| Python PyYAML 依赖是否已在 setup 流程中 | 实现期 `grep -r "import yaml" scripts/` 确认；若未引入，在 Unit 2 补 requirements |

## Documentation / Operational Notes

- 更新 `docs/design/skill-catalog.md` §3.1 把 ingest 状态从 🚧 改为 ✅ v0.2-MVP
- 更新 `README.md` 开发路线段
- `CHANGELOG.md` Unreleased 段记录 "feat: ps:knowledge-ingest (certs MVP)"
- `progress.md` 追加本次 session 记录
- 本 skill 不需运维监控，纯本地文件工具

## Sources & References

- **Origin document:** `docs/brainstorms/knowledge-ingest-requirements.md`
- Related code:
  - `scripts/ps_paths.py` — `knowledge_paths()` 已有 certs/company_profile 路径
  - `skills/rfp-parse/SKILL.md` — 最近的 skill 结构参考
  - `scripts/ps_setup.py` — script CLI 模式参考
  - `templates/company-profile.yaml` — qualifications schema 基线
- Related planning:
  - `docs/design/skill-catalog.md` §3.1 §8 §11 — v0.2 优先级与开放决策上下文
  - `docs/design/architecture-v0.1.md` §10 — 架构约束（证据链完整性）
