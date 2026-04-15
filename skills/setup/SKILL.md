---
name: ps:setup
description: 初始化 presales-engine 用户数据目录。首次使用必须运行，创建 ~/.presales/ 骨架、config.yaml 和种子模板。支持 --reset 重置和 --import 从旧数据目录导入。当用户说"初始化售前"、"ps setup"、"presales 初始化"、"配置 presales-engine"时触发。
argument-hint: "[--reset] [--import <path>] [--check]"
---

# ps:setup — 初始化用户数据目录

## 何时运行

- 首次安装插件后
- 升级插件大版本后（检测 `.version` 差异）
- 用户要求重置数据目录（`--reset`）
- 用户想迁移数据（`--import <old-path>`）

## 行为契约

1. 解析 `PRESALES_HOME`（默认 `~/.presales/`）
2. 根据场景分支：
   - `--check`：只打印当前状态，不做任何修改
   - `--reset`：二次确认 → 调用脚本备份旧目录 → 重新创建
   - `--import <path>`：先确保已 init，再从指定路径复制数据
   - 默认：若目录已存在且 `.version` 匹配 → 提示"已初始化"直接退出；否则进入交互式问答 → `--init`
3. 所有文件系统操作**必须**通过 `scripts/ps_setup.py`，禁止在 skill 内手写 `mkdir` 或 `cat >`

## 调用模式

`ps:setup` 有两条等价路径，按调用上下文选择：

### A. 非交互路径（CI / 程序化 / 已知配置）

直接调用脚本，把配置作为 JSON 字符串传入，跳过 Q&A。这是 agent-to-agent 调用的首选：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" \
  --init \
  --config-json '{"company_name_zh":"...","industry":"IT 服务",...}'
```

**`--config-json` 字段约定**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `company_name_zh` | string | ✅ | 公司中文名 |
| `company_name_en` | string | ❌ | 公司英文名 |
| `industry` | string | ✅ | 行业（IT 服务 / 软件产品 / 硬件集成 / 咨询 / 其他） |
| `product_lines` | string[] | ✅ | 产品线列表，至少 1 项 |
| `language` | string | ✅ | `zh-CN` 或 `en` |
| `currency` | string | ✅ | `CNY` / `USD` / `EUR` / 其他 |
| `highlights` | string[] | ❌ | 公司能力亮点列表 |

未列出的字段会被忽略。`highlights` 接受 string 或 string[]，scalar 会被强制归一化为单元素 list。

### B. 交互路径（人类首次安装）

用平台的 `AskUserQuestion`（或等效工具）一次问一个问题，优先单选，必要时才自由输入：

| 序 | 问题 | 类型 | 必填 |
|----|------|------|------|
| 1 | 公司中文名称 | 文本 | ✅ |
| 2 | 公司英文名称 | 文本 | ❌ |
| 3 | 所在行业 | 单选：IT 服务 / 软件产品 / 硬件集成 / 咨询 / 其他 | ✅ |
| 4 | 主要产品线（自由输入，逗号分隔） | 文本 | ✅ |
| 5 | 默认语言 | 单选：zh-CN / en | ✅ |
| 6 | 默认货币 | 单选：CNY / USD / EUR / 其他 | ✅ |
| 7 | 公司能力亮点（一段话，可跳过） | 文本 | ❌ |

收集完毕后组装成 `--config-json` 走 A 路径调用脚本。**禁止在 skill 内手写 `mkdir` 或 `cat >`**。

## 其他脚本调用

```bash
# 检查状态（人类可读 prose；--format json 见 v0.2 路标）
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --check

# 重置（脚本内部会备份到 ~/.presales.backup.<timestamp>）
# ⚠️ v0.1 无 --yes 标志，agent 调用前必须二次确认
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --reset

# 从旧目录导入
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --import /path/to/old-presales

# 强制覆盖已存在的 config.yaml / company-profile.yaml（迁移或修复用）
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ps_setup.py" --init --config-json '<json>' --force
```

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
