# presales-engine v0.1

售前复合引擎 Claude Code 插件。从招标文件（RFP）到标书正文的最小闭环，支持历史案例累积和反哺。

## 三原则

1. **LLM 做决策，脚本做体力活** — 判断类逻辑留给 skill，文件操作交给 `scripts/`
2. **程序和数据严格分离** — 插件只读（`${CLAUDE_PLUGIN_ROOT}`），用户数据存 `${PRESALES_HOME}`（默认 `~/售前/`）
3. **每段标书可追溯** — `草稿/章节/*.md` 中每个段落必须对应 `rfp.yaml` 评分项或需求条目

## 架构

6 个 Skill + 一次 setup + 用户数据目录分离。

### Skills

| Skill | 触发 | 职责 |
|-------|------|------|
| `ps:setup` | 首次安装 / 升级 | 创建 `~/售前/` 骨架、写初始配置、复制种子模板 |
| `ps:knowledge-ingest` | 用户说"入库证书" | 扫描资质证书目录，LLM 抽取元数据，确认后写入 company-profile.yaml |
| `ps:knowledge-doctor` | 用户说"知识库诊断" | 9 维度知识库完整度诊断，输出健康度报告 + 缺口指导 |
| `ps:rfp-parse` | 收到招标文件 | RFP（PDF/Word/MD）结构化解析为 `rfp.yaml` |
| `ps:rfp-analyze` | parse 完成后 | 战略分析：废标风险、评分杠杆、Go/No-Go 建议、信息缺口 |
| `ps:bid-draft` | analyze 通过后 | 按章节生成标书草稿，每段追溯到 RFP 评分项 |

### 程序 vs 数据分离

**程序**（插件仓库，只读，Git 管理）：
```
presales-engine/
├── .claude-plugin/         # 插件 manifest
├── skills/                 # 6 个 skill 定义
├── scripts/                # 路径解析 + setup 脚本
├── 模板/              # 种子模板（config / company-profile / outline / products/example）
├── knowledge-seed/         # 知识库骨架种子（每个子目录一个 README.md 填充指南）
├── docs/                   # 架构设计
└── CLAUDE.md / README.md
```

**数据**（`<parent>/售前/`，用户可写，不在 Git；默认 `~/售前/`，交互式 setup 时用户可指定父目录）：
```
<parent>/售前/
├── .version                        # 当前数据目录对应的插件版本
├── config.yaml                     # 用户配置
├── 商机/{slug}/           # 每个商机独立目录
├── cases/                          # 归档的 opportunity（跑完的单整体搬进来）
├── 知识库/                      # 知识库根（README.md 总览 + 以下子目录）
│   ├── company-profile.yaml        # 主档案（相对路径引用下面的文件）
│   ├── about/                      # 公司介绍材料（PDF/PPT/MD）
│   ├── certs/                      # 资质证书（ISO / 许可 / 测评）
│   ├── case-studies/               # 客户案例资料库（可复用，区别于顶层 cases/ 归档）
│   ├── products/                   # 产品 / 服务档案（YAML + 附件）
│   ├── competitors/                # 竞品档案（v0.2 用）
│   └── team/                       # 团队资质（花名册 + 个人证书 + 简历）
└── 模板/                      # 用户自定义模板（覆盖插件种子）
```

每个 `知识库/*/` 子目录启动时带一份 README.md（由 `ps:setup` 从 `knowledge-seed/` 拷贝），说明放什么、命名约定、格式、谁引用。填充 `知识库/` 不归 `ps:setup` 管，走手工或未来独立的 `ps:knowledge-ingest` skill。

**数据目录路径 resolution（3 层，优先级从高到低）**：
1. `PRESALES_HOME` 环境变量（CI / 一次性覆盖）
2. `~/.config/presales-engine/home` 指针文件（由 `ps:setup --home <path>` 持久化）
3. 默认 `~/售前/`（无前导点，可见目录）

### 路径约定

- `PLUGIN_ROOT` = `${CLAUDE_PLUGIN_ROOT}`（Claude Code 注入）
- `PRESALES_HOME` = 用户数据根，三层 resolution 见上，默认 `~/售前/`
- 所有脚本通过 `scripts/ps_paths.py` 解析路径，**禁止硬编码**

### Opportunity 目录契约

```
~/售前/商机/{slug}/
├── meta.yaml               # 基本信息（客户、项目、截止日期、状态）
├── rfp/
│   ├── original/           # 原始招标文件（PDF/Word/扫描件）
│   └── extracted.md        # 文本提取结果
├── 分析/
│   ├── rfp.yaml            # /ps:rfp-parse 产出
│   └── analysis.md         # /ps:rfp-analyze 产出
├── 草稿/
│   ├── outline.md          # 章节大纲
│   └── chapters/           # 分章节草稿
└── review.md               # v0.2 引入
```

## Tech Stack

- Claude Code Plugin 格式（`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`）
- Python 3.10+（脚本层，优先标准库）
- YAML（结构化数据）+ Markdown（产出）

## 开发规则

### 文档语言
- 代码、commit、变量名：**英文**
- 文档（CLAUDE.md、SKILL.md、README.md）：**中文**
- 用户产出（标书草稿）：默认中文，由 `config.yaml.preferences.language` 控制

### SKILL.md 规范
- ≤ 300 行，只写 agent 推断不出的信息（行为契约、约束、交互流程）
- 细节（prompt 模板、schema 样例）放 `references/`
- 行为约束优先用代码实现，不靠文本要求

### Python 源码头注释
每个 .py 文件头部三行：
```python
# INPUT: <依赖模块>
# OUTPUT: <提供的功能>
# POS: <系统定位>
```

### Git 工作流
- Conventional Commits
- 主分支 `main`
- 功能分支 `feat/xxx`、`fix/xxx`、`refactor/xxx`
- commit message 英文祈使语气，首行 ≤72 字符
- 每个 session 结束更新 `progress.md`

### 架构约束
1. **Skill 间零 import** — 耦合只通过文件系统
2. **禁止在 skill 内做文件系统体力活** — 统一走 `scripts/`
3. **禁止把用户数据写到插件目录** — 只能写 `PRESALES_HOME`
4. **每个标书段落必须追溯** — `[对标: SCORING-<id>]` 标记，缺失 = 失败

## Quick Start

见 `README.md`。

## 设计文档

只写接口契约（签名 / IO / 约束），禁止写实现代码。

| 文档 | 位置 | 职责 |
|------|------|------|
| 架构总览 v0.1 | `docs/design/architecture-v0.1.md` | 当前实现契约 + schema + 架构约束 |
| 完整 skill 目录 + 路线图 | `docs/design/skill-catalog.md` | 售前全生命周期所有 skill + v0.2/v0.3/v1.0 分阶段 + 数据回路设计 |

## Changelog

见 `CHANGELOG.md`。
