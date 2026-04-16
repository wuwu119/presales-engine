# 竞品档案 (`知识库/竞品/`)

每家竞品一个 YAML 文件，存放公司级资质对比数据。`ps:rfp-analyze` 做定量竞品分析，`ps:bid-draft` 做差异化卖点构造时引用。

## 目录组织

```
竞品/
├── sangfor.yaml          # 深信服
├── nsfocus.yaml          # 绿盟科技
├── venustech.yaml        # 启明星辰
├── topsec.yaml           # 天融信
└── ...                   # 每家一个文件，加友商 = 加文件
```

## YAML Schema

```yaml
company: 深信服科技股份有限公司
slug: sangfor
source: "06 资质分析沙盘（公司级）V5.0.xlsx"
last_updated: 2026-04-16
qualification_count: 45

qualifications:
  - category: 安全服务类
    name: 国测信息安全服务资质-安全工程类
    level: 二级
  - category: 体系认证
    name: ISO 27001
    level: 有效
```

## slug 命名约定

- 公司名 → 英文简称或拼音：深信服→sangfor、绿盟→nsfocus、天融信→topsec
- 完整映射见 `scripts/ps_knowledge_extract.py` 的 `COMPETITOR_SLUG_MAP`
- 不在映射表中的公司自动 sanitize（中文→拼音/连字符）

## 生成方式

```bash
python scripts/ps_knowledge_extract.py competitors \
  --xlsx "资质分析沙盘（公司级）.xlsx" \
  --output-dir ~/售前/知识库/竞品/
```

## 使用场景

1. `rfp-analyze`："RFP 要求安全工程类三级，竞品有没有？"
   → 读 `company-profile.yaml`（我方三级）+ `竞品/sangfor.yaml`（深信服二级）→ 我方有优势
2. `bid-draft`："差异化卖点"
   → 对比我方 vs 竞品资质等级差，自动构造差异化描述

## 谁引用

- `ps:rfp-analyze` 竞品格局推断段
- `ps:bid-draft` 差异化卖点构造
- `ps:competitor-scan`（v0.3 计划，自动刷新数据）
