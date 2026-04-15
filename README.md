# presales-engine

> 售前复合引擎：从招标文件到标书正文的 Claude Code 插件

从零启动的方案售前工作流。把 RFP 解析、战略分析、标书生成串成最小闭环，历史案例和复盘结论自动沉淀、反哺下一个单子。

**v0.1 聚焦应标场景**，后续版本扩展到需求挖掘、方案规划、报价、赢丢复盘。

## 特性

- 🔍 **RFP 智能解析** — PDF / Word / Markdown 招标文件结构化为 YAML（评分项 / 废标项 / 需求清单 / 时间节点 / 资质要求）
- 🎯 **战略分析** — 自动扫描废标风险、识别评分杠杆、给出 Go/No-Go 决策矩阵
- ✍️ **标书生成** — 分章节生成草稿，每段可追溯到 RFP 评分项，防止自嗨式方案
- 🗄️ **数据程序分离** — 插件只读，用户数据存于 `~/售前/`，便于备份、迁移、多机同步
- 📚 **知识累积** — 历史案例、复盘结论逐步沉淀，作为未来投标的参考

## 安装

### 方式一：通过 Claude Code marketplace（推荐）

```
/plugin marketplace add wuwu119/presales-engine
/plugin install presales-engine@wuwu119
```

### 方式二：本地开发

```bash
git clone https://github.com/wuwu119/presales-engine.git ~/代码库/presales-engine
```

然后在 `~/.claude/settings.json` 注册本地插件路径。

## 快速上手

### 1. 首次初始化

```
/ps:setup
```

**只问一个问题：公司官网 URL**。Claude 用 `WebFetch` 抓主页，抽取最小字段（公司名、行业一句话、成立年份/规模/总部 best-effort），展示给你确认，然后写入 `~/售前/`：

- `config.yaml`（基础配置，语言默认 zh-CN，货币默认 CNY）
- `知识库/company-profile.yaml`（只填抓到的基础字段；`qualifications` / `case_references` / `team` 一律留空）
- 种子模板复制到 `~/售前/模板/`

URL 抓不到或你没给 URL → 回退到最小 3 题问答：公司中文名 + 英文名 + 行业一句话，其他留空。

> ⚠️ **证据库 / 产品库 / 案例库不在 setup 范围**。setup 只建基础骨架；资质证书、客户案例、产品手册的录入走未来独立的 `ps:knowledge-ingest` 流程。

**想指定数据位置**？三种方式：
- 命令行：`python3 ps_setup.py --init --home /your/path`
- 一次性覆盖（不持久化）：设置环境变量 `PRESALES_HOME=/custom/path`
- 默认 `~/售前/`（可见目录，方便后续手工编辑）

### 2. 解析招标文件

```bash
mkdir -p ~/售前/商机/acme-2026/招标文件/原件
cp /path/to/招标文件.pdf ~/售前/商机/acme-2026/招标文件/原件/
```

然后运行：

```
/ps:rfp-parse acme-2026
```

产出：
- `招标文件/extracted.md` — 文本提取（人读用）
- `分析/rfp.yaml` — 结构化结果（评分项 / 废标项 / 需求 / 时间 / 资质）

### 3. 战略分析

```
/ps:rfp-analyze acme-2026
```

自动对照 `知识库/company-profile.yaml`，输出 `分析/analysis.md`：

- **废标风险** — 硬性资质不满足的项
- **评分杠杆** — 高权重且我方有优势的项
- **竞品格局推断** — 疑似陪标、是否定标
- **Go / No-Go 决策矩阵** — 6 维度打分
- **信息缺口** — 必须和客户澄清的问题

### 4. 生成标书草稿

```
/ps:bid-draft acme-2026
```

按章节生成标书草稿，写入 `草稿/章节/`。每段末尾注明对应的 RFP 评分项编号：

> [对标: SCORING-03 / REQ-12]

覆盖率 < 100% 时强制报警，防止漏应答。

## 数据目录

所有用户数据存储在 `~/售前/`（可通过 `PRESALES_HOME` 环境变量覆盖）：

```
~/售前/
├── .version                     # 插件版本号
├── config.yaml                  # 用户配置
├── 商机/                        # 活跃商机目录（每个项目一个子目录）
│   └── {slug}/
│       ├── meta.yaml
│       ├── 招标文件/
│       ├── 分析/
│       └── 草稿/
├── 归档/                        # 跑完的 opportunity 整体搬过来
├── 知识库/                      # 公司档案、产品档案、竞品档案等
│   ├── README.md
│   ├── company-profile.yaml
│   ├── 公司介绍/
│   ├── 资质证书/
│   ├── 客户案例/
│   ├── 产品档案/
│   ├── 竞品/
│   └── 团队/
└── 模板/                        # 用户自定义模板
```

**插件本身不存储任何用户数据**，卸载插件不影响 `~/售前/`。

## 隐私和安全

- 所有 RFP、方案、客户信息保留在本地 `~/售前/`
- 插件仓库 `.gitignore` 排除 `售前/`、`presales/`、`.presales/`（防御老数据）
- 建议 `~/售前/` 单独备份，不要 commit 到任何仓库

## 开发路线

- ✅ v0.1 — 应标最小闭环（setup / rfp-parse / rfp-analyze / bid-draft）
- 🚧 v0.2 — 合规检查 + 多角色 review + 澄清问答
- 🚧 v0.3 — 历史案例检索 + 负向学习 + 竞品雷达
- 📋 v1.0 — 完整售前闭环（intake / discover / ideate / plan / draft / review / price / retrospect）

## 贡献

- Issue: https://github.com/wuwu119/presales-engine/issues
- PR: 请先读 [CLAUDE.md](./CLAUDE.md) 了解开发规则

## License

MIT
