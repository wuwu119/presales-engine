---
name: ps:rfp-parse
description: 把招标文件（PDF/Word/Markdown）结构化解析为 rfp.yaml，抽取评分项、废标项、需求清单、时间节点和资质要求。输入 opportunity slug，自动扫描 rfp/original/ 下的文件。当用户说"解析招标文件"、"rfp parse"、"解析这份 RFP"、"提取招标要求"时触发。
argument-hint: "<opportunity-slug> [--force]"
---

# ps:rfp-parse — 招标文件结构化解析

## 前置条件

- `ps:setup` 已执行，`${PRESALES_HOME}` 存在
- `${PRESALES_HOME}/opportunities/{slug}/rfp/original/` 下至少有一个文件

## 输入

`${PRESALES_HOME}/opportunities/{slug}/rfp/original/` 下的一个或多个文件：
- `.pdf`（原生或扫描件）
- `.docx` / `.doc`
- `.md` / `.txt`（已手工转换的）

## 输出

| 文件 | 用途 |
|------|------|
| `{slug}/rfp/extracted.md` | 文本提取结果（人读用） |
| `{slug}/analysis/rfp.yaml` | 结构化解析结果，schema 见 `docs/design/architecture-v0.1.md` §5 |
| `{slug}/meta.yaml` | 基本信息（若不存在则创建） |

## 行为流程

### Phase 1: 文本提取

优先用 Claude Code 原生 `Read` 工具读取所有 `rfp/original/*`：

- 对 PDF：Read 工具支持 PDF 原生读取，最多 20 页 / 次
- 对 DOCX：若 Read 不支持，提示用户手工转 `.md` 并放回 `rfp/original/`
- 对扫描件 PDF：Read 会返回图像，此时调用 OCR 能力（若无，报错提示）

将所有文本合并写入 `{slug}/rfp/extracted.md`，按原文件名分 section，保留章节标题和页码。

### Phase 2: 结构化解析（纯 LLM 决策）

读取 `extracted.md`，按 `rfp.yaml` schema 抽取：

1. **meta** — 客户名、项目名、发布/截止日期、语言、货币
2. **qualifications** — 硬性资质（营业执照、财务指标、案例证明、人员认证等）
3. **scoring** — 评分项，**权重总和必须等于 100（允许 ±1% 舍入）**
4. **disqualifications** — 废标项，逐条引用 RFP 章节号
5. **requirements** — 功能/技术需求，按 must / should / may 分级
6. **timeline** — 关键日期
7. **parsing_meta.ambiguities** — 所有解析歧义点

### Phase 3: 写入 + 校验

1. 先写 `extracted.md`（文本提取结果）
2. 写 `rfp.yaml`（结构化结果）
3. 若 `meta.yaml` 不存在则创建，填充客户名、项目名、截止日期
4. 内嵌校验：
   - `scoring[].weight` 总和 ∈ [99, 101]
   - `deadline > issued_date`
   - 所有 `id` 在同类列表唯一
   - 必填字段齐全
5. 校验失败的字段追加到 `parsing_meta.ambiguities`，不阻断保存，但警告用户

## 约束（强制）

- **禁止编造内容** — 评分权重、废标项、时间节点必须源自 RFP 原文
- **找不到就标 null + 记入 ambiguities** — 不要猜测
- **必须保留原文引用** — 每个评分项和废标项必须记录 `source_section`（章节/页码）
- **多文件合并** — 若 `original/` 下有多个文件，按文件名字母序拼接，用 `---\n# <filename>\n---` 分隔
- **语言自动识别** — 根据 RFP 主要语言设置 `meta.language`，不强制英文

## `--force` 行为

- 不带 `--force` 且 `rfp.yaml` 已存在：询问用户是否覆盖
- 带 `--force`：直接覆盖（不备份）

## 失败处理

| 情况 | 处理 |
|------|------|
| `{slug}` 目录不存在 | 报错 + 提示先创建 `opportunities/{slug}/rfp/original/` |
| `original/` 为空 | 报错 + 提示放置文件 |
| 无法提取 PDF（加密） | 报错 + 建议手工解密后重跑 |
| 扫描件 PDF 无 OCR | 报错 + 建议手工转 Markdown |
| 解析歧义项 > 5 条 | 完成解析，但强烈建议人工复核 |

## 后续步骤提示

成功后必须输出：

> ✅ 解析完成
> - 评分项：{N} 条（权重总和：{W}%）
> - 废标项：{M} 条
> - 需求：{K} 条（must: {X} / should: {Y} / may: {Z}）
> - 资质要求：{Q} 条
> - ⚠️ 歧义待确认：{A} 处（见 `rfp.yaml` 的 `parsing_meta.ambiguities`）
>
> 下一步：运行 `/ps:rfp-analyze {slug}` 进行战略分析
