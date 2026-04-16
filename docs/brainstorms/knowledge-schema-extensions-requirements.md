# 知识库 Schema 扩展需求文档

**日期**：2026-04-16
**版本**：v0.2 补充
**状态**：设计已拍板，待实现
**上游**：`docs/brainstorms/knowledge-ingest-requirements.md`、本次 DOCX 抽取实践

## 1. 目标

扩展知识库 schema 以容纳三类新数据源：人员资质明细、公司级竞品对比、产品级证书。这三类数据由真实投标参考材料（Excel）驱动发现，是 `rfp-analyze` / `bid-draft` 做出高质量判断的关键输入。

## 2. 问题与动机

v0.2 certs MVP 已让 `company-profile.yaml.qualifications[]` 有了 29 条公司级资质。但实际投标中还需要回答：
- "我们有几个 CISP？RFP 要求 5 个够不够？" → 需要**人员证书**数据
- "竞品有没有同级资质？我们的差异化在哪？" → 需要**竞品对比**数据
- "这个产品有什么认证可以写进方案？" → 需要**产品证书**数据

现有 schema 只有目录占位，没有结构定义。三份 Excel 原始文件放着没法用。

## 3. 数据消费方式

**统一决策**：LLM 直读 YAML，不引入脚本查询层。
- 每个 YAML 文件控制在 ≤1000 行
- 超过上限的用**汇总 + 明细两层**拆分
- rfp-analyze / bid-draft 通过 Read 工具直接读取

## 4. 三类扩展设计

### 4.1 人员资质（来源：`05 人员资质明细表.xlsx`）

**数据规模**：1086 条有效 + 1404 条过期

**结构：汇总 + 明细两层**

**汇总层**（LLM 常规读）：`知识库/团队/roster.yaml`
- 扩展现有 roster.yaml schema，新增 `cert_summary` 段
- 按证书类型聚合人数：`{CISP-CISE: 45, PMP: 8, 高项: 6, ...}`
- 包含 `total_people`、`total_valid_certs`、`data_source`、`last_updated`
- 预计 ≤150 行
- rfp-analyze 的"够不够"判断只读这层

**明细层**（LLM 按需读）：`知识库/团队/cert-registry.yaml`
- 每条记录：`{name, emp_id, cert_type, cert_category, cert_no, valid_until, status}`
- 只保留**有效**证书（过期的保留原始 Excel 作参考，不转 YAML）
- 1086 条 × 每条 2 行紧凑格式 ≈ 2200 行 → 超限
- **拆分策略**：按一级证书类别拆文件（如 `cert-registry-cisp.yaml`、`cert-registry-iso.yaml`），每文件 ≤500 行
- rfp-analyze 需要查"具体派谁"时读对应分片
- bid-draft 需要列名单时读对应分片

**与现有 `company-profile.yaml.team[]` 的关系**：
- `team[]` 保持汇总级不变（角色 × 人数 × 证书类型列表）
- 新增 `team[].evidence_file: 知识库/团队/roster.yaml` 引用

### 4.2 竞品资质对比（来源：`06 资质分析沙盘（公司级）V5.0.xlsx`）

**数据规模**：35 种资质 × ~30 家友商

**结构：每家竞品一个 YAML**（符合 skill-catalog 原设计）

**文件组织**：`知识库/竞品/{slug}.yaml`

每个文件 schema：
```yaml
company: 深信服科技股份有限公司
slug: sangfor
source: "06 资质分析沙盘（公司级）V5.0.xlsx"
last_updated: 2026-04-16

qualifications:
  - category: 安全服务
    name: 国测信息安全服务资质-安全工程类
    level: 三级
    notes: ""
  - category: 体系认证
    name: ISO 27001
    level: 有效
    notes: ""
```

- 每家 ~50 行，LLM 对比时读 2 个文件（我方 company-profile + 对手）
- 全景对比时读所有竞品文件，总量可控
- **可扩展**：加友商 = 加文件，不改现有文件
- 从 Excel 矩阵自动拆分，列名 → slug 映射

**与 company-profile.yaml 的关系**：
- 我方资质已在 `qualifications[]`，不重复
- rfp-analyze 做竞品对比时：读 `company-profile.yaml` + 读 `竞品/{对手}.yaml`

### 4.3 产品证书（来源：`04 资质分析沙盘（产品级）V5.0.xlsx`）

**数据规模**：5224 条（含竞品产品），我方产品预计 100-300 条

**结构：扩展现有产品 YAML schema**

在 `知识库/产品档案/{product}.yaml` 现有 schema 上新增 `certifications:` 字段：

```yaml
# 在现有 meta/capabilities/technical 之后追加
certifications:
  - name: 网络安全专用产品安全检测证书
    issuer: 公安部
    cert_no: xxx
    valid_until: 2027-06-30
    product_type: 防火墙
    level: EAL3+
```

- 只抽**我方产品**行，竞品产品数据归入 `竞品/{slug}.yaml` 或忽略
- 每个产品增加 ~20 行认证数据
- 如果产品数量太多（>20 个产品文件），补一个 `产品档案/cert-summary.yaml` 汇总层

**与 company-profile.yaml 的关系**：
- `qualifications[]` 是**公司级**资质（ISO/CMMI/CCRC），不含产品级
- 产品级证书只存在产品档案里，不交叉

## 5. 范围

### 5.1 纳入
- 三类 schema 定义（YAML 结构 + 字段约定 + 文件组织）
- 从 Excel 自动转换为 YAML 的一次性脚本（或 skill Phase 0 里做）
- roster.yaml 汇总层自动生成
- 竞品 YAML 自动拆分
- 更新 `知识库/` 各子目录 README.md 的 schema 说明

### 5.2 非纳入
- 人员证书的自动更新/过期提醒（v0.3 `knowledge-review`）
- 竞品情报的自动刷新（v0.3 `competitor-scan` skill）
- 产品档案的完整填充（大量手工工作，不属于 ingest 范围）
- rfp-analyze / bid-draft 对新字段的消费逻辑改造（独立 PR）

## 6. 验收标准

1. `roster.yaml` 有 `cert_summary` 段，rfp-analyze 能回答"我们有几个 CISP"
2. `cert-registry-*.yaml` 分片文件总条目数 = Excel 有效行数
3. `竞品/*.yaml` 文件数 ≥ 10（主要友商），每文件 schema 一致
4. 产品 YAML 有 `certifications:` 字段，从 Excel 抽取
5. 所有 YAML 文件 ≤ 1000 行
6. 原始 Excel 保留在知识库对应目录作为 source of truth 备查

## 7. 实现优先级

1. **人员资质**（最高）— 直接补上 rfp-analyze 的最大盲区
2. **竞品对比**（高）— 差异化分析从定性升级为定量
3. **产品证书**（中）— 依赖先有产品档案 YAML，可能需要手工建基础文件

## 8. 开放问题（实现阶段决定）

1. 人员证书按什么一级类别拆分片？需要看 Excel 的实际分布再定
2. 竞品 slug 命名规则（拼音 / 英文 / 简称）？建议跟 Excel 列名走
3. 产品档案目前是空的（只有 example.yaml），需要先从 04 Excel 识别我方产品列表再建文件
4. 是否保留已过期人员证书？建议不转 YAML，保留 Excel 原件
