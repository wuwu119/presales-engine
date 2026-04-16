# 团队资质材料 (`知识库/团队/`)

核心团队资质证明。`ps:rfp-analyze` 做"人员资质匹配"时用，`ps:bid-draft` 生成"项目团队配置"章节时引用。

## 放什么

- **花名册**：`roster.yaml` — 汇总角色、人数、总资质数量
- **个人证书**：PMP、高项、CISP、CISSP、行业特定认证
- **个人简历**：核心人员简历 PDF
- **组织架构图**：团队层级结构

## 目录组织

```
团队/
├── roster.yaml                        # 汇总层（LLM 常规读，≤200 行）
├── cert-registry-cisp.yaml            # 明细分片：CISP 系列
├── cert-registry-pmp.yaml             # 明细分片：PMP
├── cert-registry-security.yaml        # 明细分片：CISSP/CISAW/CCSK/CISA 等
├── cert-registry-it-mgmt.yaml         # 明细分片：ITIL/ISO27001/PRINCE2 等
├── cert-registry-other.yaml           # 明细分片：其他类别
├── 杭州本地化服务团队.yaml              # 本地化团队花名册（可选）
├── certs/                              # 个人证书 PDF（可选）
│   └── zhang-san/pmp-2027-12-31.pdf
├── resumes/                            # 个人简历 PDF（可选，敏感）
└── org-chart.png                       # 组织架构图（可选）
```

## 两层数据结构

### 汇总层：`roster.yaml`（LLM 常规读）

```yaml
meta:
  data_source: "05 人员资质明细表.xlsx"
  last_updated: "2026-04-16"
  total_people: 764
  total_valid_certs: 1085

cert_summary_by_type:
  注册信息安全工程师（CISE）: 155
  项目管理专业人士资格（PMP）: 201
  注册信息系统安全专家（CISSP）: 45
  # ...

cert_summary_by_category:
  中国信息安全测评中心注册信息安全专业人员（CISP）: 279
  项目管理专业人士资格（PMP）: 201
  # ...
```

`rfp-analyze` 回答 "我们有几个 CISP" 只需读这层。

### 明细层：`cert-registry-{shard}.yaml`（LLM 按需读）

每个分片 ≤300 行，紧凑 pipe-delimited 格式：

```yaml
# cert-registry-cisp
# 格式: 姓名|工号|证书类型|证书编号|有效期至
certs:
  - "张三|A010250|注册信息安全工程师（CISE）|CNITSEC2019CISE0280|2027-06-30"
  - "李四|A001808|注册渗透测试工程师（CISP-PTE）|PTE-2023-456|2026-12-31"
```

`bid-draft` 需要列人员名单时读对应分片。

## 生成方式

```bash
python scripts/ps_knowledge_extract.py team \
  --xlsx "人员资质明细表.xlsx" \
  --output-dir ~/售前/知识库/团队/
```

## 在 company-profile.yaml 里的引用

```yaml
team:
  - role: 项目经理
    count: 5
    certifications: [PMP, PRINCE2, 高项]
    evidence_file: 知识库/团队/roster.yaml
```

## 谁引用它

- `ps:rfp-analyze` 废标风险扫描段：对照 RFP 的人员资质要求
- `ps:bid-draft` 项目团队配置章节：按 RFP 要求生成团队组织
