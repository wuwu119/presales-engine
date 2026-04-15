# 竞品档案 (`知识库/竞品/`)

> ⚠️ **v0.2 功能占位**。v0.1 的 `ps:setup` 只建此目录，不使用它。`ps:rfp-analyze` 目前做的"竞品格局推断"是定性分析，不读此目录。

## 未来用途（v0.2+）

存放主要竞品的情报档案，供 `ps:rfp-analyze` 做定量竞品分析和 `ps:bid-draft` 做差异化卖点构造时引用。

## 未来目录组织（预告）

```
competitors/
├── competitor-a.yaml     # 竞品档案
├── competitor-a/         # 附件：公开案例、定价页截图
├── competitor-b.yaml
└── ...
```

## 未来 YAML Schema 草稿

```yaml
meta:
  slug: competitor-a
  name: 竞品 A 公司全称
  category: 直接竞争 / 间接竞争 / 替代品
pricing:
  model: 订阅 / 一次性 / 混合
  approx_range: "xxx 万 / 年"
strengths:
  - "..."
weaknesses:
  - "..."
typical_customers: []
product_overlap: []
```

## 谁会引用它（未来）

- `ps:rfp-analyze` 竞品格局推断段：定量分析
- `ps:bid-draft` 差异化卖点构造
- `ps:competitor-scan` skill（v0.3 计划）

## v0.1 建议

现在不用填。先专注跑通第一个真实 RFP 流程。竞品信息可以先手写在 `rfp-analyze` 的输出里作为定性判断。
