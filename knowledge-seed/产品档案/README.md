# 产品档案库 (`知识库/产品档案/`)

公司所有产品 / 服务的结构化档案，按产品魔方三库体系组织。`ps:rfp-analyze` 用它匹配 RFP 需求，`ps:bid-draft` 用它生成"技术方案"章节。

## 目录结构

每个产品一个**子目录**（必须），含 YAML（结构化索引）+ MD（段落级内容）双文件：

```
产品档案/
├── README.md                       # 本文件
├── firewall-pro/                   # 产品子目录（slug = firewall-pro）
│   ├── facts.yaml                  # 核心事实库索引（19 模块）
│   ├── facts.md                    # 核心事实库叙述
│   ├── evidence.yaml               # 可信证据库索引（13 模块）
│   └── evidence.md                 # 可信证据库叙述
├── siem-enterprise/
│   ├── facts.yaml
│   ├── facts.md
│   ├── evidence.yaml
│   └── evidence.md
└── ...
```

## 产品发现契约

**子目录 + `facts.yaml` 存在 = 一个有效产品。** knowledge-doctor、bid-draft、rfp-analyze 均按此契约发现产品。

## Schema

参考 `<售前>/模板/产品档案/example/`（由 `ps:setup` 从插件拷贝过来）。完整 schema 定义见插件的 `skills/knowledge-ingest/references/product-cube-schema.md`。

### 最小可用产品（"可查"级别）

核心事实库 19 模块中 ≥ 60% 子模块达标：

```yaml
# facts.yaml 关键字段
meta:
  slug: firewall-pro
  name: 防火墙旗舰版
  category: 硬件
overview:
  intro:
    word_count: 85
    _q: { confidence: high, source: "白皮书§1" }
  positioning:
    target_segments: [政府, 金融]
    _q: { confidence: high }
functions:
  security:
    - { name: 入侵防御, variant: [硬件] }
```

## 命名约定

- 子目录名 = `<slug>`（小写、连字符分隔）
- slug 要和 `facts.yaml` 内部 `meta.slug` 一致
- 附件放在子目录内（可选）

## 入库方式

运行 `/ps:knowledge-ingest products --source <材料目录>` 自动提取，或手动复制模板后编辑。

## 谁引用它

- `ps:rfp-analyze` 读 `产品档案/*/facts.yaml` 做产品-需求匹配
- `ps:bid-draft` 读 `产品档案/*/facts.yaml`（结构化参数）+ `产品档案/*/facts.md`（段落引用）
- `ps:knowledge-doctor` 扫描子目录统计产品完整度和可用等级

## 四级可用

| 等级 | 条件 | 用途 |
|------|------|------|
| 已录入 | facts.yaml 存在，核心事实 < 60% 达标 | 仅占位 |
| 可查 | 核心事实 ≥ 60% | bid-draft 可初步引用 |
| 可投 | 核心事实 ≥ 80% + 证据 ≥ 50% | 标书有说服力 |
| 可竞 | 可投 + 策略 ≥ 50% | 能打竞品（未来） |
