# presales-engine v0.1

售前复合引擎 Claude Code 插件。从招标文件（RFP）到标书正文的最小闭环，支持历史案例累积和反哺。

## 三原则

1. **LLM 做决策，脚本做体力活** — 判断类逻辑留给 skill，文件操作交给 `scripts/`
2. **程序和数据严格分离** — 插件只读（`${CLAUDE_PLUGIN_ROOT}`），用户数据存 `${PRESALES_HOME}`（默认 `~/.presales/`）
3. **每段标书可追溯** — `draft/chapters/*.md` 中每个段落必须对应 `rfp.yaml` 评分项或需求条目

## 架构

4 个 Skill + 一次 setup + 用户数据目录分离。

### Skills

| Skill | 触发 | 职责 |
|-------|------|------|
| `ps:setup` | 首次安装 / 升级 | 创建 `~/.presales/` 骨架、写初始配置、复制种子模板 |
| `ps:rfp-parse` | 收到招标文件 | RFP（PDF/Word/MD）结构化解析为 `rfp.yaml` |
| `ps:rfp-analyze` | parse 完成后 | 战略分析：废标风险、评分杠杆、Go/No-Go 建议、信息缺口 |
| `ps:bid-draft` | analyze 通过后 | 按章节生成标书草稿，每段追溯到 RFP 评分项 |

### 程序 vs 数据分离

**程序**（插件仓库，只读，Git 管理）：
```
presales-engine/
├── .claude-plugin/         # 插件 manifest
├── skills/                 # 4 个 skill 定义
├── scripts/                # 路径解析 + setup 脚本
├── templates/              # 种子模板（config / company-profile / outline）
├── docs/                   # 架构设计
└── CLAUDE.md / README.md
```

**数据**（`~/.presales/`，用户可写，不在 Git）：
```
~/.presales/
├── .version                # 当前数据目录对应的插件版本
├── config.yaml             # 用户配置
├── opportunities/{slug}/   # 每个商机独立目录
├── cases/                  # 历史案例库
├── knowledge/              # 公司档案、产品、竞品
└── templates/              # 用户自定义模板（覆盖种子）
```

**环境变量**：`PRESALES_HOME` 可覆盖默认路径。

### 路径约定

- `PLUGIN_ROOT` = `${CLAUDE_PLUGIN_ROOT}`（Claude Code 注入）
- `PRESALES_HOME` = 环境变量，默认 `~/.presales/`
- 所有脚本通过 `scripts/ps_paths.py` 解析路径，**禁止硬编码**

### Opportunity 目录契约

```
~/.presales/opportunities/{slug}/
├── meta.yaml               # 基本信息（客户、项目、截止日期、状态）
├── rfp/
│   ├── original/           # 原始招标文件（PDF/Word/扫描件）
│   └── extracted.md        # 文本提取结果
├── analysis/
│   ├── rfp.yaml            # /ps:rfp-parse 产出
│   └── analysis.md         # /ps:rfp-analyze 产出
├── draft/
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

| 文档 | 位置 |
|------|------|
| 架构总览 v0.1 | `docs/design/architecture-v0.1.md` |

## Changelog

见 `CHANGELOG.md`。
