# 缺口指导模板

每个非充足维度按此模板渲染指导信息。

## company_certs — 公司资质

- **去哪找**：找法务部/行政部要最新证书扫描件，优先续期即将过期的 ISO27001 和 CCRC 系列
- **怎么喂**：把 PDF 扔进 `知识库/资质证书/` 后跑 `/ps:knowledge-ingest certs`
- **特殊**：当 expired > 0 时额外提示"N 条已过期，建议找行政部确认是否已续期"

## team_roster — 团队汇总

- **去哪找**：找 HR 或项目管理部要人员资质明细 Excel
- **怎么喂**：`python scripts/ps_knowledge_extract.py team --xlsx <人员资质.xlsx> --output-dir ~/售前/知识库/团队/`

## team_registry — 团队明细

- **去哪找**：同团队汇总（team 命令自动生成分片）
- **怎么喂**：同上

## products — 产品档案

- **去哪找**：找产品线负责人要 datasheet / 产品手册，或从公司官网下载
- **怎么喂**：每个产品建一个 YAML → `知识库/产品档案/{product-slug}.yaml`

## competitors — 竞品对比

- **去哪找**：找市场部或投标同事要公司级资质竞争分析沙盘 Excel
- **怎么喂**：`python scripts/ps_knowledge_extract.py competitors --xlsx <资质沙盘.xlsx> --output-dir ~/售前/知识库/竞品/`

## about — 公司介绍

- **去哪找**：找行政部/市场部要营业执照、公司宣传册、企业简介
- **怎么喂**：放进 `知识库/公司介绍/`（PDF/PPT/MD 均可）

## case_studies — 客户案例

- **去哪找**：找售前团队/项目经理整理最近 3-5 个成功案例，需要：客户名/行业/金额/摘要
- **怎么喂**：案例材料放 `知识库/客户案例/`

## case_references — 案例引用

- **去哪找**：客户案例入库后手动添加
- **怎么喂**：编辑 `知识库/company-profile.yaml`，在 `case_references[]` 下添加引用条目

## highlights — 差异化亮点

- **去哪找**：从护网战绩、资质优势、行业排名中提炼 3-5 条可量化亮点
- **怎么喂**：编辑 `知识库/company-profile.yaml`，在 `highlights[]` 下添加
