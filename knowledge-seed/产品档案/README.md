# 产品档案库 (`知识库/产品档案/`)

公司所有产品 / 服务的结构化档案。`ps:rfp-analyze` 用它做"评分杠杆"时匹配 RFP 需求，`ps:bid-draft` 用它生成"技术方案"章节。

## 放什么

每个产品 / 服务**一个 YAML 文件**（必须）+ 可选附件：

```
products/
├── firewall-pro.yaml            # 产品档案（必须）
├── firewall-pro/                # 附件目录（可选）
│   ├── datasheet.pdf            # 产品手册
│   ├── architecture.png         # 架构图
│   └── benchmarks.md            # 性能数据
├── siem-enterprise.yaml
└── ...
```

## YAML Schema

参考 `<售前>/模板/产品档案/example.yaml`（由 `ps:setup` 从插件拷贝过来）。最小字段集：

```yaml
meta:
  slug: firewall-pro
  name: 防火墙旗舰版
  category: 硬件
capabilities:
  - name: 吞吐量
    description: "20 Gbps 双向并发"
technical:
  architecture: 专用硬件
  deployment: [on-premise, hybrid]
delivery:
  timeline_days: 15
pricing:
  model: 一次性
references:
  - case_id: CASE-001   # 指向 知识库/客户案例/ 里的案例
```

## 命名约定

- YAML 文件名 = `<slug>.yaml`（小写、连字符分隔）
- slug 要和 YAML 内部 `meta.slug` 一致
- 附件目录名 = slug

## 种子模板

`ps:setup` 会把 `模板/产品档案/example.yaml` 拷到 `<售前>/模板/产品档案/example.yaml` 作为 schema 参考。新增产品时：

1. `cp ~/售前/模板/产品档案/example.yaml ~/售前/知识库/产品档案/<your-slug>.yaml`
2. 编辑填充真实数据
3. 可选：建 `~/售前/知识库/产品档案/<your-slug>/` 放附件

## 谁引用它

- `ps:rfp-analyze` 对照 RFP 需求逐条匹配产品能力
- `ps:bid-draft` 生成"技术方案"章节时按权重选产品组合
- 未来 `ps:knowledge-ingest` 会从产品手册 PDF 自动抽取字段生成 YAML 草稿
