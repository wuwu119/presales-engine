---
name: ps:bid-draft
description: 基于 rfp.yaml、analysis.md 和公司档案，分章节生成标书草稿。每个段落必须追溯到 RFP 评分项或需求条目，防止自嗨式方案。当用户说"生成标书"、"bid draft"、"写方案初稿"、"起草标书"时触发。
argument-hint: "<opportunity-slug> [--chapter <name>] [--outline-only]"
---

# ps:bid-draft — 标书草稿生成

## 前置条件（硬性）

| 前置 | 校验 |
|------|------|
| `rfp.yaml` 存在且校验通过 | ✅ 必需 |
| `analysis.md` 存在 | ✅ 必需 |
| `analysis.md` 决策 ∈ {Go, Conditional-Go} | ✅ 必需，No-Go 拒绝执行 |
| `company-profile.yaml` 存在 | ✅ 必需 |

前置不满足：拒绝执行，指引先跑前置 skill。

## 输入

- `商机/{slug}/分析/rfp.yaml`
- `商机/{slug}/分析/analysis.md`
- `${PRESALES_HOME}/知识库/company-profile.yaml`
- `${PRESALES_HOME}/知识库/产品档案/*/facts.yaml`（结构化参数）
- `${PRESALES_HOME}/知识库/产品档案/*/facts.md`（段落引用）
- 模板（用户优先）：
  - `${PRESALES_HOME}/模板/outline-{language}.yaml` — 章节大纲
  - `${PRESALES_HOME}/模板/chapters/*.md` — 章节正文片段（可无）
  - 回退：`${CLAUDE_PLUGIN_ROOT}/模板/...`

## 输出

- `商机/{slug}/草稿/outline.md` — 章节大纲（含评分项映射）
- `商机/{slug}/草稿/章节/{NN-name}.md` — 每章一个文件

## 行为流程

### Phase 1: 生成大纲（`--outline-only` 模式止步于此）

1. 读取 `模板/outline-{language}.yaml`（默认跟随 `rfp.yaml.meta.language`）
2. 把 `rfp.yaml.scoring` 逐项映射到章节（一个章节可覆盖多个评分项）
3. 按权重**重排**章节顺序（高权重章节更靠前 + 篇幅预算更大）
4. 废标项（`disqualifications`）必须在"资质声明"章节逐条直接应答
5. 输出 `outline.md`，含：
   - 章节编号和标题
   - 每章对应的评分项 id（`[对标: SCORING-01, SCORING-03]`）
   - 每章的预估篇幅（字数或段落数）
   - 每章的关键卖点

6. **大纲确认前不写正文**（除非用户明确跳过）

### Phase 2: 分章节生成

对每个章节按顺序：

1. 读取该章节应覆盖的评分项和需求条目
2. 读取模板片段（若 `模板/chapters/{name}.md` 存在）
3. 结合 `company-profile` 和 `产品档案/*/facts.yaml` + `facts.md` 生成正文
4. **每段末尾必须追加追溯标记**：`> [对标: SCORING-<id> / REQ-<id> / DISQ-<id>]`
5. 写入 `草稿/章节/{NN-name}.md`

追溯标记是**强约束**，没有标记的段落在 v0.2 `/ps:bid-review` 会被拒。

### Phase 3: 覆盖率校验

**v0.1（当前行为）**：由 LLM 自检，**不写文件**，**不强制中止**。

生成完所有章节后，LLM 必须：
1. 扫描自己刚写出的 `草稿/章节/*.md` 提取所有 `[对标: ...]` 追溯标记
2. 对照 `rfp.yaml.scoring` 和 `rfp.yaml.requirements`
3. 在最终对话消息中明确列出（不写到文件）：
   - ✅ 已覆盖项
   - ❌ 未覆盖项（按权重降序）
   - ⚠️ 论述单薄项（段落 < 3 段 / 字数 < 200）

如果覆盖率 < 100%，**警告**用户但不中止 — 由用户决定是否接受。

**v0.2 路标**：引入 `scripts/bid_coverage.py` 作为机械裁判，届时：
- 自动写入 `草稿/coverage-report.md`
- 覆盖率 < 80% 强制中止（不允许用户拍板）
- 覆盖率 80%–99% 必须用户确认后写入 `meta.yaml.acknowledged_gaps`

> ⚠️ v0.1 **不写** `草稿/coverage-report.md`，**不强制**任何覆盖率门槛。下游 agent 不应假设此文件存在。

## 约束（强制）

- **禁止自嗨式方案** — 不能写 RFP 没要求的"亮点"功能，除非 `analysis.md` 标记为"差异化杠杆"
- **禁止虚假案例** — 引用的客户案例必须在 `company-profile.case_references` 或 `知识库/归档/` 中存在
- **禁止数字魔法** — 不编造业绩数据、用户量、性能指标
- **语言一致** — 使用 `rfp.yaml.meta.language`，不要混用
- **术语镜像** — 关键术语使用 RFP 原文用词（例如 RFP 用"招标人"就不要写"甲方"），**不要**"翻译"成产品手册术语
- **禁止产品吹嘘** — `产品档案/*/facts.yaml` 中没写的能力不要在标书中"加戏"

## 单章重生成

`--chapter <name>` 只重新生成指定章节，不动其他章节。用于局部迭代。

## 失败处理

| 情况 | 处理 |
|------|------|
| 前置文件缺失 | 报错 + 指引先跑前置 skill |
| `analysis.md` 决策 = No-Go | 拒绝执行 + 提示改决策或放弃 |
| 模板不存在 | 从零生成 + 提示用户"此章节无模板，建议首次生成后沉淀为模板" |
| 覆盖率 < 100% (v0.1) | LLM 在对话中警告 + 列出未覆盖项，**不中止**（v0.2 引入硬门槛） |
| 用户跳过大纲确认 | 允许，但生成后强警告：未经大纲确认可能偏离需求 |

## 后续步骤提示

```
✅ 草稿生成完成
   章节数：{N}
   总字数：{M}
   评分项覆盖率：{X}%
   位置：{slug}/草稿/章节/

下一步：
1. 人工审阅 + 客户反馈迭代
2. 若需要重写某章：/ps:bid-draft {slug} --chapter <name>
3. v0.2 将提供 /ps:bid-review 自动审阅
```
