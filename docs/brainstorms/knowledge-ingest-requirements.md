# ps:knowledge-ingest 需求文档

**日期**：2026-04-15
**版本**：v0.2 MVP
**状态**：设计已拍板，待实现
**上游**：`docs/design/skill-catalog.md` §3.1 + §11 开放决策 #1

## 1. 目标

让用户零配置地把资质证书类证据文件入库，并自动同步到 `company-profile.yaml`，为 `ps:rfp-analyze` 的 Go/No-Go 判断提供可追溯的证据链起点。

**核心约束**：用户只负责把 PDF 扔进目录，不写任何 YAML、不维护 manifest、不标元数据。所有结构化信息由 LLM 从文件内容抽取，用户在表格里确认即可。

## 2. 问题与动机

v0.1 的 `company-profile.yaml` 是种子模板，`qualifications: []` 空数组。现状用户要手写 YAML + 手填有效期 + 手贴文件路径，体验差到没人会填，`rfp-analyze` 的"是否满足资质要求"判断因此只能基于空知识库瞎猜。`knowledge-ingest` 是打破这个死锁的第一把钥匙。

## 3. 范围（MVP）

### 3.1 纳入
- 只处理 `知识库/资质证书/` 目录
- 支持文件类型：PDF（v0.2 起点）
- LLM 从证书内容抽取：证书名称、发放机构、证书编号、有效期起止、适用主体
- 展示抽取结果表格，用户确认后写入 `company-profile.yaml` 的 `qualifications[]`
- 已登记的文件不重复处理
- 低置信度字段 ⚠️ 标记，用户手修

### 3.2 非纳入（v0.3+ 再做）
- `cases/` / `products/` / `about/` / `competitors/` / `team/` 五类子目录
- DOCX / PPTX / 图片扫描件
- OCR（扫描型 PDF 先报错提示用户换原生 PDF）
- 批量撤销 / rollback
- 证书到期提醒
- 跨多公司 profile（单公司假设）

## 4. 用户旅程

```
1. 用户把 iso27001.pdf 扔进 知识库/资质证书/
2. 用户说 "入库一下资质证书" → 触发 /ps:knowledge-ingest certs
3. Skill 扫描目录，对比 company-profile.yaml 已引用的 evidence_file
4. 发现新文件 N 个，逐个调 LLM 抽取元数据
5. 会话里展示紧凑表格（见 §5）
6. 用户批准 / 勾掉不要的 / 纠正字段
7. Skill 把批准的条目 append 进 qualifications[]
8. 打印 "已登记 N 条，跳过 M 条"
```

## 5. 交互契约

### 5.1 触发
- `/ps:knowledge-ingest certs`（v0.2 唯一参数）
- 无参时默认 certs 并在输出里说明"v0.2 只支持 certs"

### 5.2 文件状态判定
**唯一真相源**：`company-profile.yaml.qualifications[].evidence_file`

- 目录里的文件路径 ∈ 某条 qualification 的 evidence_file → 已登记，跳过
- 不存在 → 新文件，走抽取流程
- 用户想重新抽取 → 手动删除 YAML 里的对应条目，再跑一次
- **不引入**：`.ingest-state.json` / hash ledger / 隐藏状态文件

### 5.3 抽取确认表格
每次运行必须在会话里输出一张紧凑表格（不折行、列数 ≤ 6）：

| # | 文件 | 证书名 | 发证机构 | 有效期至 | 置信度 |
|---|------|--------|----------|----------|--------|
| 1 | iso27001.pdf | ISO 27001 信息安全管理体系 | CNAS | 2027-06-30 | ✅ |
| 2 | 等保三级.pdf | 信息系统安全等级保护三级 | ⚠️ 公安部? | ⚠️ 未识别 | ⚠️ |

置信度规则：
- ✅ 所有关键字段均抽取成功且 LLM 自评 ≥ 高
- ⚠️ 任一关键字段缺失 / LLM 自评为中低 → 该条整行标 ⚠️，用户必须决定（批准/跳过/手修）

### 5.4 写入策略
- 批准的条目以 append 方式加入 `qualifications[]`，不覆盖已有条目
- `id` 字段自动生成：`QUAL-{zero-padded-incremental}`，从已有最大 id +1
- 原始 PDF 文件不移动、不改名、不复制
- 写入后打印：`✅ 已登记 N 条 | ⏭️ 跳过 M 条（已存在） | ⚠️ 用户放弃 K 条`

## 6. 数据约定

### 6.1 qualification 条目 schema（对齐 templates/company-profile.yaml 现有格式）
```yaml
qualifications:
  - id: QUAL-001
    name: ISO 27001 信息安全管理体系认证
    issuer: CNAS
    cert_no: IS-2024-12345        # 新增字段，LLM 抽取
    valid_from: 2024-07-01
    valid_until: 2027-06-30
    evidence_file: 知识库/资质证书/iso27001.pdf
    ingested_at: 2026-04-15        # 新增字段，入库时间戳
    confidence: high               # 新增字段：high/medium/low
```

**新增字段向后兼容**：`rfp-analyze` 已有逻辑只依赖 `name / valid_until / evidence_file`，新字段不破坏既有读取。

### 6.2 路径约定
- 扫描根：`${PRESALES_HOME}/知识库/资质证书/`
- `evidence_file` 写入 YAML 时用**相对 PRESALES_HOME 的路径**：`知识库/资质证书/iso27001.pdf`

## 7. 验收标准

1. **空知识库冷启动**：扔 3 个真实证书 PDF → 跑 ingest → qualifications[] 有 3 条，evidence_file 路径全部指向真实存在的文件
2. **幂等性**：立刻再跑一次 → 打印 "跳过 3 条"，YAML 无任何变动
3. **低置信度路径**：扔 1 个扫描件 PDF（LLM 抽不出字段）→ 表格整行标 ⚠️，用户选"跳过" → YAML 不新增条目
4. **追溯完整**：`ps:rfp-analyze` 引用某条 qualification 时，`evidence_file` 指向的文件必须真实存在（v0.1 架构约束 §10.8 已规定）
5. **禁止隐藏状态**：运行完后 `知识库/` 目录里不应出现 `.ingest-state.json` / `.cache/` 等隐藏文件

## 8. 非功能约束

- **单次扫描上限**：≤ 20 个新文件。超过时先打印警告要求用户分批（避免 LLM 调用爆炸）
- **LLM 预算**：每个文件一次抽取调用，失败重试 1 次
- **离线失败模式**：LLM 不可用时直接报错退出，不进入"用户手填"兜底（会破坏零配置承诺）
- **SKILL.md 行数**：≤ 150 行（规则：细节进 references/）

## 9. 开放问题（实现阶段决定）

以下不影响需求定案，留给 `ps:plan` 阶段：
1. LLM 抽取 prompt 的 few-shot 用哪几张证书？（需要用户提供 2-3 个真实样本）
2. 表格在终端里怎么渲染得紧凑好读？（可能要用 `rich` 或纯 ASCII）
3. `rfp-analyze` 现有代码对 `qualifications` 字段的读取点在哪，新字段引入是否真的零破坏？（需要代码侧验证）

## 10. 与路线图的关系

- **解锁**：`ps:rfp-analyze` 的真实 Go/No-Go 判断、`ps:bid-draft` 的资质章节自动填充
- **后续扩展路径**（v0.3+）：同一套"原地扫描 + LLM 抽取 + 表格确认"模板套用到 `cases/` `products/` 等子目录，每个类型单独拍 schema
- **不与 retrospect 冲突**：`retrospect` 产出的 `lessons.jsonl` 是另一条知识回路，与 ingest 互不依赖
