# 产品魔方 Schema — 三库 41 模块定义

本文件是产品入库的**单一真相源**。`product-extraction-prompt.md` 和 `facts.yaml` / `evidence.yaml` 模板均以此为准。

## Schema 版本

`schema_version: "1.0"` — 本期（v0.1）详细定义核心事实库 19 模块 + 证据库 13 模块，策略库 9 模块留骨架。

## 模块 ID 编号

| 范围 | 库 | 本期状态 |
|------|-----|---------|
| 1–19 | 核心事实库 | 详细定义 |
| 20–32 | 可信证据库 | 详细定义 |
| 33–41 | 竞争策略库 | 骨架（ID+名称） |

---

## 一、核心事实库（19 模块）

> 定位：产品认知基石，回答"我们是什么、能做什么、解决什么问题"

### （一）产品概述

#### M01 整体介绍

- **YAML key:** `overview.intro`
- **写作公式:** 一句话三要素法 — "产品本质 + 解决的核心问题 + 适用业务场景"
- **字段:**
  - `word_count`: int — 核心描述字数（≤100）
  - `tags.scene`: list — 适用场景（初次接触/技术验证/商务攻坚/竞争决胜/战略赋能）
  - `tags.role`: list — 目标角色
  - `tags.industry`: list — 目标行业
- **一票否决:** 未包含三要素 / 超过 100 字 / 使用技术黑话
- **提取可行性:** auto

#### M02 产品定位

- **YAML key:** `overview.positioning`
- **写作公式:** 精准定位三要素法 — "目标客群画像 + 差异化坐标 + 不适用场景说明"
- **字段:**
  - `target_segments`: list — 目标客群
  - `differentiation_axis`: str — 差异化轴
  - `has_not_applicable`: bool — 是否写明不适用场景
  - `tags`: dict
- **一票否决:** 未写明不适用场景 / 定位与实际能力不匹配
- **提取可行性:** auto

#### M03 应用现状

- **YAML key:** `overview.status`
- **写作公式:** 数据权威三要素法 — "已服务客户数 + 行业分布（前3）+ 标杆客户（脱敏）"
- **字段:**
  - `customer_count`: int|null
  - `industry_distribution`: dict|null
  - `benchmark_count`: int
  - `data_as_of`: str|null — 统计截止日期
  - `tags`: dict
- **一票否决:** 数据无时间标注 / 关键数据无来源
- **提取可行性:** hybrid（客户数常缺失）

#### M04 解决思路

- **YAML key:** `overview.approach`
- **写作公式:** 逻辑闭环三步法 — "核心方法论（≤3步）+ 客户可感知逻辑链 + 与传统方案对比优势"
- **字段:**
  - `methodology_steps`: int — 方法论步骤数
  - `has_vs_traditional`: bool — 是否有传统方案对比
  - `tags`: dict
- **一票否决:** 缺"问题→方法→结果"闭环 / 使用绝对化表述
- **提取可行性:** auto

#### M05 演进路线

- **YAML key:** `overview.roadmap`
- **写作公式:** 价值延续三要素法 — "近期规划（6个月）+ 中长期方向（1-3年）+ 客户价值延续点"
- **字段:**
  - `near_term`: str|null — 近期规划
  - `mid_term`: str|null — 中长期方向
  - `tags`: dict
- **一票否决:** 未区分"已发布"和"规划中" / 过度承诺
- **提取可行性:** manual（通常不在材料中）

### （二）产品功能

#### M06 安全防护类

- **YAML key:** `functions.security`
- **写作公式:** 防护三要素法 — "防护对象 + 防护能力 + 典型场景覆盖"
- **字段:** list of `{name, variant, version, ...}`
  - `name`: str — 功能名称
  - `variant`: list — 适用版本/形态
  - `version`: str|null — 起始版本
- **一票否决:** 版本标注不精准 / 功能描述模糊
- **提取可行性:** auto

#### M07 运维管理类

- **YAML key:** `functions.operations`
- **写作公式:** 效率提升三要素法 — "管理痛点 + 解决方案 + 量化效果"
- **字段:** list of `{name, variant, has_quantified_effect}`
- **一票否决:** 缺量化效果指标
- **提取可行性:** auto（量化效果常缺失 → hybrid）

#### M08 集成扩展类

- **YAML key:** `functions.integration`
- **写作公式:** 集成三要素法 — "集成对象 + 集成方式 + 价值收益"
- **字段:** list of `{name, variant, protocol, additional_cost}`
  - `protocol`: str|null — 接口协议
  - `additional_cost`: bool — 是否需额外成本
- **一票否决:** 接口类型不明确 / 隐瞒额外成本
- **提取可行性:** auto

### （三）应用价值

#### M09 风险防御类

- **YAML key:** `value.risk_defense`
- **写作公式:** 风险量化三要素法 — "风险类型 + 量化效果 + 验证方式"
- **字段:** list of `{type, coverage, verification, ...}`
- **一票否决:** 使用"100%防护"等绝对化表述 / 无验证方式
- **提取可行性:** auto

#### M10 合规治理类

- **YAML key:** `value.compliance`
- **写作公式:** 合规三要素法 — "法规/标准名称 + 产品能力匹配点 + 合规价值"
- **字段:** list of `{regulation, clause, match}`
  - `regulation`: str — 法规全称
  - `clause`: str|null — 条款号
  - `match`: str — 产品匹配点
- **一票否决:** 法规引用无文号 / 使用"确保合规"替代"助力合规"
- **提取可行性:** auto

#### M11 业务赋能类

- **YAML key:** `value.business_enablement`
- **写作公式:** 业务价值三要素法 — "业务痛点 + 安全赋能点 + 业务收益"
- **字段:**
  - `items`: int — 赋能项数量
- **一票否决:** 使用技术语言而非业务语言
- **提取可行性:** auto

#### M12 成本优化类

- **YAML key:** `value.cost_optimization`
- **写作公式:** 成本量化三要素法 — "成本类型 + 量化节约 + ROI计算"
- **字段:**
  - `has_roi`: bool — 是否有 ROI 数据
- **一票否决:** 成本数据无来源 / ROI 计算无前提条件
- **提取可行性:** manual（ROI 数据通常不在材料中）

### （四）关键能力

#### M13 核心技术能力

- **YAML key:** `capabilities.core_tech`
- **写作公式:** 技术通俗三要素法 — "技术名称 + 客户语言原理 + 客户可感知价值"
- **字段:** list of `{name, ...}` — 每项核心技术的关键指标自由扩展
- **一票否决:** 使用技术黑话 / 无验证证据关联
- **提取可行性:** auto

#### M14 差异化能力亮点

- **YAML key:** `capabilities.differentiators`
- **写作公式:** 差异化三要素法 — "差异化点 + 竞品对比优势 + 客户价值"
- **字段:** list of `{point, has_evidence, gap}`
- **一票否决:** 使用贬低性语言 / 差异化无证据支撑
- **提取可行性:** hybrid（竞品对比数据常缺失）

#### M15 能力验证路径

- **YAML key:** `capabilities.verification`
- **写作公式:** 验证三要素法 — "验证方式 + 验证步骤 + 证据锚点"
- **字段:** list of `{capability, method, has_template, has_benchmark}`
- **一票否决:** 验证步骤不具体 / 无证据关联
- **提取可行性:** hybrid

### （五）典型场景

> 典型场景按场景实例组织，每个场景含 M16–M19 四个子模块。YAML key 为 `scenarios[]`，每个场景元素含以下字段。

#### M16 场景定义与背景

- **写作公式:** 场景定义三要素法 — "场景名称（客户语言）+ 业务背景 + 技术环境特征"
- **字段（场景元素内）:**
  - `id`: str — 场景 ID（SCENE-NNN）
  - `name`: str — 场景名称
  - `variant`: str — 适用产品形态
  - `industries`: list — 适用行业
- **一票否决:** 场景名称使用技术术语
- **提取可行性:** auto

#### M17 客户痛点与挑战

- **写作公式:** 痛点共鸣三要素法 — "具体问题（≤3点）+ 业务影响（量化）+ 情绪痛点（客户原话）"
- **字段（facts.md 中描述）:** 嵌入场景段落
- **一票否决:** 痛点超过 3 个分散重点 / 无量化影响
- **提取可行性:** auto

#### M18 价值诉求与目标

- **写作公式:** 价值目标三要素法 — "核心诉求（≤3条）+ 成功标准（可衡量）+ 决策关键点"
- **字段（facts.md 中描述）:** 嵌入场景段落
- **一票否决:** 使用模糊表述替代可衡量标准
- **提取可行性:** hybrid

#### M19 适用客户画像

- **写作公式:** 画像筛选三要素法 — "行业特征 + 技术特征 + 触发信号（客户说什么时适用）"
- **字段（场景元素内）:**
  - `has_customer_quote`: bool — 是否有客户触发信号
- **一票否决:** 触发信号不具体
- **提取可行性:** auto

---

## 二、可信证据库（13 模块）

> 定位：信任加固引擎，用第三方报告、客户案例、行业荣誉回答"为什么可信"

### （六）权威背书

#### M20 市场研究报告

- **YAML key:** `authority.market_reports`
- **写作公式:** 权威三要素法 — "报告名称+机构 + 关键结论引用（含页码）+ 客户价值解读"
- **字段:** list of `{name, institution, year, conclusion, page_ref}`
- **一票否决:** 引用无页码 / 超 2 年未标注时效
- **提取可行性:** manual

#### M21 第三方测评

- **YAML key:** `authority.evaluations`
- **写作公式:** 测评三要素法 — "测评机构+项目 + 核心数据结论 + 测评时间"
- **字段:** list of `{name, institution, date, report_id, _q}`
- **一票否决:** 选择性展示结果 / 无报告编号
- **提取可行性:** hybrid（材料中可能提及但缺细节）

#### M22 合规与创新认证

- **YAML key:** `authority.certifications`
- **写作公式:** 认证四要素法 — "认证名称+颁发机构 + 证书编号+有效期 + 认证范围 + 创新点说明"
- **字段:** list of `{name, issuer, cert_no, valid_until, scope}`
- **一票否决:** 缺证书四要素（名称/编号/机构/有效期）
- **提取可行性:** hybrid

### （七）荣誉奖项

#### M23 国际奖项

- **YAML key:** `honors.international`
- **写作公式:** 国际荣誉三要素法 — "奖项名称+颁发机构 + 获奖年份 + 获奖理由 + 行业影响力"
- **字段:** list of `{name, institution, year, reason}`
- **一票否决:** 无获奖理由 / 无影响力说明
- **提取可行性:** manual

#### M24 国内奖项

- **YAML key:** `honors.domestic`
- **写作公式:** 国内荣誉三要素法 — "奖项名称+主办方 + 获奖年份 + 评选维度 + 行业地位"
- **字段:** list of `{name, organizer, year, dimension}`
- **一票否决:** 使用"最高奖""唯一"等夸大表述
- **提取可行性:** manual

#### M25 行业荣誉

- **YAML key:** `honors.industry`
- **写作公式:** 行业认可三要素法 — "荣誉名称+授予方 + 授予年份 + 授予原因 + 客户感知价值"
- **字段:** list of `{name, grantor, year, reason}`
- **一票否决:** 堆砌超过 5 个
- **提取可行性:** manual

### （八）成功案例

> 案例按实例组织，每个案例含 M26–M32 七个子模块。YAML key 为 `cases[]`。

#### M26 案例基础信息

- **写作公式:** 客户背景三要素法 — "客户行业+规模（脱敏）+ 合作时间 + 部署范围 + 客户标签"
- **字段（案例元素内）:**
  - `id`: str — 案例 ID（CASE-NNN）
  - `customer`: str — 脱敏客户名
  - `industry`: str
  - `variant`: str — 使用的产品形态
  - `scale`: str|null — 部署规模
  - `date`: str|null — 合作时间
- **一票否决:** 客户可被识别
- **提取可行性:** auto（脱敏信息通常在材料中）

#### M27 客户挑战与痛点

- **写作公式:** 痛点还原三要素法 — "业务背景 + 具体痛点描述 + 客户原话（脱敏）"
- **字段（evidence.md 中描述）:** 嵌入案例段落
- **一票否决:** 使用主观归因
- **提取可行性:** auto

#### M28 解决方案及亮点

- **写作公式:** 方案匹配三要素法 — "产品配置方案 + 关键能力应用 + 亮点量化"
- **字段（evidence.md 中描述）:** 嵌入案例段落
- **一票否决:** 技术堆砌而非痛点聚焦
- **提取可行性:** auto

#### M29 量化成果数据

- **写作公式:** 数据验证三要素法 — "关键指标改善（前后对比）+ 业务影响数据 + 客户认可表述"
- **字段（案例元素内）:**
  - `has_quantified_results`: bool
- **一票否决:** 孤例数据无统计周期
- **提取可行性:** manual（量化成果极少在材料中）

#### M30 客户证言

- **写作公式:** 证言三要素法 — "证言人角色+姓名（脱敏）+ 证言内容（≤50字）+ 授权状态"
- **字段（案例元素内）:**
  - `has_testimonial`: bool
- **一票否决:** 无客户授权书
- **提取可行性:** manual

#### M31 证据附件包

- **写作公式:** 证据四要素法 — "附件类型清单 + 脱敏说明 + 授权状态 + 获取方式"
- **字段（案例元素内）:**
  - `has_attachments`: bool
- **一票否决:** 附件含未脱敏敏感信息
- **提取可行性:** manual

#### M32 适用场景标签

- **写作公式:** 标签四要素法 — "行业标签 + 场景标签 + 角色标签 + 竞争标签"
- **字段（案例元素内）:**
  - `scene_tags`: list
- **一票否决:** 标签超过 5 个导致检索失效
- **提取可行性:** auto

---

## 三、竞争策略库（9 模块）— 骨架

> 定位：竞争制胜武器库。本期不做交互补全，仅预留 ID 和名称。

| ID | 模块 | 子模块 | YAML key（预留） |
|----|------|--------|------------------|
| M33 | 竞争优势 | 核心能力对比点 | `competition.core_comparison` |
| M34 | 竞争优势 | 服务支持对比点 | `competition.service_comparison` |
| M35 | 竞争优势 | 客户选择理由库 | `competition.selection_reasons` |
| M36 | 竞争优势 | 常见质疑应答库 | `competition.objection_handling` |
| M37 | 机会发现 | 客户驱动类 | `opportunities.customer_driven` |
| M38 | 机会发现 | 威胁驱动类 | `opportunities.threat_driven` |
| M39 | 机会发现 | 政策驱动类 | `opportunities.policy_driven` |
| M40 | 机会发现 | 竞争驱动类 | `opportunities.competition_driven` |
| M41 | 机会发现 | 机会行动指南 | `opportunities.action_playbook` |

---

## 提取可行性汇总

| 可行性 | 模块 ID | 说明 |
|--------|---------|------|
| **auto** | M01, M02, M04, M06, M08, M09, M10, M11, M13, M16, M17, M19, M26, M27, M28, M32 | 材料中通常可直接提取 |
| **hybrid** | M03, M07, M14, M15, M18, M21, M22 | 部分可提取，部分需人工补充 |
| **manual** | M05, M12, M20, M23, M24, M25, M29, M30, M31 | 通常不在材料中，需人工输入 |

## `_q` 质量元数据规范

每个模块的 YAML 表示中带 `_q` 字段：

```yaml
_q:
  confidence: high|medium|low|null   # 提取置信度
  source: "白皮书§3.1"               # 材料来源（章节级）
  gap: "缺客户数和行业分布"           # 缺口描述（无缺口时省略）
```

## 四级可用门槛

| 等级 | 核心事实库覆盖 | 证据库覆盖 | 策略库覆盖 | 说明 |
|------|--------------|-----------|-----------|------|
| 已录入 | < 60% | — | — | 批量提取后初始状态 |
| 可查 | ≥ 60% | — | — | bid-draft 可初步引用 |
| 可投 | ≥ 80% | ≥ 50% | — | 标书有说服力 |
| 可竞 | ≥ 80% | ≥ 50% | ≥ 50% | 能打竞品（本期不做） |

"达标"定义：字段非空 + `_q.confidence` 非 null。
