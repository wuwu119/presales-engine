---
name: ps:setup
description: 初始化 presales-engine 用户数据目录。首次使用必须运行，默认在 ~/presales/ 创建骨架、config.yaml 和种子模板，支持 --home 指定其他位置。支持 --reset 重置和 --import 从旧数据目录导入。当用户说"初始化售前"、"ps setup"、"presales 初始化"、"配置 presales-engine"时触发。
argument-hint: "[--home <path>] [--reset] [--import <path>] [--check]"
---

# ps:setup — 初始化用户数据目录

## 何时运行

- 首次安装插件后
- 升级插件大版本后（检测 `.version` 差异）
- 用户要求重置数据目录（`--reset`）
- 用户想迁移数据（`--import <old-path>`）

## 行为契约

1. 解析数据目录路径（三层 resolution，顺序见下）
2. 根据场景分支：
   - `--check`：只打印当前状态，不做任何修改
   - `--reset`：二次确认 → 调用脚本备份旧目录 → 重新创建
   - `--import <path>`：先确保已 init，再从指定路径复制数据
   - 默认：若目录已存在且 `.version` 匹配 → 提示"已初始化"直接退出；否则进入交互式问答 → `--init`
3. 所有文件系统操作**必须**通过 `scripts/ps_setup.py`，禁止在 skill 内手写 `mkdir` 或 `cat >`

### 数据目录路径 resolution（3 层）

| 优先级 | 来源 | 用途 |
|--------|------|------|
| 1 (最高) | 环境变量 `PRESALES_HOME` | CI / 一次性覆盖 / 高级用户 |
| 2 | 指针文件 `~/.config/presales-engine/home` | 由 `ps:setup --home <path>` 持久化 |
| 3 (默认) | `~/presales/` | **可见目录**，方便用户手工编辑 |

`--home <path>` 标志会写入指针文件并对当前 init 生效。后续所有 skill 自动遵循。

## 调用模式

**默认走交互问答（路径 B），除非配置已被显式提供。**

判断规则（**严格按此执行，不要凭"我是 agent"自行优化掉问答**）：

| 触发条件 | 走哪条路径 |
|---------|-----------|
| 用户直接输入 `/ps:setup` 或自然语言"初始化 presales-engine"，**没有**附带 JSON 配置或 `--config-json` 参数 | **B（交互问答）** ← 99% 的情况 |
| 用户明确在请求里贴了配置 JSON（例如"用这个 config 初始化：{...}"） | A（非交互） |
| 另一个 skill 程序化调用 `ps:setup`，带完整 config 参数 | A（非交互） |
| CI / shell 脚本直接调用 `python3 ps_setup.py --init --config-json '...'` | A（非交互），不经过 skill 层 |

**关键**：Claude 自身是 agent 不构成走 A 路径的理由。只有"配置已被显式提供"才走 A。如果用户什么都没说就让你 setup，**必须**走 B 把问题问完。

### B. 交互路径（默认）

> **交互工具硬性约束**：所有用户输入**必须**通过平台的 `AskUserQuestion` 工具（Claude Code 原生）或等效工具。**禁止**在对话里写"请选择：1. X / 2. Y / 3. Z"这种文本式选单让用户手打回复——那不是交互对话，是聊天机器人式的退化。每一次需要用户决策的地方都走 `AskUserQuestion`。

#### Step 1：问父目录

调用 `AskUserQuestion`：
- `question`: "presales workspace 放在哪个父目录下？（将在此目录创建 `presales/` 子目录，默认 `~/`）"
- `input_type`: text / free-form，默认值 `~/`

派生完整路径：`<parent>/presales/`。展开 `~/` 为绝对路径。例：
- 用户输 `~/` → home = `/Users/<you>/presales`
- 用户输 `~/Documents/` → home = `/Users/<you>/Documents/presales`
- 用户输 `/Users/<you>/work/` → home = `/Users/<you>/work/presales`

拿到派生 home 后，直接告诉用户"workspace 将建在 `<derived-home>`"，然后进入 Step 2（**不**问确认，减少问答数）。

#### Step 2：问 URL

调用 `AskUserQuestion`：
- `question`: "请提供公司官网 URL（例如 `https://example.com`）"
- `input_type`: text / free-form

#### Step 3：抓取（Phase 1）

用 `WebFetch` 抓取用户给的 URL。如果主页首屏信息不足（纯 SPA / 只有 logo），**最多再抓一个** `/about` 或 `/company` 子页。**禁止深爬**。

#### Step 4：抽取最小字段（Phase 2）

从抓到的 HTML / Markdown 内容里，**只**抽取这些字段：

| 字段 | 来源线索 |
|------|----------|
| `company.name_zh` / `name_en` | `<title>`、`og:site_name`、首屏 logo 文本、版权行 |
| `company.industry` | meta description、slogan，一句话推断 |
| `company.founded` | "成立于 YYYY" / "Since YYYY" / "About us" 段落 |
| `company.size` | "X 名员工" / "X+ employees"（数字或区间） |
| `company.location` | footer / Contact 页的地址 |
| 一句话简介 | meta description 或首屏一行文案 |
| `preferences.language` / `currency` | 按域名推断：`.cn` 或中文内容 → `zh-CN` / `CNY`；`.com` 英文内容 → `en` / `USD`；不确定默认 `zh-CN` / `CNY` |

**硬性规则**：

1. **严禁编造**：页面没有明确文字的字段一律 `null`。
2. **以下字段 v0.1 setup 永远留空**（绝对规则，无例外，即使页面上有）：
   - `qualifications[]`
   - `case_references[]`
   - `team[]`
   - `highlights[]`
   - `company.product_lines[]`
   - 这些字段的建设不归 setup 管，留给未来独立的知识库构建流程

#### Step 5：展示 Review 表格（Phase 3 前半）

用**一个紧凑的 Markdown 表格**展示抽取结果，禁止一个字段一个字段 dump。格式必须长这样：

```markdown
| 字段 | 值 | 来源 |
|------|-----|------|
| 中文名 | 奇安信 | `<title>` |
| 英文名 | Qianxin | `og:site_name` |
| 行业 | 网络安全 | meta description |
| 成立年份 | 2014 | About us 页 |
| 总部 | 北京 | footer |
| 员工规模 | null | — |
| 一句话简介 | 新一代网络安全领军者 | hero slogan |
| 语言 / 货币 | zh-CN / CNY | 域名 .cn + 中文内容 |
```

未识别的字段值显示为 `null`，来源列显示为 `—`。所有 Markdown 代码块输出给用户一次看完。

#### Step 6：用 `AskUserQuestion` 要确认（Phase 3 后半）

表格之后**立刻**调用 `AskUserQuestion`：
- `question`: "以上信息是否正确？"
- options（single-select，required）：
  - ✅ **全部接受** — 直接写入
  - ✏️ **修改某项** — 下一步再选改哪个字段
  - ❌ **全部丢弃** — 走 fallback 最小手工问答

**禁止直接输出 "请选择：1/2/3" 让用户打字回复。必须走 `AskUserQuestion` 让用户点选。**

#### Step 7：按用户选择分叉

**选 ✅**：调用脚本写入，**必须**带上 Step 1 派生的 `--home`：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" \
  --init \
  --home <Step 1 派生的完整路径> \
  --config-json '{"company_name_zh":"...","company_name_en":"...","industry":"...","language":"zh-CN","currency":"CNY"}'
```

脚本会自动创建完整的知识库骨架（`knowledge/{about,certs,case-studies,products,competitors,team}/` 各带 README.md 填充指南），并把 Step 1 的路径持久化到 `~/.config/presales-engine/home` 指针文件。

**选 ✏️**：再调用 `AskUserQuestion`：
- `question`: "要修改哪个字段？"
- options: 列出 Step 5 表格里所有字段作为 single-select 选项
- 用户选中字段后，再调一次 `AskUserQuestion` 问新值（text input）
- 把修正合并进抽取结果，**返回 Step 5 重新展示表格** + Step 6 再问一次是否确认
- 循环直到用户选 ✅ 或 ❌

**选 ❌**：进 B-fallback 段。

**选 ✏️**：再调用 `AskUserQuestion`：
- `question`: "要修改哪个字段？"
- options: 列出 Step 4 表格里所有字段作为 single-select 选项
- 用户选中字段后，再调一次 `AskUserQuestion` 问新值（text input）
- 把修正合并进抽取结果，**返回 Step 4 重新展示表格** + Step 5 再问一次是否确认
- 循环直到用户选 ✅ 或 ❌

**选 ❌**：进 B-fallback 段。

### B-fallback：URL 不可用或抽取失败

触发条件：
- `WebFetch` 工具不可用
- URL 返回 4xx / 5xx / 超时
- 抓到 HTML 但关键字段都提取不到（例如纯 JS 渲染的 SPA）
- 用户在 review 阶段选 ❌

回退到**最小手工问答**（3 题），**每题都通过 `AskUserQuestion` 一题一问**，禁止文本式 "请回答以下 3 个问题："：

1. `AskUserQuestion`：`"公司中文名称"`（text input，必填）
2. `AskUserQuestion`：`"公司英文名称（可跳过）"`（text input，可选）
3. `AskUserQuestion`：`"所在行业（一句话描述）"`（text input，必填）

收集完后组装成 `--config-json` 调用脚本，默认 `language=zh-CN` / `currency=CNY`，其他字段全部留空。用户后续可手工编辑 `~/presales/knowledge/company-profile.yaml` 补充。

---

> ⚠️ **证据库 / 产品库 / 案例库的构建不归 `ps:setup` 管**
>
> `company-profile.yaml` 里的 `qualifications[]` / `case_references[]` / `team[]` 字段，以及 `knowledge/products/*.yaml` 需要基于真实文件证据（ISO 证书 PDF、案例 PPT、产品手册等）建立。
> v0.1 的 setup **只写基础公司信息**，这些高价值字段留空。
> 未来版本会引入独立的 `ps:knowledge-ingest`（暂定名）skill，让用户按标准格式提供证据文件，预处理成标准化的知识库条目。设计待定。

### A. 非交互路径（仅当配置已被提供）

调用形式：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" \
  --init \
  --home /Users/<you>/presales \
  --config-json '{"company_name_zh":"...","industry":"...",...}'
```

`--home` 可省略（默认 `~/presales/`），脚本按 3 层 resolution 解析。

**`--config-json` 字段约定**（B 路径组装时也按此 schema）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `company_name_zh` | string | ✅ | 公司中文名 |
| `company_name_en` | string | ❌ | 公司英文名 |
| `industry` | string | ❌ | 行业描述（一句话，自由文本） |
| `product_lines` | string[] | ❌ | 产品线列表。v0.1 默认留空，留给独立知识库流程 |
| `language` | string | ❌ | `zh-CN` / `en`，默认 `zh-CN` |
| `currency` | string | ❌ | `CNY` / `USD` / `EUR`，默认 `CNY` |
| `highlights` | string[] | ❌ | v0.1 默认留空 |

未列出的字段会被忽略。`highlights` 接受 string 或 string[]，scalar 会被强制归一化为单元素 list。

**v0.1 设计原则**：config-json 字段一律宽松，除 `company_name_zh` 外全部可选；缺失字段自动补默认值或 null。填充 `qualifications` / `case_references` / `team` 等深度字段应走未来的独立知识库 skill，不经过本脚本。

## 其他脚本调用

```bash
# 检查状态（输出包含 source 层：env / pointer / default）
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --check

# 重置（备份到 <home>.backup.<timestamp>，命名跟随 home dir 名）
# ⚠️ v0.1 无 --yes 标志，agent 调用前必须二次确认
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --reset

# 从旧目录导入（深度合并，文件级跳过已存在）
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --import /path/to/old-presales

# 强制覆盖已存在的 config.yaml / company-profile.yaml（迁移或修复用）
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --init --config-json '<json>' --force
```

`--home` 只能与 `--init` 一起使用。`--reset` / `--import` / `--check` 都基于当前 resolution 解析的 home。

`--force` 行为：
- 不带：`config.yaml` / `company-profile.yaml` 已存在则跳过写入（保护用户已编辑的内容）
- 带：覆盖所有种子文件，**不备份**（用户已经手工编辑的字段会被丢弃）

## 产出

执行成功后，`${PRESALES_HOME}/` 应包含：

```
${PRESALES_HOME}/
├── .version                    # 插件版本号
├── config.yaml                 # 由交互式问答填充
├── opportunities/              # 空目录
├── cases/                      # 空目录
├── knowledge/
│   ├── company-profile.yaml    # 由交互式问答填充
│   ├── products/               # 含种子 products/example.yaml
│   └── competitors/            # 空目录
└── templates/                  # 含种子 outline-zh-CN.yaml 等
```

## 约束

- **禁止在 skill 内用 `mkdir`、`cat >`、`echo >`** — 所有文件系统操作走脚本
- **禁止把用户数据写到插件目录** — 只能写 `PRESALES_HOME`
- **禁止未经确认覆盖已有文件** — 除非 `--reset` 明确指定
- **幂等** — 重复执行默认不应产生副作用

## 失败处理

| 情况 | 处理 |
|------|------|
| 无写权限 | 报错 + 提示检查目录权限 |
| 磁盘空间不足 | 报错 + 建议清理 |
| `--import` 源目录不存在 | 报错 + 列出期望路径 |
| `--reset` 未二次确认 | 中止，不做任何改动 |
| `--init` 时用户中途退出问答 | 不写任何文件，下次重跑 |

## 后续步骤提示

setup 成功后必须输出：

> ✅ 已初始化到 `${PRESALES_HOME}`。
>
> 下一步：
> 1. 把 RFP 文件放到 `${PRESALES_HOME}/opportunities/<项目名>/rfp/original/`
> 2. 运行 `/ps:rfp-parse <项目名>` 解析
> 3. 按需补充 `${PRESALES_HOME}/knowledge/company-profile.yaml`（案例、资质、团队）
