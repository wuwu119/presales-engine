---
title: "feat: 产品知识库构建 — 产品魔方 schema 入库"
type: feat
status: active
date: 2026-04-17
origin: docs/brainstorms/knowledge-products-requirements.md
---

# feat: 产品知识库构建 — 产品魔方 schema 入库

## Overview

扩展 `ps:knowledge-ingest` 支持 `products` 子命令，将产品材料（PDF/Word/Excel/PPT）按产品魔方体系结构化入库为 YAML+MD 双文件。同步升级 knowledge-doctor 产品诊断为分级可用评估，更新 bid-draft/rfp-analyze 的产品发现路径。

这是对现有扁平 `{slug}.yaml` 产品存储结构的**破坏性变更**。

## Problem Frame

知识库产品档案为空（0 个结构化文件），bid-draft 和 rfp-analyze 无产品数据可用。用户有 20+ 产品的成套材料但手工填写不现实。通过天擎 SDK 原型验证，核心事实库约 60% 可自动提取。(see origin: `docs/brainstorms/knowledge-products-requirements.md`)

## Requirements Trace

- R1. 产品存储改为子目录结构 `{slug}/`（破坏性变更，含下游更新清单）
- R2. 每个库 YAML+MD 双文件
- R3. 本期做核心事实库+证据库
- R4. YAML 带 `_q` 质量元数据
- R5-R6. 核心事实库 19 模块 + 证据库 13 模块
- R7. 产品魔方完整 schema 固化到 references
- R7a. 质量检查为结构性检查
- R8. MD 缺失项用 `> ❌` 标注
- R9. 四级可用：已录入→可查→可投→可竞
- R10. knowledge-doctor 升级
- R11. 扩展 knowledge-ingest products 子命令
- R12-R15. 质量检查、交互补全、证据库半自动、批量模式
- R16-R18. 格式支持、只读、slug 确认
- R19. 入库后 mini 诊断

## Scope Boundaries

- 不做策略库交互补全（目录预留交 ps:setup）
- 不做材料文件移动/复制
- 不做跨产品关联
- 不做自动更新（需手动重跑）
- 不做 OCR
- PPT 为实验性支持（best-effort）

### Deferred to Separate Tasks

- 策略库填充：未来 session，需销售/产品团队输入
- rfp-analyze 产品匹配逻辑重写：本期仅更新发现路径，匹配逻辑后续
- 旧扁平 YAML 迁移脚本：本期无已有产品文件，暂不需要

## Context & Research

### Relevant Code and Patterns

- `scripts/ps_knowledge_ingest.py`：scan/apply 双子命令模式，`SUPPORTED_TYPES = {"certs"}` 门控
- `scripts/ps_knowledge_extract.py`：多子命令模式（`team`/`competitors`），`--xlsx` + `--output-dir`
- `scripts/ps_knowledge_doctor.py`：`_diagnose_products` 用 `_count_yaml_files`，阈值 min=1 sufficient=3
- `scripts/ps_paths.py`：`knowledge_paths()["products"]` = `知识库/产品档案/`
- `templates/产品档案/example.yaml`：现有 schema（meta/capabilities/technical/delivery/pricing）
- `knowledge-seed/产品档案/README.md`：描述扁平 `{slug}.yaml` 结构
- `skills/knowledge-ingest/SKILL.md`：5 阶段流程（scan→extract→confirm→apply→mini-doctor）
- `skills/bid-draft/SKILL.md`：读 `产品档案/*.yaml`
- `skills/rfp-analyze/SKILL.md`：读 `产品档案/*.yaml` 做产品匹配

### Institutional Learnings

无（`docs/solutions/` 尚未建立）

## Key Technical Decisions

- **产品入库走 SKILL.md（LLM 决策）而非 scripts/（脚本体力活）**：与 certs 入库不同，产品提取是从非结构化文档到 19 个语义模块的映射，必须由 LLM 完成。脚本只负责文本提取（PDF→text）和文件 IO。SKILL.md 5 阶段流程复用 certs 模式但 IO 契约完全不同
- **不重构 ps_knowledge_ingest.py 为插件式**：certs 的 scan/apply 和 products 的 extract/write IO 差异太大，强行抽象得不偿失。products 新增独立的 `cmd_scan_products`/`cmd_apply_products` 子命令，与 certs 并列
- **产品发现契约：子目录 + facts.yaml 存在 = 一个产品**：knowledge-doctor 和 bid-draft 都按此契约发现产品，不依赖文件名 glob
- **重跑行为：幂等跳过**：如果 `{slug}/facts.yaml` 已存在，默认跳过。用户可用 `--force` 覆盖
- **批量模式：每个产品独立上下文**：产品间清空 LLM 上下文，避免串扰。批量编排由 SKILL.md 控制（循环调用单产品流程）

## Open Questions

### Resolved During Planning

- **products 子命令放 ps_knowledge_ingest.py 还是独立文件？** → 放 `ps_knowledge_ingest.py`，与 certs 并列，共享路径解析和 YAML IO utils
- **facts.yaml schema 谁定义？** → 由 `references/product-cube-schema.md` 定义，SKILL.md 引用
- **evidence.yaml 由谁生成？** → 与 facts 同时生成，案例描述从材料提取，量化成果和证言标 ❌

### Deferred to Implementation

- LLM 单次可处理的材料总量上限，可能需要分批送入
- PPT 提取效果，可能需要多模态识别降级
- 产品魔方写作公式的结构性检查规则细节

## Output Structure

```
skills/knowledge-ingest/
├── SKILL.md                            # 扩展：新增 products 流程
└── references/
    ├── product-cube-schema.md          # 新增：41 模块完整定义
    └── product-extraction-prompt.md    # 新增：LLM 提取 prompt 模板

scripts/
└── ps_knowledge_ingest.py             # 修改：新增 products scan/apply

templates/产品档案/
└── example/                           # 新增：替代原 example.yaml
    ├── facts.yaml
    └── facts.md

knowledge-seed/产品档案/
└── README.md                          # 修改：更新目录结构说明

# 用户数据目录产出（~/售前/知识库/产品档案/{slug}/）：
# ├── facts.yaml
# ├── facts.md
# ├── evidence.yaml
# └── evidence.md
```

## Implementation Units

### Phase 1: Schema 与基础设施

- [ ] **Unit 1: 产品魔方 schema 参考文档**

**Goal:** 将产品魔方 41 模块体系固化为实现的单一真相源

**Requirements:** R7

**Dependencies:** 无

**Files:**
- Create: `skills/knowledge-ingest/references/product-cube-schema.md`

**Approach:**
- 从本次 session 中的产品魔方分析（`产品魔方-内容体系20260410.docx`）提取完整模块定义
- 每个模块包含：ID、名称、所属库（核心事实/证据/策略）、写作公式、字段列表、一票否决项、标签定义
- 标注每个模块的自动提取可行性（auto/manual/hybrid）
- 本期只详细定义核心事实库 19 模块和证据库 13 模块的字段，策略库 9 模块留骨架

**Patterns to follow:**
- `skills/knowledge-ingest/references/cert-extraction-prompt.md` 的 schema 定义风格

**Test expectation:** none — 纯文档

**Verification:**
- schema 覆盖产品魔方全部 41 个模块 ID
- 核心事实库 19 模块每个有写作公式和字段列表
- 证据库 13 模块每个有字段列表

---

- [ ] **Unit 2: 存储结构迁移**

**Goal:** 将产品存储从扁平 YAML 改为子目录双文件结构

**Requirements:** R1, R2

**Dependencies:** Unit 1

**Files:**
- Delete: `templates/产品档案/example.yaml`
- Create: `templates/产品档案/example/facts.yaml`
- Create: `templates/产品档案/example/facts.md`
- Create: `templates/产品档案/example/evidence.yaml`
- Create: `templates/产品档案/example/evidence.md`
- Modify: `knowledge-seed/产品档案/README.md`
- Modify: `scripts/ps_paths.py`（如需新增 helper）
- Test: `tests/test_ps_knowledge_doctor.py`

**Approach:**
- 新 example 模板按 Unit 1 的 product-cube-schema 生成，facts.yaml 含全部 19 模块骨架 + `_q: {confidence: null, gap: "待填充"}`
- facts.md 含全部 19 模块标题和 `> ❌ 待填充` 占位符
- evidence.yaml/md 含 13 模块骨架
- README.md 更新目录结构图和填写说明
- `ps_paths.py` 无需改动（`knowledge_paths()["products"]` 返回的仍是 `产品档案/` 目录）

**Patterns to follow:**
- 现有 `knowledge-seed/` 各子目录的 README.md 风格
- 现有 `templates/company-profile.yaml` 的注释风格

**Test scenarios:**
- Happy path: `ps:setup` 执行后 `产品档案/example/` 目录存在，含 4 个文件
- Edge case: 已有旧 `example.yaml` 时不报错（setup 用 `shutil.copytree` 不 overwrite）

**Verification:**
- `templates/产品档案/example/facts.yaml` 可被 Python YAML 正常解析
- 所有 19 个核心事实模块在 facts.yaml 中有对应 key

---

### Phase 2: 脚本层

- [ ] **Unit 3: ps_knowledge_ingest.py 扩展 products 子命令**

**Goal:** 在现有 scan/apply 架构旁新增 products 的 scan/apply

**Requirements:** R11, R16, R17, R18

**Dependencies:** Unit 2

**Files:**
- Modify: `scripts/ps_knowledge_ingest.py`
- Test: `tests/test_ps_knowledge_ingest.py`

**Approach:**
- `SUPPORTED_TYPES` 扩展为 `{"certs", "products"}`
- 新增 `cmd_scan_products(args)`：
  - 接收 `--source <外部目录>` 参数（与 certs 不同，certs 扫描知识库内部目录）
  - 遍历 source 目录下所有支持格式文件（PDF/docx/xlsx/pptx/md）
  - 检查 `知识库/产品档案/{slug}/facts.yaml` 是否已存在 → 已存在则跳过（除非 `--force`）
  - 输出 JSON：`{slug, source_dir, files: [{name, format, size}], status: "new"|"exists"}`
- 新增 `cmd_apply_products(args)`：
  - 接收 JSON payload（facts + evidence 的结构化数据）
  - 创建 `知识库/产品档案/{slug}/` 目录
  - 写入 facts.yaml + facts.md + evidence.yaml + evidence.md
  - 原子写入：先写 `.tmp` 再 rename
- slug 默认值：source 目录名的 kebab-case 转换

**Patterns to follow:**
- `cmd_scan`/`cmd_apply` 的参数解析和错误处理模式
- `_die()` 错误退出模式
- exit codes 体系（2=HOME, 3=dir, 4=YAML, 5=payload）

**Test scenarios:**
- Happy path: scan 一个包含 3 个 PDF 的目录 → 返回 JSON 含 3 个文件条目
- Happy path: apply 一个合法 payload → 创建 4 个文件，YAML 可解析
- Edge case: source 目录不存在 → exit code 3
- Edge case: slug 目录已存在且无 --force → status "exists"，apply 跳过
- Edge case: slug 目录已存在且有 --force → 覆盖写入
- Error path: payload 缺必填字段 → exit code 5
- Error path: PRESALES_HOME 未设置 → exit code 2

**Verification:**
- `python ps_knowledge_ingest.py scan --type products --source /tmp/test` 返回合法 JSON
- `python ps_knowledge_ingest.py apply --type products --payload <json>` 创建预期目录结构

---

- [ ] **Unit 4: knowledge-doctor 产品诊断升级**

**Goal:** 产品维度从文件计数改为分级可用评估

**Requirements:** R9, R10, R19

**Dependencies:** Unit 2

**Files:**
- Modify: `scripts/ps_knowledge_doctor.py`
- Test: `tests/test_ps_knowledge_doctor.py`

**Approach:**
- `_diagnose_products` 重写：
  - 扫描 `产品档案/` 下的子目录（排除 example）
  - 每个子目录检查 `facts.yaml` 是否存在
  - 解析 facts.yaml 的 `_q` 字段，统计非空模块数
  - 计算 tier：`<60%` = 已录入，`≥60%` = 可查，`≥80% + evidence≥50%` = 可投
- JSON 输出变更：
  - 保留 `value`（产品总数）向后兼容
  - 新增 `products_detail: [{slug, tier, facts_coverage, evidence_coverage, gap_count}]`
- mini 模式（`--mode mini`）：只输出变化项 + 最高优先缺口

**Patterns to follow:**
- 现有 `_diagnose_*` 函数的返回结构
- `_count_yaml_files` 的目录遍历模式

**Test scenarios:**
- Happy path: 空产品目录 → value=0, products_detail=[]
- Happy path: 1 个产品 facts.yaml 含 12/19 模块非空 → tier="可查"
- Happy path: 1 个产品 facts 16/19 + evidence 7/13 → tier="可投"
- Edge case: facts.yaml 存在但 YAML 格式错误 → 该产品标为 error，不影响其他
- Edge case: 只有 evidence.yaml 没有 facts.yaml → 不算有效产品
- Integration: mini 模式输出只含变化项

**Verification:**
- `python ps_knowledge_doctor.py diagnose --mode full` 输出 JSON 含 `products_detail` 字段
- 各 tier 阈值判断正确

---

### Phase 3: Skill 层

- [ ] **Unit 5: LLM 提取 prompt 模板**

**Goal:** 定义 LLM 从产品材料提取结构化信息的 prompt

**Requirements:** R7, R7a, R11

**Dependencies:** Unit 1

**Files:**
- Create: `skills/knowledge-ingest/references/product-extraction-prompt.md`

**Approach:**
- 参考 `cert-extraction-prompt.md` 的结构（role → schema → few-shot → output format）
- prompt 按产品魔方 19 个核心事实模块组织，每个模块给出：期望字段、写作公式、输出 JSON key
- 输出格式为嵌套 JSON：`{overview_intro: {content: "...", _q: {confidence: "high", source: "白皮书§3.1"}}, ...}`
- 证据库 13 模块用独立 prompt（案例提取 prompt）
- 对每个字段标注置信度评估规则

**Patterns to follow:**
- `references/cert-extraction-prompt.md` 的 prompt 结构

**Test expectation:** none — 纯文档，通过实际提取效果验证

**Verification:**
- prompt 覆盖 19 个核心事实模块的全部字段
- 输出 JSON schema 与 Unit 2 的 facts.yaml 模板 key 一致

---

- [ ] **Unit 6: knowledge-ingest SKILL.md 扩展 products 流程**

**Goal:** 定义产品入库的 5 阶段交互流程

**Requirements:** R11, R12, R13, R14, R15, R18, R19

**Dependencies:** Unit 3, Unit 4, Unit 5

**Files:**
- Modify: `skills/knowledge-ingest/SKILL.md`

**Approach:**
- 触发：`/ps:knowledge-ingest products --source <路径>`
- Phase 1 (scan)：调用 `ps_knowledge_ingest.py scan --type products --source <路径>`，展示文件清单，确认 slug
- Phase 2 (extract)：逐个读取材料文件（Read tool），用 product-extraction-prompt 调 LLM 提取
- Phase 3 (review)：展示产品魔方审计表（按模块列出完整度），标注 ✅/⚠️/❌
- Phase 4 (apply)：调用 `ps_knowledge_ingest.py apply --type products`，写入 4 个文件
- Phase 5 (diagnose)：调用 `ps_knowledge_doctor.py diagnose --mode mini`
- 交互补全（R13）：Phase 3 后如果用户选择"补全"，进入对话式逐模块填充
- 批量模式（R15）：循环执行 Phase 1-5，每个产品独立，产品间输出分隔线 + 摘要

**Patterns to follow:**
- 现有 certs 流程的 5 阶段模式
- Phase 结构和编号风格

**Test expectation:** none — SKILL.md 是行为契约文档，由集成测试验证

**Verification:**
- SKILL.md ≤ 150 行（规则约束）
- 覆盖单产品流程 + 批量模式 + 交互补全三个路径
- 每个 Phase 有明确的输入/输出/错误处理

---

### Phase 4: 下游消费者更新

- [ ] **Unit 7: bid-draft / rfp-analyze 产品发现路径更新**

**Goal:** 更新下游 skill 从子目录结构发现产品

**Requirements:** R1（下游更新清单）, SC5

**Dependencies:** Unit 2

**Files:**
- Modify: `skills/bid-draft/SKILL.md`
- Modify: `skills/rfp-analyze/SKILL.md`

**Approach:**
- bid-draft：产品读取路径从 `产品档案/*.yaml` 改为 `产品档案/*/facts.yaml`（结构化参数）+ `产品档案/*/facts.md`（段落引用）
- rfp-analyze：产品匹配路径同步更新，读 `facts.yaml` 中的 `functions.security` 和 `capabilities` 做 RFP 需求匹配
- 两个 SKILL.md 中搜索 `产品档案/*.yaml` 全部替换为新路径
- 本期仅更新发现路径，不改生成逻辑

**Patterns to follow:**
- 各 SKILL.md 现有的路径引用方式

**Test expectation:** none — SKILL.md 行为契约，由端到端验证

**Verification:**
- `grep -r "产品档案/\*.yaml" skills/` 返回空（旧路径全部替换）
- bid-draft 和 rfp-analyze SKILL.md 中包含 `产品档案/*/facts.yaml` 路径

---

- [ ] **Unit 8: 废弃旧产品模板 + setup 更新**

**Goal:** 清理旧扁平模板，setup 复制新子目录结构

**Requirements:** R1, R3

**Dependencies:** Unit 2

**Files:**
- Delete: `templates/产品档案/example.yaml`（被 Unit 2 创建的 `example/` 替代）
- Modify: `scripts/ps_setup_utils.py`（如果 setup 硬编码了 example.yaml 的复制逻辑）

**Approach:**
- 检查 `ps_setup_utils.py` 的 `DEFAULT_DIRS` 和 seed 复制逻辑
- 如果用 `shutil.copytree` 整个目录复制 knowledge-seed，无需改动
- 如果有针对 `example.yaml` 的特殊处理，需适配为目录复制

**Patterns to follow:**
- `ps_setup_utils.py` 现有的目录创建和 seed 复制模式

**Test scenarios:**
- Happy path: `ps:setup` 后 `产品档案/` 下有 README.md，无旧 example.yaml
- Edge case: 已有 `产品档案/` 目录时 setup 不覆盖

**Verification:**
- `templates/产品档案/example.yaml` 不再存在
- `templates/产品档案/example/` 目录含 4 个文件

## System-Wide Impact

- **Interaction graph:** knowledge-ingest(products) → ps_knowledge_ingest.py(scan/apply) → 写入 `产品档案/{slug}/` → knowledge-doctor(diagnose) 读取 → bid-draft/rfp-analyze 消费
- **Error propagation:** LLM 提取失败 → facts.yaml 对应模块 `_q.confidence: null` + facts.md 标 `> ❌` → doctor 报告为缺口 → bid-draft 跳过该模块
- **State lifecycle risks:** 批量模式中途中断 → 部分产品已写入、部分未写入。幂等设计（scan 检查已存在）确保重跑安全
- **API surface parity:** rfp-analyze 和 bid-draft 的产品读取逻辑必须同步更新，否则一个读新路径一个读旧路径
- **Unchanged invariants:** company-profile.yaml 不受影响；certs 入库流程不变；商机目录结构不变

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| LLM 提取质量不稳定，60% 目标可能达不到 | 产品魔方写作公式嵌入 prompt 引导提取；_q 置信度标记低质量字段 |
| PPT 文本提取效果差 | PPT 标为实验性支持，降级时提示用户提供 PDF/Word 替代 |
| 20+ 产品批量处理耗时长 | 每产品独立上下文避免串扰；支持中断后重跑（幂等跳过） |
| 新旧产品 schema 不兼容导致 bid-draft/rfp-analyze 崩溃 | Unit 7 在 Unit 3 之前或同步完成，确保消费者路径先更新 |
| knowledge-doctor JSON schema 变更影响现有渲染 | `value` 字段保留向后兼容，`products_detail` 为新增字段 |

## Documentation / Operational Notes

- `CLAUDE.md` 架构表需更新产品档案目录结构说明
- `CHANGELOG.md` 记录产品存储结构破坏性变更
- progress.md 记录 session 产出

## Sources & References

- **Origin document:** [docs/brainstorms/knowledge-products-requirements.md](docs/brainstorms/knowledge-products-requirements.md)
- **产品魔方原始文档:** `/Users/wuwu/Downloads/110-收件箱/lanxindownload/产品魔方-内容体系20260410.docx`（外部参考，不入库）
- **天擎 SDK 原型:** `~/售前/知识库/产品档案/tianqing-antivirus-sdk/`（实际验证产出）
- Related plan: `docs/plans/2026-04-15-001-feat-knowledge-ingest-certs-plan.md`
- Related plan: `docs/plans/2026-04-16-001-feat-knowledge-schema-extensions-plan.md`
