# presales-engine 完整 Skill 目录 + 路线图

> 本文档枚举售前全生命周期所需的所有 skill，按 pipeline 顺序组织，标注版本阶段（v0.1 ✅ / v0.2 🚧 / v0.3 🚧 / v1.0 📋）。
>
> 这是**产品路线图**，不是 v0.1 实现细节。v0.1 的 skill 契约和 schema 见 `architecture-v0.1.md`。
>
> 本文档的目的：让任何时刻产品的"完整形态"可见，指导版本规划和优先级决策，避免 v0.1 的设计决策无意中阻塞后续 skill 的建设。

## 1. 设计思想：Compound 数据回路

对标 compound-engineering 的核心思想：**每次交付都沉淀知识反哺下一次**。这是 presales-engine 和普通 "RFP 解析工具"的本质区别。

```
每个商机跑完 ps:retrospect
        ↓
cases/<slug>/ 归档完整历史（RFP + 分析 + 草稿 + 结果 + 复盘）
        ↓
ps:knowledge-ingest 自动提取可复用资产
        ↓
下次 ps:rfp-analyze 检索相似案例  → 证据更充分
下次 ps:bid-draft 引用权重最高的案例 → 论证更硬
下次 ps:solution-ideate 避开失败模式  → 决策更准
下次 ps:discover 更快识别 BANT 缺口   → 资源更省
```

一年后，`cases/` 积累 20-50 个单子，`lessons.jsonl` 积累 100+ 条失败模式，`知识库/` 有完整证据链——这时候系统才真正有护城河。v0.1 到 v1.0 的每个 skill 都在为这个飞轮加润滑。

## 2. 完整生命周期全景图

```
前置阶段        需求挖掘         投标决策         方案构造         标书产出         提交后        赢/丢复盘
  ┌──────┐      ┌──────┐       ┌──────┐       ┌──────┐        ┌──────┐        ┌──────┐      ┌───────┐
  │ lead-│      │intake│       │rfp-  │       │ideate│        │ draft│        │  qa  │      │retro- │
  │ scan │─────▶│disco-│──────▶│parse │──────▶│ plan │───────▶│review│───────▶│negoti│─────▶│spect  │
  │      │      │ver   │       │analy-│       │price │        │comp- │        │      │      │       │
  │      │      │quali-│       │ze    │       │      │        │liance│        │      │      │       │
  └──────┘      │ fy   │       └──────┘       └──────┘        └──────┘        └──────┘      └───┬───┘
                └──────┘                                                                          │ 沉淀
                                                                                                   ▼
                  ┌──── 知识资产（cross-cutting，任何阶段独立跑） ──────┐
                  │                                                          │
                  │  knowledge-ingest  │  case-match                        │
                  │  competitor-scan   │  objection-lib                     │
                  │                                                          │
                  └──────────────────────────────────────────────────────────┘

                  ┌──── Meta / 系统级 ───────────────────────────────────────┐
                  │  setup ✅   │   status   │   doctor                     │
                  └──────────────────────────────────────────────────────────┘

                  ┌──── 客户关系（跨周期） ───────────────────────────────────┐
                  │  account-profile  │  account-update  │  relationship-map │
                  └──────────────────────────────────────────────────────────┘
```

## 3. Pipeline Skills（按流水线顺序）

### 3.1 前置阶段

#### `ps:lead-scan` 📋 v1.0
- **职责**：从行业会议、公开招采网、邮件订阅、社交平台扫描线索
- **输入**：线索源配置 `config.leads_sources`
- **输出**：`leads/{date}-{source}.yaml` 线索列表
- **依赖**：外部 API / 爬虫 / RSS
- **价值**：主动发现机会，减少对人工线索的依赖

### 3.2 需求挖掘（pre-RFP）

#### `ps:intake` 🚧 v0.3
- **职责**：接线初触，销售和客户第一次沟通完后记录初步需求
- **输入**：对话纪要（自然语言粘贴）
- **输出**：`商机/{slug}/context.yaml`（客户、场景、初步痛点、预算区间、时间窗）
- **交互**：AskUserQuestion 填充 BANT/MEDDIC 必填字段
- **价值**：让每个新机会都有结构化起点，不靠销售记忆

#### `ps:discover` 🚧 v0.3
- **职责**：Socratic 式深度需求挖掘
- **输入**：`context.yaml` + 追加对话
- **输出**：`商机/{slug}/discovery.md`（决策链图、痛点优先级、预算确认、关键决策人立场、竞争态势推断）
- **关键机制**：不让销售填表，agent 主动反问追到底层真需求
- **价值**：售前最大的浪费是需求挖得浅，这是护城河

#### `ps:qualify` 🚧 v0.3
- **职责**：pre-RFP 阶段的 Go/No-Go 资格评分
- **输入**：discovery.md + `知识库/company-profile.yaml`
- **输出**：`商机/{slug}/qualify.yaml`（BANT/MEDDIC 评分 + 前置建议）
- **硬规则**：BANT 不过关主动劝退，避免沉没成本
- **价值**：投标前止损，省掉后面 90% 的浪费

### 3.3 RFP 阶段（v0.1 核心）

#### `ps:rfp-parse` ✅ v0.1
- 见 `architecture-v0.1.md` §4.2 的完整契约
- **职责**：PDF/Word RFP → 结构化 `rfp.yaml`
- **输入**：`商机/{slug}/招标文件/原件/*.{pdf,docx,md}`
- **输出**：`分析/rfp.yaml`、`招标文件/extracted.md`、`meta.yaml`

#### `ps:rfp-analyze` ✅ v0.1
- 见 `architecture-v0.1.md` §4.3 的完整契约
- **职责**：战略分析 + Go/No-Go 决策矩阵
- **输入**：`rfp.yaml` + `company-profile.yaml` + `产品档案/*.yaml`
- **输出**：`分析/analysis.md`（废标风险 / 评分杠杆 / 竞品格局 / 决策矩阵 / 信息缺口）

### 3.4 方案设计

#### `ps:solution-ideate` 🚧 v0.3
- **职责**：方案多路径发散
- **输入**：`rfp.yaml` + `analysis.md` + `产品档案/*.yaml`
- **输出**：`商机/{slug}/方案/candidates.md`（**3 条路径**：最小可行 / 标准推荐 / 旗舰方案）
- **硬规则**：强制产出 3 条，避免销售只会报一个中间档
- **价值**：反自嗨机制，客户能感受到选项对比

#### `ps:solution-plan` 🚧 v0.3
- **职责**：选定方案后的技术架构 + 交付拆解
- **输入**：选定的 candidate
- **输出**：`方案/plan.md`（架构图、模块拆分、交付工时、人员配置、风险清单）
- **价值**：让 draft 阶段有可实施性依据

### 3.5 标书产出

#### `ps:price` 🚧 v0.2
- **职责**：报价推演
- **输入**：`plan.md` + `知识库/竞品/*.yaml` + `company-profile.pricing_baseline`
- **输出**：`商机/{slug}/pricing.yaml`（成本底线 + 3 档报价 + 竞品锚定 + 让步顺序 + 风险溢价）
- **价值**：销售最痛的环节，避免裸报或报错

#### `ps:bid-draft` ✅ v0.1
- 见 `architecture-v0.1.md` §4.4 的完整契约
- **职责**：按章节生成标书草稿，强制追溯标记
- **输出**：`草稿/outline.md` + `草稿/章节/{NN-name}.md`

#### `ps:bid-review` 🚧 v0.2
- **职责**：多角色批判（对标 ce:review）
- **输入**：draft + rfp + analysis + pricing
- **输出**：`草稿/review.md`（5 个 persona 并行批判）
- **Persona 清单**：
  - 技术可行性（架构 / 实施风险 / 资源匹配）
  - 商务合规（法务 / 条款风险 / 合同条件）
  - 客户视角（是否回答了客户真正关心的问题）
  - 竞品对抗（我们的方案对比竞品有多少真差异化）
  - 内部成本（毛利 / 交付风险 / 机会成本）
- **价值**：CE 最核心的质量机制，对售前同样适用

#### `ps:bid-compliance` 🚧 v0.2
- **职责**：合规清单机械检查
- **输入**：draft + rfp.yaml
- **输出**：`草稿/compliance-report.md`（废标项覆盖矩阵 + 评分项响应覆盖矩阵）
- **硬规则**：漏项不允许提交
- **价值**：防漏应答（这是 v0.1 bid-draft 里承诺但未实现的硬门槛）

### 3.6 提交后

#### `ps:bid-qa` 🚧 v0.2
- **职责**：评标澄清问答应对
- **输入**：甲方澄清问题 + rfp + draft + analysis
- **输出**：`商机/{slug}/qa/{NN-question}.md`（答案 + 依据 + 风险提示）
- **价值**：提交后周旋环节不靠销售拍脑袋

#### `ps:bid-negotiate` 📋 v1.0
- **职责**：商务谈判辅助
- **输入**：谈判上下文 + pricing.yaml + 竞品档案
- **输出**：让步建议 + 底线红线 + 换让策略
- **价值**：临门一脚环节

### 3.7 复盘

#### `ps:retrospect` 🚧 v0.2
- **职责**：赢/丢复盘 → 沉淀到 cases + lessons
- **输入**：项目结果（赢/丢/推迟/废标） + 用户叙述
- **输出**：
  - `归档/{slug}/` ← 整个商机目录搬过来
  - `知识库/lessons.jsonl` 追加条目（含 fail_mode 标签）
  - `company-profile.yaml.case_references` 追加条目（若赢单 + 客户授权）
- **硬规则**：没跑 retrospect 的商机不允许归档
- **价值**：**数据回路闭环的起点**，是这套系统的灵魂

## 4. 知识资产（cross-cutting）

这层 skill 独立于 pipeline，任何阶段都可以跑。是系统的长期资产层。

#### `ps:knowledge-ingest` 🚧 v0.2（**高优先级，先定设计**）

- **职责**：按标准格式把用户提供的证据文件批量入库
- **输入格式**（待定）：
  - 选项 A：目录约定（用户把文件按 `ingest/certs/` / `ingest/cases/` 摆好，跑 ingest 自动归类）
  - 选项 B：manifest 文件（`ingest.yaml` 里列每个文件的类型 + 元数据）
  - 选项 C：混合（文件 + 可选 manifest，manifest 缺失时用 LLM 推断）
- **处理流程**：
  1. 识别文件类型（PDF/DOCX/PPTX/图片扫描）
  2. 提取元数据（证书有效期、客户名、项目金额、产品功能点）
  3. 按类型映射到 YAML schema
  4. 拷贝原始文件到 `知识库/{子目录}/`
  5. 生成 / 更新 `company-profile.yaml` 的引用条目
- **价值**：整个证据链的起点。所有 `qualifications` / `case_references` / `产品档案` 都靠它。设计对了，后续 rfp-analyze 就能做真实可追溯的 Go/No-Go
- **v0.2 拆解**：先定输入格式规范（纯设计无代码），再实现 certs/ 子流程作为 MVP

#### `ps:case-match` 🚧 v0.3
- **职责**：历史案例检索
- **输入**：关键词 + 行业 + 规模区间
- **输出**：Top 5 相似案例（含权重 + 引用路径）
- **谁调用**：`rfp-analyze` / `bid-draft` / `solution-ideate`
- **价值**：让历史积累真正"变现"

#### `ps:competitor-scan` 🚧 v0.3
- **职责**：竞品情报扫描
- **输入**：竞品名
- **输出**：`知识库/竞品/{slug}.yaml`（公开信息：产品能力 / 定价 / 典型客户 / 优缺点）
- **价值**：`rfp-analyze` 的竞品格局推断升级为定量分析

#### `ps:objection-lib` 📋 v1.0
- **职责**：客户异议应对话术库
- **输入**：客户异议原话
- **输出**：历史类似异议 + 应对话术 + 成功率
- **价值**：低层反复出现的场景不再靠记忆

## 5. Meta / 系统级

#### `ps:setup` ✅ v0.1
- 见 `skills/setup/SKILL.md`
- **职责**：初始化 / 迁移 / 重置工作区

#### `ps:status` 🚧 v0.2
- **职责**：列出所有 slug 当前的 pipeline stage
- **输入**：无
- **输出**：表格（slug / 客户 / 阶段 / deadline / 最后活动时间）
- **Stage 枚举**：`new / intake / discovered / qualified / parsed / analyzed / drafted / reviewed / submitted / clarifying / closed-won / closed-lost`
- **价值**：跑 3 个以上商机就必须的可见性

#### `ps:doctor` 📋 v1.0
- **职责**：检查 knowledge 引用完整性、证据文件存在性、schema 合规性
- **输入**：无
- **输出**：健康报告（断链 / 孤儿文件 / 过期证书 / schema 漂移）
- **价值**：长期运行后系统自检

## 6. 客户关系（跨周期）

#### `ps:account-profile` 📋 v1.0
- **职责**：重点客户档案
- **输入**：客户名
- **输出**：`知识库/accounts/{customer-slug}.yaml`（采购偏好 / 决策链 / 往来历史 / 关键联系人）

#### `ps:account-update` 📋 v1.0
- **职责**：每次接触后更新客户档案

#### `ps:relationship-map` 📋 v1.0
- **职责**：跨商机关系图谱
- **输入**：所有 opportunity + account 数据
- **输出**：关系图（谁在哪个项目对我们表态 / 决策权重 / 影响路径）

## 7. 版本路线图

### v0.1（已发布，11 commits，GitHub 仓库：wuwu119/presales-engine）

- ✅ `ps:setup` — URL 驱动初始化 + 完整中文知识库骨架 + 父目录交互
- ✅ `ps:rfp-parse`
- ✅ `ps:rfp-analyze`
- ✅ `ps:bid-draft`

**目标**：最小应标闭环，一份 RFP 能从文件变成可追溯的草稿

### v0.2（下一版本，重点：质量门槛 + 知识资产基础）

- 🚧 `ps:knowledge-ingest`（**先定设计，再写代码**）
- 🚧 `ps:retrospect`（数据回路闭环）
- 🚧 `ps:bid-review`（多角色批判，对标 ce:review）
- 🚧 `ps:bid-compliance`（合规清单，把 v0.1 没实现的硬门槛补上）
- 🚧 `ps:bid-qa`
- 🚧 `ps:status`
- 🚧 `ps:price`

**目标**：可对外交付的 beta，支持完整一单从 RFP 到归档

### v0.3（深度阶段，重点：pre-RFP + 知识复利）

- 🚧 `ps:intake`
- 🚧 `ps:discover`
- 🚧 `ps:qualify`
- 🚧 `ps:solution-ideate`
- 🚧 `ps:solution-plan`
- 🚧 `ps:case-match`
- 🚧 `ps:competitor-scan`

**目标**：打通 pre-RFP 阶段，支持主动打单和跨单子知识复利

### v1.0（成熟版本，重点：主动性 + 关系管理）

- 📋 `ps:lead-scan`
- 📋 `ps:bid-negotiate`
- 📋 `ps:objection-lib`
- 📋 `ps:account-profile` / `account-update` / `relationship-map`
- 📋 `ps:doctor`

**目标**：完整售前 + 客户关系管理，从接线到赢单全链路

## 8. 建设优先级（下一步 v0.2）

按 ROI × 依赖关系排序。前 3 个是必做，后 4 个按需：

1. **`ps:knowledge-ingest`（设计先行）**
   - 为什么第一：定了输入格式之后整个证据链才有起点。不定它，所有后续 skill 都要假设知识库是空的或者靠用户手写，体验差
   - v0.2 拆解：先一个独立 brainstorm session 定规范 → 再实现 certs/ 子流程 MVP → 再补 cases/products/

2. **`ps:retrospect`（数据回路闭环）**
   - 为什么第二：没有它所有跑过的单子都是孤岛，`cases/` 永远是空目录，flywheel 无法启动
   - 依赖：独立，可立即建

3. **`ps:bid-review`（质量跃迁）**
   - 为什么第三：对标 ce:review 的最核心机制。建好之后 `bid-draft` 产出质量会飞跃
   - 依赖：independent，但最好等 knowledge-ingest 落地后，review 引用证据更有料

4. **`ps:bid-compliance`（硬门槛）**
   - 为什么第四：v0.1 bid-draft 里承诺了"覆盖率 < 100% 强制报警"但其实没实现。补这个洞
   - 可和 bid-review 同步做

5. **`ps:status`（日常可见性）**
   - 小 skill 但救命，跑 3 个以上商机必需
   - 依赖：无，随时可建

6. **`ps:bid-qa`（提交后周旋）**
   - 价值高但依赖真实评标澄清场景，需要先跑完一个真实单子才能调教

7. **`ps:price`（商务决策）**
   - 价值高但依赖真实成本数据和竞品档案，需要 v0.3 的 competitor-scan 铺垫

## 9. 不纳入 v1.0 的能力（明确边界）

v1.0 仍然是**售前工具**，不包含：

| 领域 | 原因 | 替代 |
|---|---|---|
| CRM | 用户通常已有 Salesforce / HubSpot / 纷享销客 | 外部系统，可做数据导入 |
| 项目交付 | 不是售前范围（中标后项目经理的事） | 外部工具 |
| 财务结算 | 不是售前范围 | 外部 ERP |
| ERP 集成 | v2+ 考虑 | v2+ |
| 合同管理 | 边界模糊，可能 v1.x 再纳入 | 外部合同管理工具 |

边界原则：**任何和"从接线到赢单"直接相关的留在 presales-engine；赢单之后的流程全部外包**。

## 10. 架构一致性约束（跨所有 skill）

从 v0.1 继承、对所有后续 skill 同样有效的硬规则（出自 `architecture-v0.1.md` §9 + `CLAUDE.md`）：

1. **Skill 间零 import** — 耦合只通过文件系统
2. **禁止在 skill 内做文件系统体力活** — 统一走 `scripts/`（rfp-parse Phase 0 是 v0.1 临时例外，v0.2 移到 `scripts/ps_opportunity.py`）
3. **禁止把用户数据写到插件目录** — 只能写 `PRESALES_HOME`
4. **SKILL.md ≤ 300 行** — 精简原则
5. **LLM 做决策，脚本做体力活** — 判断力不写脚本，确定性操作才写脚本
6. **用户数据目录用中文命名** — 商机/归档/知识库/模板 + 各子目录；文件名和 dict keys 保持英文
7. **每段产出可追溯** — 任何 LLM 生成的结构化产物（rfp.yaml / analysis.md / bid 章节 / qa 应答）都必须带 source 引用
8. **证据链完整** — `company-profile` 引用的文件必须真实存在于 `知识库/` 对应子目录，不能凭空构造

## 11. 未解问题 / 开放决策

以下问题在 v0.2 设计前需要用户拍板：

1. **knowledge-ingest 输入格式**：目录约定 / manifest / 混合？
2. **retrospect 归档时机**：跑完 bid-draft 后立即允许归档，还是必须等 submission 结果？
3. **bid-review 的 persona 数量**：5 个够不够？是不是按行业再细分（金融/政务/互联网）？
4. **price 的成本数据来源**：从历史 retrospect 回填，还是手工维护 cost-baseline.yaml？
5. **solution-ideate 的 3 条路径硬约束**：是否允许客户明确拒绝中间档后退化到 2 条？
6. **跨商机知识复利**：case-match 的权重算法（行业相似度 / 规模匹配 / 时间衰减），待实数据后调参
