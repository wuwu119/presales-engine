# 产品材料 → 产品魔方结构化提取参考

本文件由 `skills/knowledge-ingest/SKILL.md` Phase 2 引用。Claude 用 Read 读取产品材料文件后，按本文档约定输出结构化 JSON。

完整模块定义见 `product-cube-schema.md`。

## 提取策略

1. **逐文件读取** — 用 Read 工具依次读取材料目录下的所有支持格式文件
2. **累积提取** — 不同文件可能覆盖不同模块，后读文件补充前面的空白，不覆盖已有高置信度内容
3. **双轨输出** — 同时产出 facts（核心事实库）和 evidence（可信证据库）两组 JSON
4. **质量自评** — 每个模块标注 `_q`（confidence + source + gap）

## 核心事实库提取（19 模块 → facts JSON）

### 提取指令

你将收到一个产品的全部材料文本。请按以下 19 个模块逐一提取信息，输出嵌套 JSON。

对每个模块：
- 如果材料中有对应信息 → 提取并标注 `_q.confidence` 和 `_q.source`
- 如果材料中无对应信息 → 该模块值设为模板默认值，`_q.confidence: null`，`_q.gap` 说明缺什么、找谁补
- **禁止猜测** — 材料中未出现的信息不能编造

### 输出 JSON Schema

```json
{
  "meta": {
    "slug": "产品slug",
    "name": "产品中文名",
    "name_en": "英文名或null",
    "vendor": "厂商名",
    "category": "SaaS|本地部署|硬件|服务|SDK|咨询",
    "status": "active",
    "version": "版本号或空",
    "schema_version": "1.0"
  },

  "overview": {
    "intro": {
      "word_count": 85,
      "tags": {"scene": ["初次接触"], "role": ["CIO"], "industry": ["金融"]},
      "_q": {"confidence": "high", "source": "白皮书§1.1"}
    },
    "positioning": {
      "target_segments": ["中大型企业"],
      "differentiation_axis": "差异化描述",
      "has_not_applicable": true,
      "tags": {},
      "_q": {"confidence": "high", "source": "白皮书§2"}
    },
    "status": {
      "customer_count": 328,
      "industry_distribution": {"金融": "45%", "政务": "30%"},
      "benchmark_count": 6,
      "data_as_of": "2024Q2",
      "tags": {},
      "_q": {"confidence": "medium", "source": "白皮书§8", "gap": "缺行业分布"}
    },
    "approach": {
      "methodology_steps": 3,
      "has_vs_traditional": true,
      "tags": {},
      "_q": {"confidence": "high", "source": "白皮书§3"}
    },
    "roadmap": {
      "near_term": null,
      "mid_term": null,
      "tags": {},
      "_q": {"confidence": null, "gap": "完全缺失，需产品经理输入"}
    }
  },

  "functions": {
    "security": [
      {"name": "功能名", "variant": ["版本A"], "version": "V1.0+"}
    ],
    "operations": [
      {"name": "功能名", "variant": [], "has_quantified_effect": false}
    ],
    "integration": [
      {"name": "接口名", "variant": [], "protocol": "REST", "additional_cost": false}
    ]
  },

  "value": {
    "risk_defense": [
      {"type": "风险类型", "coverage": "覆盖范围", "verification": "验证方式"}
    ],
    "compliance": [
      {"regulation": "法规全称", "clause": "条款号", "match": "产品匹配点"}
    ],
    "business_enablement": {
      "items": 2,
      "_q": {"confidence": "high"}
    },
    "cost_optimization": {
      "has_roi": false,
      "_q": {"confidence": null, "gap": "需产品/销售提供成本对比"}
    }
  },

  "capabilities": {
    "core_tech": [
      {"name": "技术名称"}
    ],
    "differentiators": [
      {"point": "亮点描述", "has_evidence": false, "gap": "缺竞品对比数据"}
    ],
    "verification": [
      {"capability": "能力名", "method": "POC", "has_template": true, "has_benchmark": false}
    ]
  },

  "scenarios": [
    {
      "id": "SCENE-001",
      "name": "场景名称（客户语言）",
      "variant": "产品形态",
      "industries": ["行业"],
      "has_customer_quote": false
    }
  ],

  "specs": {},

  "sources": [
    {"file": "文件名.pdf", "type": "whitepaper"}
  ]
}
```

### 各模块写作公式（提取时对照）

| 模块 | 写作公式 | 提取要点 |
|------|---------|---------|
| M01 整体介绍 | 产品本质 + 核心问题 + 适用场景 | ≤100字，禁技术黑话 |
| M02 产品定位 | 目标客群 + 差异化坐标 + 不适用场景 | 必须有不适用场景 |
| M03 应用现状 | 客户数 + 行业分布 + 标杆客户 | 标注数据截止时间 |
| M04 解决思路 | 方法论≤3步 + 逻辑链 + vs传统 | 必须有对比 |
| M05 演进路线 | 近期 + 中长期 + 客户价值 | 通常缺失 |
| M06 安全防护 | 防护对象 + 能力 + 场景 | 标注版本 |
| M07 运维管理 | 痛点 + 方案 + 量化效果 | 量化效果常缺 |
| M08 集成扩展 | 对象 + 方式 + 收益 | 标注额外成本 |
| M09 风险防御 | 风险类型 + 量化效果 + 验证 | 禁用绝对化 |
| M10 合规治理 | 法规名称+文号 + 匹配点 + 价值 | 法规要精准 |
| M11 业务赋能 | 业务痛点 + 赋能点 + 收益 | 用业务语言 |
| M12 成本优化 | 成本类型 + 量化 + ROI | 通常缺失 |
| M13 核心技术 | 技术名 + 通俗原理 + 价值 | 禁技术黑话 |
| M14 差异化亮点 | 亮点 + 竞品对比 + 价值 | 对比数据常缺 |
| M15 验证路径 | 方式 + 步骤 + 证据 | 步骤要具体 |
| M16-19 典型场景 | 背景+痛点+诉求+画像 | 触发信号要具体 |

## 可信证据库提取（13 模块 → evidence JSON）

### 输出 JSON Schema

```json
{
  "meta": {
    "slug": "产品slug",
    "schema_version": "1.0"
  },

  "authority": {
    "market_reports": [],
    "evaluations": [
      {"name": "VB100", "institution": "Virus Bulletin", "date": null, "report_id": null, "_q": {"gap": "缺年份和得分"}}
    ],
    "certifications": []
  },

  "honors": {
    "international": [],
    "domestic": [],
    "industry": []
  },

  "cases": [
    {
      "id": "CASE-001",
      "customer": "某XX企业",
      "industry": "互联网",
      "variant": "middleware",
      "scale": null,
      "date": null,
      "has_quantified_results": false,
      "has_testimonial": false,
      "has_attachments": false,
      "scene_tags": ["标签1", "标签2"]
    }
  ]
}
```

### 证据库提取规则

| 模块 | 提取要点 | 缺失标记 |
|------|---------|---------|
| M20 市场报告 | 需含机构+页码，通常材料中没有 | `[]` + evidence.md 标 ❌ |
| M21 第三方测评 | 材料中可能提及但缺细节 | 提取提及，gap 标缺什么 |
| M22 合规认证 | 产品级认证，非公司级 | 区分公司资质 vs 产品认证 |
| M23-25 荣誉奖项 | 通常不在产品材料中 | `[]` + ❌ |
| M26 案例基础信息 | 从白皮书/案例文档提取 | 脱敏客户名 |
| M27 客户挑战 | 案例中的痛点描述 | 自动提取 |
| M28 解决方案 | 案例中的方案描述 | 自动提取 |
| M29 量化成果 | 极少在材料中 | `has_quantified_results: false` + ❌ |
| M30 客户证言 | 需客户授权，材料中无 | `has_testimonial: false` + ❌ |
| M31 证据附件 | 需整理脱敏 | `has_attachments: false` + ❌ |
| M32 场景标签 | 从案例内容推导 | 自动提取 |

## facts.md 生成规则

基于 facts JSON 生成 Markdown，结构对应 `product-cube-schema.md` 的模块编号：

- 每个模块一个三级标题（`### N. 模块名`）
- 有内容的模块：直接写叙述性段落（bid-draft 引用的段落）
- 缺失模块：用 `> ❌ {缺失原因}。{找谁补、从哪获取}` 格式标注
- 部分缺失：写已有部分，缺失字段用 `> ⚠️ 缺{字段名}` 标注

## evidence.md 生成规则

同 facts.md 规则，但模块编号从 20 开始。案例部分按 CASE-NNN 编号组织，每个案例含完整七子模块描述。

## 置信度评估规则

| 场景 | confidence |
|------|-----------|
| 原文直接抄录（如产品名、参数） | high |
| 从上下文合理推断（如从功能描述推行业） | medium |
| 材料中未提及，无法提取 | null（不是 low） |
| 材料提及但信息不完整 | medium + gap 说明缺什么 |

**`low` 仅用于**：材料中有相关描述但存在矛盾或表述模糊，提取结果可能不准确。

## 禁止项

- **禁止猜测** — 材料中未提及的信息设为 null/空 + `_q.confidence: null`
- **禁止翻译** — 保留原文语言，中文就中文，英文就英文
- **禁止合并产品** — 一次提取只处理一个产品
- **禁止编造案例** — 案例必须来自材料原文
- **禁止添加竞品分析** — 策略库不在本期提取范围
