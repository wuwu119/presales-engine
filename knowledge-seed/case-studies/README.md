# 客户案例资料库 (`knowledge/case-studies/`)

**可复用**的客户成功案例材料。

## 与顶层 `cases/` 的区别

- `<presales>/cases/` = **归档目录**，存已跑完的 opportunity 整个目录（原始 RFP + 生成的标书 + 复盘结论）
- `<presales>/knowledge/case-studies/` = **可复用资料库**，存已得到客户授权、可在新标书里公开引用的案例材料

打个比方：`cases/` 是"病历档案"，`case-studies/` 是"可以写进论文的精选病例"。

## 放什么

- 客户案例 PPT / PDF（官方版本）
- 项目总结文档
- 客户授权的见证信 / 合作声明
- 获奖证书、媒体报道
- 可脱敏后展示的合同片段

⚠️ **重要**：放在这里的材料默认**可被 bid-draft 直接引用到标书**。放之前确认客户已授权或内容已脱敏。

## 目录组织（推荐）

按客户 slug 建子目录：

```
case-studies/
├── acme-bank/
│   ├── overview.md              # 案例概述（最常引用）
│   ├── case-2024-core-system.pdf  # 正式案例材料
│   ├── testimonial.pdf          # 客户授权见证信
│   └── press-release.pdf        # 公开媒体报道
├── xyz-insurance/
│   └── ...
```

每个客户目录至少有一个 `overview.md`，包含：
- 客户名（脱敏情况说明）
- 年份
- 项目规模（金额 / 时长 / 人月）
- 行业
- 应用场景
- 交付成果
- 可引用的核心数字（3-5 个）

## 格式

- `overview.md` 必须是 Markdown
- 原始材料用 PDF / DOCX / PPTX

## 在 company-profile.yaml 里的引用

```yaml
case_references:
  - id: CASE-001
    customer: XX 银行（脱敏："某股份制银行"）
    industry: 金融
    year: 2024
    scale: "5000 万"
    summary: "为 XX 银行建设核心系统..."
    evidence_file: case-studies/acme-bank/overview.md
    public_usable: true
```

`public_usable: true` 表示可在公开标书引用；脱敏说明见 `overview.md`。

## 谁引用它

- `ps:rfp-analyze` **评分杠杆分析**段：对照 RFP "类似项目经验"要求
- `ps:bid-draft` **类似项目案例**章节：按行业相关性 + 权重选 3-5 个
- 未来 `ps:case-match` skill（v0.3）会做自动案例检索
