# presales-engine

> 售前复合引擎：从招标文件到标书正文的 Claude Code 插件

从零启动的方案售前工作流。把 RFP 解析、战略分析、标书生成串成最小闭环，历史案例和复盘结论自动沉淀、反哺下一个单子。

**v0.1 聚焦应标场景**，后续版本扩展到需求挖掘、方案规划、报价、赢丢复盘。

## 特性

- 🔍 **RFP 智能解析** — PDF / Word / Markdown 招标文件结构化为 YAML（评分项 / 废标项 / 需求清单 / 时间节点 / 资质要求）
- 🎯 **战略分析** — 自动扫描废标风险、识别评分杠杆、给出 Go/No-Go 决策矩阵
- ✍️ **标书生成** — 分章节生成草稿，每段可追溯到 RFP 评分项，防止自嗨式方案
- 🗄️ **数据程序分离** — 插件只读，用户数据存于 `~/presales/`，便于备份、迁移、多机同步
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

交互式问答：**数据存放位置（默认 `~/presales/`，可改）**、公司名、行业、产品线、默认语言。执行后：
- 在你选的位置生成目录骨架（默认 `~/presales/`，可见目录方便手工编辑）
- 写入 `config.yaml` 和 `company-profile.yaml`
- 复制种子模板
- 把所选路径持久化到 `~/.config/presales-engine/home`（指针文件，下次自动用）

**想换位置**？三种方式：
- 交互式 setup 时直接回答 Q1
- 命令行：`python3 ps_setup.py --init --home /your/path --config-json '{}'`
- 一次性覆盖（不持久化）：设置环境变量 `PRESALES_HOME=/custom/path`

### 2. 解析招标文件

```bash
mkdir -p ~/presales/opportunities/acme-2026/rfp/original
cp /path/to/招标文件.pdf ~/presales/opportunities/acme-2026/rfp/original/
```

然后运行：

```
/ps:rfp-parse acme-2026
```

产出：
- `rfp/extracted.md` — 文本提取（人读用）
- `analysis/rfp.yaml` — 结构化结果（评分项 / 废标项 / 需求 / 时间 / 资质）

### 3. 战略分析

```
/ps:rfp-analyze acme-2026
```

自动对照 `knowledge/company-profile.yaml`，输出 `analysis/analysis.md`：

- **废标风险** — 硬性资质不满足的项
- **评分杠杆** — 高权重且我方有优势的项
- **竞品格局推断** — 疑似陪标、是否定标
- **Go / No-Go 决策矩阵** — 6 维度打分
- **信息缺口** — 必须和客户澄清的问题

### 4. 生成标书草稿

```
/ps:bid-draft acme-2026
```

按章节生成标书草稿，写入 `draft/chapters/`。每段末尾注明对应的 RFP 评分项编号：

> [对标: SCORING-03 / REQ-12]

覆盖率 < 100% 时强制报警，防止漏应答。

## 数据目录

所有用户数据存储在 `~/presales/`（可通过 `PRESALES_HOME` 环境变量覆盖）：

```
~/presales/
├── .version                    # 插件版本号
├── config.yaml                 # 用户配置
├── opportunities/              # 商机目录（每个项目一个子目录）
│   └── {slug}/
│       ├── meta.yaml
│       ├── rfp/
│       ├── analysis/
│       └── draft/
├── cases/                      # 历史案例库
├── knowledge/                  # 公司档案、产品档案、竞品档案
│   ├── company-profile.yaml
│   └── products/
└── templates/                  # 用户自定义模板
```

**插件本身不存储任何用户数据**，卸载插件不影响 `~/presales/`。

## 隐私和安全

- 所有 RFP、方案、客户信息保留在本地 `~/presales/`
- 插件仓库 `.gitignore` 排除 `presales/`、`.presales/`（v0.1 旧默认）和 `opportunities/`
- 建议 `~/presales/` 单独备份，不要 commit 到任何仓库

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
