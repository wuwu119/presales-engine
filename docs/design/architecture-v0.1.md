# presales-engine v0.1 架构设计

> 本文档只描述接口契约和约束，不写实现代码。实现细节在代码阶段决定。

## 1. 设计目标

1. **程序和数据严格分离** — 插件只读（`${CLAUDE_PLUGIN_ROOT}`），数据可写（`${PRESALES_HOME}` 默认 `~/.presales/`）。卸载插件不影响用户数据。
2. **最小闭环优先** — v0.1 只做应标链路，一个 opportunity 能从 RFP 走到标书草稿。
3. **每段标书可追溯** — `draft/chapters/*.md` 中每个段落必须对应 `rfp.yaml` 评分项或需求条目。
4. **知识累积反哺** — 历史 opportunity 归档到 `cases/`，未来 skill 可检索。
5. **LLM 做决策，脚本做体力活** — 判断类逻辑留给 skill，文件操作交给 `scripts/`。

## 2. 路径约定

| 变量 | 含义 | 默认值 | 来源 |
|------|------|--------|------|
| `PLUGIN_ROOT` | 插件根目录（只读） | - | Claude Code 注入 `${CLAUDE_PLUGIN_ROOT}` |
| `PRESALES_HOME` | 用户数据根目录（可写） | `~/.presales/` | 环境变量 |

统一由 `scripts/ps_paths.py` 解析，**禁止硬编码**。

## 3. 用户数据目录契约

```
${PRESALES_HOME}/
├── .version                    # 插件版本号（升级时迁移用）
├── config.yaml                 # 用户配置
├── opportunities/
│   └── {slug}/
│       ├── meta.yaml
│       ├── rfp/
│       │   ├── original/       # 原始招标文件
│       │   └── extracted.md    # 文本提取（Markdown）
│       ├── analysis/
│       │   ├── rfp.yaml
│       │   └── analysis.md
│       ├── draft/
│       │   ├── outline.md
│       │   └── chapters/
│       └── review.md           # v0.2 引入
├── cases/                      # 归档的 opportunity
├── knowledge/
│   ├── company-profile.yaml
│   ├── products/
│   └── competitors/            # v0.2 引入
└── templates/                  # 用户自定义（覆盖插件种子）
```

## 4. Skill 契约

### 4.1 ps:setup

| 字段 | 内容 |
|------|------|
| 输入 | 交互式问答（可选 `--reset`、`--import <path>`、`--check`） |
| 输出 | `${PRESALES_HOME}/` 目录骨架 + `config.yaml` + `company-profile.yaml` + `.version` |
| 前置条件 | Python 3.10+、写权限 |
| 幂等性 | 是（已存在的文件不覆盖，除非 `--reset`） |
| 失败模式 | 权限不足 / 磁盘满 / `--import` 源不存在 |

### 4.2 ps:rfp-parse

| 字段 | 内容 |
|------|------|
| 输入 | `{slug}/rfp/original/*.{pdf,docx,md,txt}` |
| 输出 | `{slug}/analysis/rfp.yaml` + `{slug}/rfp/extracted.md` + `{slug}/meta.yaml` |
| 前置条件 | setup 已执行、原始文件存在 |
| Schema | 见 §5 |
| 失败模式 | 无法读取 PDF、文件格式不支持、`--force` 未指定但 `rfp.yaml` 已存在 |

### 4.3 ps:rfp-analyze

| 字段 | 内容 |
|------|------|
| 输入 | `{slug}/analysis/rfp.yaml` + `knowledge/company-profile.yaml` + `knowledge/products/*.yaml` |
| 输出 | `{slug}/analysis/analysis.md` |
| 必含段落 | 执行摘要 / 废标风险扫描 / 评分杠杆分析 / 竞品格局推断 / Go-NoGo 决策矩阵 / 信息缺口 / 投标建议 |
| 失败模式 | `rfp.yaml` 格式不合规、`company-profile` 缺失关键字段 |

### 4.4 ps:bid-draft

| 字段 | 内容 |
|------|------|
| 输入 | `rfp.yaml` + `analysis.md` + `outline.md`（可选） + `templates/` |
| 输出 | `{slug}/draft/outline.md` + `{slug}/draft/chapters/*.md` |
| 硬约束 | Go/No-Go = `No-Go` 时拒绝执行；每段末尾必须含 `[对标: SCORING-<id> / REQ-<id> / DISQ-<id>]` 标记；评分项覆盖率 < 100% 强制报警 |
| 失败模式 | 前置文件缺失、模板读取失败、覆盖率不足 |

## 5. rfp.yaml Schema

```yaml
meta:
  slug: string                 # opportunity slug（同目录名）
  customer: string             # 甲方名称
  project_name: string         # 项目名称
  issued_date: string          # ISO 8601，RFP 发布日期
  deadline: string             # ISO 8601，投标截止日期
  language: string             # zh-CN | en
  currency: string             # CNY | USD | EUR

qualifications:                # 资质要求（硬性）
  - id: string                 # QUAL-001
    description: string
    mandatory: bool
    evidence_type: string      # cert | license | financial | case | other
    source_section: string     # RFP 章节/页码引用

scoring:                       # 评分项
  - id: string                 # SCORING-001
    section: string            # 所属章节
    description: string
    weight: number             # 百分比，全表总和 ∈ [99, 101]
    type: string               # tech | commercial | qualification
    sub_items:                 # 可选子项
      - description: string
        max_score: number

disqualifications:             # 废标项（任一触发即废标）
  - id: string                 # DISQ-001
    description: string
    source_section: string     # RFP 章节引用

requirements:                  # 功能 / 技术需求
  - id: string                 # REQ-001
    category: string           # functional | non-functional | integration
    description: string
    priority: string           # must | should | may
    verification: string       # 验收方式
    source_section: string

timeline:
  bid_open: string             # 投标开始
  bid_close: string            # 投标截止
  clarification_deadline: string
  evaluation_date: string
  award_date: string

key_dates:                     # 其他关键日期（合同签订、项目启动等）
  - name: string
    date: string
    notes: string

parsing_meta:
  source_files: list           # 原始文件列表
  parse_confidence: number     # 0-1
  parsed_at: string            # ISO 8601
  parser_version: string
  ambiguities:                 # 解析时的歧义点，人工复核
    - field: string
      reason: string
      suggested_value: string
```

**校验规则**：
- 必填字段齐全
- `scoring[].weight` 总和 ∈ [99, 101]（允许 1% 舍入误差）
- `deadline > issued_date`
- 所有 `disqualifications[].source_section` 非空
- 所有 `id` 字段在同类列表中唯一

## 6. 跨 Skill 依赖图

```
┌──────────┐
│ ps:setup │  （一次性）
└────┬─────┘
     │ 创建 PRESALES_HOME 骨架
     ▼
┌───────────────┐     ┌─────────────────┐     ┌───────────────┐
│ ps:rfp-parse  │ ──▶ │ ps:rfp-analyze  │ ──▶ │ ps:bid-draft  │
└───────────────┘     └─────────────────┘     └───────────────┘
  rfp.yaml              analysis.md             outline.md
  extracted.md                                   chapters/
  meta.yaml
```

**约束**：
- `rfp-analyze` 必须等 `rfp-parse` 产出 `rfp.yaml`
- `bid-draft` 必须等 `rfp-analyze` 产出 `analysis.md` 且决策 ∈ {Go, Conditional-Go}
- skill 间零 import，只通过文件系统通信
- 每个 skill 能独立重跑，不破坏其他 skill 的产出

## 7. 版本迁移

`.version` 文件记录当前数据目录对应的插件版本。`ps:setup` 被再次调用时：
1. 读取 `.version`
2. 比对当前插件版本
3. 若有迁移需要，执行 `scripts/migrations/v{old}_to_v{new}.py`（v0.1 无迁移）
4. 更新 `.version`

## 8. 未来演进（非本版本）

| 版本 | 新增 skill | 新增脚本 |
|------|-----------|---------|
| v0.2 | `ps:bid-review`（合规 + 多角色批判）、`ps:bid-qa`（澄清问答） | `bid_coverage.py`、`compliance_check.py` |
| v0.3 | `ps:case-match`（历史案例检索）、`ps:competitor-scan` | `case_index.py` |
| v1.0 | 完整售前闭环：`ps:intake` → `ps:discover` → `ps:ideate` → `ps:plan` → `ps:draft` → `ps:review` → `ps:price` → `ps:retrospect` | 完整知识库检索栈 |

## 9. 架构约束（硬规则）

1. **Skill 间零 import** — 耦合只通过文件系统
2. **禁止在 skill 内做文件系统体力活** — 统一走 `scripts/`
   - **v0.1 临时例外**：`ps:rfp-parse` Phase 0 允许通过 inline `mkdir -p` 创建 opportunity 子树（对应 ce:review 2026-04-15 的 Finding #9 修复）。v0.2 路标：引入 `scripts/ps_opportunity.py --create --slug` 把 mkdir 移出 skill。
3. **禁止把用户数据写到插件目录** — 只能写 `PRESALES_HOME`
4. **SKILL.md ≤ 300 行** — 精简原则，细节放 `references/`
5. **LLM 做决策，脚本做体力活** — 判断力不写脚本，确定性操作才写脚本
6. **每个标书段落必须追溯** — `[对标: <id>]` 标记，缺失 = 失败
7. **`rfp.yaml` 校验前置** — 下游 skill 必须校验 `rfp.yaml` 合规才执行
8. **文档只写接口契约** — 设计文档禁止写函数体 / if-else / 循环逻辑
