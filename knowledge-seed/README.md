# 知识库目录结构

`knowledge/` 是公司可复用资产的根。`ps:rfp-analyze` 和 `ps:bid-draft` 会引用此目录下的文件做 Go/No-Go 判断和标书内容生成。

## 子目录一览

| 目录 | 放什么 | 哪个 skill 引用 |
|------|--------|-----------------|
| `about/` | 公司介绍材料（PDF / PPT / Markdown） | `rfp-analyze`、`bid-draft` |
| `certs/` | 资质证书扫描件（ISO、CMMI、行业许可） | `rfp-analyze`（废标风险扫描） |
| `case-studies/` | 可复用的客户案例资料（区别于顶层 `cases/`） | `rfp-analyze`、`bid-draft` |
| `products/` | 产品 / 服务档案（YAML + 可选附件） | `rfp-analyze`、`bid-draft` |
| `competitors/` | 竞品档案（v0.2 功能，v0.1 占位） | `competitor-scan`（未来） |
| `team/` | 团队资质材料（简历、个人证书） | `rfp-analyze`（人员资质匹配） |

## 主档案

`company-profile.yaml` 是入口档案，用**相对路径**引用上面各子目录的文件，例如：

```yaml
qualifications:
  - id: QUAL-001
    name: ISO 9001
    valid_until: 2027-12-31
    evidence_file: certs/iso9001-SGS-2027.pdf   # 相对 knowledge/
```

这样迁移整个 `knowledge/` 目录时引用不会失效。

## 顶层 `cases/` vs `knowledge/case-studies/`

- `<presales>/cases/` — **归档目录**，存已跑完的 opportunity 整个目录（含原始 RFP、生成的标书、复盘）
- `<presales>/knowledge/case-studies/` — **可复用资料库**，存客户允许公开引用的案例材料（overview、授权见证信、公开演讲稿等）

## 填充时机

`ps:setup` 只建**空骨架**。填充不归 setup 管：

- **手工**：按每个子目录 README 的命名约定直接放文件
- **自动化**（未来）：`ps:knowledge-ingest` skill 会读标准格式的输入批量生成 YAML 条目 + 拷贝证据文件

v0.1 只支持手工填充。
