# 团队资质材料 (`knowledge/team/`)

核心团队资质证明。`ps:rfp-analyze` 做"人员资质匹配"时用，`ps:bid-draft` 生成"项目团队配置"章节时引用。

## 放什么

- **花名册**：`roster.yaml` — 汇总角色、人数、总资质数量
- **个人证书**：PMP、高项、CISP、CISSP、行业特定认证
- **个人简历**：核心人员简历 PDF
- **组织架构图**：团队层级结构

## 目录组织（推荐）

```
team/
├── roster.yaml                  # 团队汇总（必须）
├── certs/                       # 个人证书
│   ├── zhang-san/
│   │   ├── pmp-2023-12-31.pdf
│   │   └── 高项-2025-06-30.pdf
│   └── li-si/
│       └── cissp-2027-09-15.pdf
├── resumes/                     # 个人简历（可选，敏感）
│   ├── zhang-san.pdf
│   └── li-si.pdf
└── org-chart.png                # 组织架构图
```

## `roster.yaml` Schema

```yaml
roles:
  - role: 项目经理
    count: 5
    certifications_summary:
      PMP: 3
      PRINCE2: 2
      高项: 4
  - role: 高级架构师
    count: 8
    certifications_summary:
      阿里云 ACP: 5
      AWS SA-Pro: 3
      CISSP: 2

key_members:
  - name: 张三（可脱敏）
    role: 技术总监
    years_of_experience: 15
    certs: [PMP, CISSP, 高项]
    cert_files: [certs/zhang-san/pmp-2023-12-31.pdf, ...]
    resume_file: resumes/zhang-san.pdf
```

## 命名约定（个人证书）

`<证书名>-<有效期到>.pdf`，例如：

- `pmp-2023-12-31.pdf`
- `cissp-2027-09-15.pdf`
- `高项-2025-06-30.pdf`

## 格式

- `roster.yaml` 必须是 YAML
- 证书 / 简历用 PDF

## 在 company-profile.yaml 里的引用

```yaml
team:
  - role: 项目经理
    count: 5
    certifications: [PMP, PRINCE2, 高项]
    evidence_file: team/roster.yaml
```

## 谁引用它

- `ps:rfp-analyze` 废标风险扫描段：对照 RFP 的人员资质要求
- `ps:bid-draft` 项目团队配置章节：按 RFP 要求生成团队组织
