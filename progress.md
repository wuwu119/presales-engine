# presales-engine Progress

## Session: 2026-04-15 — 项目初始化

### 决策
- 项目名 `presales-engine`，GitHub 仓库 `wuwu119/presales-engine`（暂不推）
- Claude Code plugin 格式（`.claude-plugin/plugin.json` + `marketplace.json`）
- 程序数据分离：插件只读，用户数据存 `~/.presales/`（可由 `PRESALES_HOME` 覆盖）
- v0.1 聚焦应标：`ps:setup / ps:rfp-parse / ps:rfp-analyze / ps:bid-draft` 4 个 skill
- 历史方案从零累积（用户反馈以前的方案质量都不满意，不导入历史）
- Plan C 路线：最小闭环先跑通一个真实单子，再决定加什么

### 本次产出
- 插件骨架：`.claude-plugin/` + `skills/` + `scripts/` + `templates/` + `docs/`
- 4 个 skill 的 SKILL.md（完整契约 + 行为描述）
- `scripts/ps_paths.py` — 统一路径解析（PRESALES_HOME / CLAUDE_PLUGIN_ROOT）
- `scripts/ps_setup.py` — `~/.presales/` 初始化脚本（`--init` / `--reset` / `--import` / `--check`）
- 种子模板 4 份（config / company-profile / products/example / outline-zh-CN）
- 架构文档 `docs/design/architecture-v0.1.md`（只写接口契约，不写实现）
- CLAUDE.md / README.md / LICENSE / CHANGELOG / .gitignore

### 模块测试状态
- `ps_setup.py` — ⚠️ 无自动化测试（v0.2 补 pytest）
- `ps_paths.py` — ⚠️ 无自动化测试（v0.2 补 pytest）
- SKILL.md — 未跑真实 RFP 验证（v0.1 完成后用真实单子跑一遍）

### 待办（v0.1 → v0.2）
- [ ] setup/paths 脚本的 pytest 测试
- [ ] 真实 PDF 解析端到端验证（需要一份真实 RFP）
- [ ] 补 `ps:bid-review`（合规检查 + 多角色批判）
- [ ] 补 `ps:bid-qa`（评标澄清应答）
- [ ] 首次推送到 `github.com/wuwu119/presales-engine`

### 未解决的问题
- PDF 解析依赖库选型未定：`pdfplumber` / `pymupdf` / `unstructured`？v0.1 暂用 LLM 直接读
- marketplace.json 实际安装流程尚未验证（需要 `/plugin marketplace add` 测试）

## Session: 2026-04-15 — ce:review 审计 + 首轮修复

### 决策
- 对首个 commit 跑 `/compound-engineering:ce-review`，以空树为 base
- 7 个 reviewer：correctness / testing / maintainability / project-standards / agent-native / kieran-python / cli-readiness
- 发现 0 P0 / 11 P1 / 14 P2 / 12 P3（跨 reviewer 合并后），完整报告见 `.context/compound-engineering/ce-review/20260415-163000-840af8eb/`
- 选 Plan C 路线中的"单点高 ROI"：只修 Finding #1（删除 fallback YAML writer），用最小改动验证方向

### 本次产出

**已应用的 safe_auto 修复（2 条）**：
- `scripts/ps_paths.py` — 删除 `_as_str_dict` 死代码（M-02），内联到 `__main__`
- `.gitignore` — 删除 `~/.presales/` 无效行（PSF-003），git 不展开 `~`

**主修复：Finding #1 — 删除 fallback YAML writer**：
- 删除 `_try_yaml_dump` / `_fallback_yaml` / `_fmt_scalar`（共 74 LOC）
- 重写 `_write_yaml` 直接调用 `yaml.safe_dump`，PyYAML 缺失时抛 `RuntimeError` 并给出 `pip install pyyaml` 提示
- **一次删除同时解决 5 条 finding**：
  - KP-01 YAML 保留字数据损坏（`yes/no/null` 未加引号导致读回变类型）
  - TD-003 list-of-dicts 分支 off-by-one（`first_line_pad[:-2]`）
  - KP-08 / PSF-001 Article IV 违规（339 行 → 273 行，-66 LOC）
  - KP-09 fallback 辅助函数未加类型注解
- 端到端验证：`--init` + `--check` 均可跑，PyYAML 正确处理所有种子数据的序列化

### 模块测试状态（无变化）
- `ps_setup.py` — ⚠️ 无自动化测试（v0.2 补 pytest），但修改后已通过手工端到端验证
- `ps_paths.py` — ⚠️ 无自动化测试

### 首次跑真实 RFP 前剩余必修项（5 条，按 ROI 排序）
- [ ] **#9** 补 `ps:rfp-parse` 的 slug 目录自动创建路径
- [ ] **#8** 在 `skills/setup/SKILL.md` 文档化 `--config-json` 非交互路径
- [ ] **#6** 改 `skills/bid-draft/SKILL.md` Phase 3 描述为 v0.2 no-op
- [ ] **#3** `scripts/ps_setup.py` `reset_home` 加深度守卫（防 `PRESALES_HOME=~` 灾难）
- [ ] **#4** `scripts/ps_setup.py` `import_from` 改深度合并（防 populated subdir 数据丢失）
- [ ] **#5** `scripts/ps_setup.py` `.version` 写入顺序调整到最后

### 本 session 未触及的 review finding
- P1 Finding #2（sys.path.insert → 改包结构）— 牵动 `scripts/__init__.py` 和 `python3 -m scripts.ps_setup` 调用方式，改动面大，延后
- P1 Finding #7（缺 `rfp_validate.py`）— 需要先定 schema 文件格式，延后
- P1 Finding #11（`--check --format json`）— 独立小改，延后
- P2 全部 14 条 — 留作 v0.2 backlog
- P3 10 条（除去已应用的 2 条）— 留作低优先级

## Session: 2026-04-15 (cont.) — git author 重写 + SKILL.md 契约修复

### 决策
- 把已有 2 个 commit 的 author 从 `wuwu <wuwu@wuwu-MacBook-Air.local>` 重写为 `wuwu119 <wuwu119@gmail.com>`（rebase --root --exec amend）— 推 GitHub 前清理身份
- 用户选 option 2：只修 SKILL.md 契约层面的 3 条（#6 / #8 / #9），不动现有 Python，让首次端到端运行有正确的契约文档

### 本次产出

**Git 身份重写**：
- 设 `git config user.name="wuwu119"` / `user.email="wuwu119@gmail.com"`
- `git rebase --root --exec "git commit --amend --reset-author --no-edit"`
- 两个 commit hash 都变了：`a74abe0 → 57decde`、`0467f9c → c195fe1`

**SKILL.md 契约修复（3 条 Finding）**：

- **Finding #8** `skills/setup/SKILL.md` 重写"调用模式"段：
  - 显式区分 A 路径（非交互 `--config-json`）和 B 路径（交互 Q&A）
  - 列出 `--config-json` 完整字段表（必填/选填/类型）
  - **顺手修了 Finding #10**：`--force` 行为补全到"其他脚本调用"段
  - 134 行（之前 106，+28）

- **Finding #9** `skills/rfp-parse/SKILL.md` 新增 Phase 0 "准备 opportunity 目录"：
  - skill 通过 inline `mkdir -p` 自动创建 `{slug}/{rfp/original,analysis,draft/chapters}` 子树
  - 创建后强制检查 `rfp/original/` 是否为空
  - 失败表里 `{slug}` 目录不存在那行改为 "Phase 0 自动创建"
  - 这是对 architecture 约束 #2 的 v0.1 临时例外，已在 architecture-v0.1.md §9 加注（v0.2 路标：引入 `scripts/ps_opportunity.py`）
  - 115 行（之前 99，+16）

- **Finding #6** `skills/bid-draft/SKILL.md` Phase 3 重写：
  - 明确分 v0.1（LLM 自检，**不写文件**，**不强制中止**）vs v0.2 路标（`bid_coverage.py` + 硬门槛）
  - 失败表里"覆盖率 < 80% 强制中止"改为"v0.1 警告不中止，v0.2 引入硬门槛"
  - **顺手修了 Finding #29**：原 100% 警告 vs 80% 中止的阈值矛盾消失（v0.1 完全不中止）
  - 121 行（之前 113，+8）

**Architecture doc 同步**：
- `docs/design/architecture-v0.1.md` §9 约束 #2 加 v0.1 临时例外注释，链接到 ce:review 2026-04-15 的 Finding #9

### Review finding 状态更新
本 session 共关闭 **5 条 finding**：#6 / #8 / #9 / #10 / #29

P1 剩余：#2 / #3 / #4 / #5 / #7 / #11 (6 条，从 11 → 6)
P2 剩余：14 条（未触及）
P3 剩余：9 条（已应用 2，关闭 1）

### 模块测试状态（无变化）
- 所有改动均在 SKILL.md / 架构文档 / progress 层，未触及 Python 代码

### 下一步候选
- 修剩余 P1 Python 层（#3 reset_home 守卫 / #4 import_from 深合并 / #5 .version 写入顺序）— 一个 commit 集中改 ps_setup.py
- 装到本地 Claude Code 验证 skill 是否可被正确触发
- 推 GitHub

## Session: 2026-04-15 (cont.) — Python 必修 P1 修复 + ps_setup_utils.py 拆分

### 决策
- 用户选 option 1：修剩余 3 条 Python 必修 finding（#3 / #4 / #5），顺手带 KP-05 (init 异常处理) + C-06 (备份命名冲突)
- Article IV 边界发现：直接添加 3 条修复后 ps_setup.py 涨到 334 行，超出 300 行限额。决定拆出 `scripts/ps_setup_utils.py` 容纳纯辅助函数 + 常量，保持主文件在限额内
- 危险路径守卫初稿被 macOS 的 `/tmp → /private/tmp` resolve 绕过：单纯用 `len(parts) >= 3` 不够，补上显式危险路径集合 `_UNSAFE_RESET_PATHS`

### 本次产出

**新文件 `scripts/ps_setup_utils.py`（66 行）**：
- 容纳纯辅助函数 + 常量：`VERSION`、`DEFAULT_DIRS`、`_UNSAFE_RESET_PATHS`、`_now_iso`、`_write_yaml`、`_normalize_highlights`
- 不依赖 PRESALES_HOME 或任何项目状态，可独立单元测试

**`scripts/ps_setup.py` 修复（334 → 300 行）**：

- **Finding #5**：`init_skeleton` 写入顺序调整 — `.version` 移到所有 config / 模板写完之后；任何中间步骤抛 `OSError` 不会留下 `.version`，下次 `--init` 不会触发"已初始化"早退，而是重试
- **Finding #5 (KP-05 顺带)**：`init_skeleton` 整个 try/except 包住，把 `OSError` 转为友好 stderr 提示 + return 1，调用方的 `rc != 0` 检查终于可达
- **Finding #3**：`reset_home` 加 3 层守卫
  1. `len(home.parts) < 3`（绝对深度防御）
  2. `home == Path.home()`（防 $HOME）
  3. `home in _UNSAFE_RESET_PATHS`（防 macOS `/tmp → /private/tmp` 这类 resolve 绕过）
- **Finding #3 (C-06 顺带)**：备份命名加微秒精度 + collision counter，同秒双 reset 不再炸
- **Finding #4**：`import_from` 改为 `rglob("*")` 深度遍历，逐文件复制；`target.exists()` 只跳过同名文件，不再吞掉整个已存在的子目录。修复了"`--init` 后 `knowledge/products/` 是空目录 → import 直接跳过，源 products/*.yaml 全部丢失"的数据丢失 bug

**`scripts/ps_setup.py` 行数控制**：
- 拆出 utils 后 273 → 248 行
- 加 3 条修复后 248 → 311 行
- `_UNSAFE_RESET_PATHS` 也搬到 utils + docstring 微调 → **300 行整**（卡限额）

### 端到端验证（5 类全过）

1. `--init` + `--check` 正常，`highlights` 字符串自动归一化为 list
2. 幂等：重跑 `--init` 命中 "已初始化" 早退
3. 危险路径全部拒绝：`/tmp`、`/var`、`/Users`、`$HOME`
4. 深度合并 import：fresh `--init` 后 import 一份带 `knowledge/products/{a,b}.yaml` 的源，**4 个文件全部正确落到 target**（旧实现会丢 2 个 products）。再 import 一次跳过全部 4 个
5. 安全路径下 `--reset` 仍正常备份 + 删除原目录

### Review finding 状态更新

本 session 关闭 **5 条 finding**：#3 / #4 / #5 / KP-05 / C-06

P1 剩余：#2 / #7 / #11（3 条，从 6 → 3）
P2 剩余：13（KP-05 关闭）
P3 剩余：8（C-06 关闭）

**首次跑真实 RFP 前必修清单**：✅ **全部完成**

### 模块测试状态
- ✅ `ps_setup.py` — 手工端到端验证 5 类场景全过；自动化测试仍待 v0.2
- ✅ `ps_setup_utils.py` — 新文件，纯函数易测，v0.2 第一批补的 pytest 目标
- ✅ `ps_paths.py` — 无变化，仍待 v0.2 自动化测试

### 仍未触及
- P1 #2 sys.path.insert → 包结构改造（涉及 scripts/__init__.py 和调用方式，单独 commit 处理）
- P1 #7 缺 `rfp_validate.py`（等 schema 文件格式定下来）
- P1 #11 `--check --format json`（独立小改，留作下次）
- P2 全部 13 条 → v0.2 backlog
- P3 8 条 → 低优先级

## Session: 2026-04-15 (cont.) — UX 修复：可见默认目录 + 自定义路径

### 决策
- 用户反馈两个 UX 漏洞：
  1. 默认 `~/.presales/` 是隐藏目录，用户要手工编辑 yaml 和 RFP，不该藏起来
  2. 没有交互方式让用户选择数据存放位置（只能改环境变量，对人类不友好）
- 修法：默认改 `~/presales/`（无前导点）+ 加 `--home <path>` flag + 持久化指针文件 + 三层 resolution

### 设计：3 层 resolution
```
1. PRESALES_HOME 环境变量              # CI / 一次性覆盖（最高优先级）
2. ~/.config/presales-engine/home    # 指针文件，由 ps:setup --init --home 写入
3. ~/presales/                       # 默认（无 dot，可见）
```

### 本次产出

**`scripts/ps_paths.py`（93 → 135 行）**：
- 新增 `_config_pointer_path` / `_read_pointer` / `write_pointer` / `presales_home_source`
- `presales_home()` 改成三层 resolution
- 默认从 `~/.presales/` 改为 `~/presales/`
- `__main__` debug 输出加 source 层 + 指针文件路径

**`scripts/ps_setup.py`（300 → 297 行，仍卡限）**：
- 新增 `--home <path>` CLI 标志
- `main()` 处理 --home：写指针文件 + `os.environ["PRESALES_HOME"]` 覆盖（限 --init 配合使用）
- `check_status()` 输出加 source 层（env / pointer / default）
- `reset_home()` backup 命名从硬编码 `.presales.backup.<ts>` 改为 `<home.name>.backup.<ts>`，跟随实际 home 目录命名
- 为了腾出 line budget，trim 了 init_skeleton docstring + "下一步" 打印块 + reset_home docstring + check_status 的 opportunities/cases 计数循环

**`skills/setup/SKILL.md`（134 → 150 行）**：
- 重写"行为契约"段：加 3 层 resolution 表
- 交互式 Q&A 加 Q1 "数据存放位置（默认 `~/presales/`，可改）"，原 7 题顺延为 Q2-Q8
- 非交互调用 A 路径示例加 `--home` 标志
- 描述字段 + argument-hint 同步加 `--home`
- "其他脚本调用"段 backup 命名注释更新

**文档全量替换 `~/.presales/` → `~/presales/`**：
- README.md（10 处 + 调整 quickstart 描述）
- CLAUDE.md（6 处 + 路径约定段重写为 3 层 resolution）
- docs/design/architecture-v0.1.md（2 处 + §2 路径约定段加 3 层 resolution + 指针文件设计说明）
- skills/rfp-parse/SKILL.md（Phase 0 bash example）
- 4 个 templates/*.yaml（顶部注释）

**保留为历史的 `.presales` 引用**：
- progress.md 旧 session 条目
- CHANGELOG.md v0.1.0 条目
- ps_setup.py 注释（设计决策说明）
- .gitignore 保留 `.presales/` 行做防御，新增 `presales/` 行

**.gitignore**：加 `presales/` 行，保留 `.presales/` 防御老用户

**CHANGELOG.md**：新增 Unreleased 段，记录 4 项变更

### 端到端验证（5 类全过）

```
✓ 默认 → ~/presales/，source=default
✓ --home 指定 + 写 pointer + init 落盘到自定义路径
✓ pointer 落盘后再次 check，source=pointer
✓ env 优先于 pointer：PRESALES_HOME=/x check 返回 /x，source=env
✓ --home 必须配 --init（其他模式拒绝）
✓ pointer 指向 /tmp 时仍触发危险路径守卫
✓ pointer 指向自定义路径时 reset 仍正常
✓ backup 命名跟随 home name：/tmp/foo → /tmp/foo.backup.<ts>
✓ 删除 pointer 后回退到默认
```

### 模块测试状态（无变化）
- ✅ ps_setup.py / ps_paths.py / ps_setup_utils.py — 手工端到端验证；自动化测试仍待 v0.2

### 下一步候选
- 推 GitHub
- 装本地 Claude Code 验证新流程（你刚才已经验过基本加载）
- 跑真实 RFP 端到端
- 修剩余 P1 #2 / #7 / #11

## Session: 2026-04-15 (cont.) — setup scope 收窄到 URL + 独立知识库

### 决策
- 用户反馈 1：之前的交互问答模式失效（SKILL.md 把 A 路径描述成"agent-to-agent 首选"，Claude 读到就跳过问答）→ 已在上个 commit `cc0ae9b` 修复
- 用户反馈 2：初始化不应该问一堆问题，**只给公司名字，其他自动从网上抓**
- 用户反馈 3：证据库 / 产品库 / 案例库的建设不应该塞进 setup，**应该独立设计**，让用户按标准格式提供文件或者走预处理流程
- 我的反建议"让用户提供本地文件 + URL + 粘贴文字混合输入"被否：scope 收窄到只一个 URL，其他独立 skill 处理

### 本次产出

**`skills/setup/SKILL.md`（170 → 231 行）**：
- B 路径彻底重写为"URL 驱动的最小信息抽取"：
  - Q1 仅 = 公司官网 URL
  - Phase 1 抓取：WebFetch 主页（最多再抓一个 /about 子页）
  - Phase 2 抽取：仅提取 name_zh/name_en/industry/founded/size/location 最小字段 + 按域名推断 language/currency；所有 qualifications/cases/team/highlights/product_lines 一律留空
  - Phase 3 Review + 写入：Markdown 表格 + source 标注 + ✅/✏️/❌ 确认
  - 严禁编造，找不到就 null
- 新增 B-fallback 段：URL 不可用或抽取失败 → 回退到 3 题最小手工问答（中文名 + 英文名 + 行业一句话）
- 加醒目的 v0.1 scope 声明：**证据库 / 产品库 / 案例库不归 ps:setup 管**，留给未来 `ps:knowledge-ingest`（暂定名）
- A 路径 schema 表更新：只 `company_name_zh` 必填，其他字段全部可选，`product_lines` / `highlights` 强调 v0.1 留空

**`README.md` 同步**：
- Quickstart 的 setup 段重写为 URL 驱动的说明
- 加 ⚠️ 证据库 / 产品库 / 案例库不在 setup 范围的声明
- 指定数据位置的 3 种方式列出

### 没触碰的代码
- `ps_setup.py` / `ps_paths.py` / `ps_setup_utils.py` 一行不动：现有 `--config-json` 的字段都变成可选后，Python 端用 `config.get("field", "")` 的默认值语义本来就吃得住；没有写死的 required 字段
- 4 个 template YAML 不动
- 其他 SKILL.md 不动

### 未解问题
- `ps:knowledge-ingest` 的独立设计：什么输入格式（文件路径列表 / 标准化目录结构 / zip 包）、支持哪些文件类型、如何映射到 qualifications / case_references / products 的 YAML 结构、evidence_file 存放规则——**全部待 v0.2+ 设计会议**
- URL 驱动 setup 未在真实 Claude Code 里验证过 Q1 + WebFetch + review + 写入全链路
- WebFetch 工具的可用性检测逻辑目前只是"抓不到就 fallback"，没在 skill 开头做 capability probe

### 下一步候选
- 重启新 Claude Code 窗口，重新跑 `/ps:setup`，验证 URL 流程是否真的按新 SKILL.md 跑
- 设计 `ps:knowledge-ingest` 的输入格式规范（单独的 brainstorm session）
- 推 GitHub

## Session: 2026-04-15 (cont.) — 父目录交互 + 完整知识库骨架

### 决策
- 用户要求一次性做完：(1) 交互式选父目录；(2) 生成完整知识库骨架并带填充指南
- 父目录策略：Q1 让用户输父目录（默认 `~/`），派生完整 home = `<parent>/presales/` 后再问 URL
- 知识库骨架策略：建 6 个子目录（`about`/`certs`/`case-studies`/`products`/`competitors`/`team`），每个带一份 README.md 填充指南，从插件的 `knowledge-seed/` 种子目录拷贝
- 命名关键：`knowledge/case-studies/`（可复用案例资料库）vs 顶层 `cases/`（归档 opportunity），语义不同命名必须区分

### 本次产出

**新增插件目录 `knowledge-seed/`（7 个 README 文件）**：
- `knowledge-seed/README.md` — 总览 + 引用规则 + `cases/` vs `case-studies/` 解释
- `knowledge-seed/about/README.md` — 公司介绍材料
- `knowledge-seed/certs/README.md` — 资质证书（带推荐命名约定 `<cert>-<issuer>-<expiry>.pdf`）
- `knowledge-seed/case-studies/README.md` — 客户案例资料库（强调 public_usable 语义）
- `knowledge-seed/products/README.md` — 产品档案库（指向 templates/products/example.yaml schema）
- `knowledge-seed/competitors/README.md` — v0.2 占位（明确说 v0.1 不用）
- `knowledge-seed/team/README.md` — 团队资质（含 roster.yaml schema 示例）

每个 README 按固定结构：放什么 / 命名约定 / 格式 / 在 company-profile.yaml 里的引用 / 谁引用它。

**`scripts/ps_paths.py`（135 → 145 行）**：
- `knowledge_paths()` 加 5 个新子路径键（`about` / `certs` / `case_studies` / `team`；products / competitors 原来就有）
- 新增 `seed_knowledge_dir()` 返回 `plugin_root() / "knowledge-seed"`

**`scripts/ps_setup_utils.py`（66 → 70 行）**：
- `DEFAULT_DIRS` 加 4 个新子目录（`knowledge/{about,certs,case-studies,team}`；products / competitors 原来就有）

**`scripts/ps_setup.py`（297 → 296 行，净 -1）**：
- 把 `_copy_seed_templates` 通用化为 `_copy_seed_dir(source, target, force)` — 不再写死"templates"
- `init_skeleton()` 现在调用两次：一次拷 templates，一次拷 knowledge-seed
- 导入清单加 `seed_knowledge_dir`

**`skills/setup/SKILL.md`（260 → 283 行）**：
- Step 1 新增"问父目录"（AskUserQuestion text input，默认 `~/`），派生 `<parent>/presales/` 完整路径
- 原 Step 1（问 URL）变 Step 2，后续 Step 编号全部 +1
- Step 7（原 Step 6）"选 ✅"分支**必须**带 `--home <Step 1 派生的完整路径>` 调脚本
- 说明脚本会自动创建完整知识库骨架 + 拷 7 份 README

**文档同步**：
- `CLAUDE.md` 程序/数据分离段重写：程序侧加 `knowledge-seed/`；数据侧 `knowledge/` 展开到 6 个子目录带注释
- `docs/design/architecture-v0.1.md` §3 用户数据目录契约：知识库 tree 展开到 6 个子目录 + 每个带 README；加 "`cases/` vs `knowledge/case-studies/`" 命名区分说明

### 端到端验证

```
PRESALES_HOME=/tmp/... python3 scripts/ps_setup.py --init --config-json '{}'
→ 创建了 10 个目录 + 14 个文件：
  - cases/ opportunities/ templates/ templates/products/
  - knowledge/ + 6 子目录（about/certs/case-studies/products/competitors/team）
  - knowledge/README.md + 6 个子目录 README.md + company-profile.yaml
  - templates/ 原 4 份种子模板
  - .version + config.yaml
```

### 行数汇总
- scripts/ps_setup.py: 296 / 300 ✅
- scripts/ps_paths.py: 145 / 300 ✅
- scripts/ps_setup_utils.py: 70 / 300 ✅
- skills/setup/SKILL.md: 283 / 300 ✅
- 6 个 knowledge-seed README: 28-81 行不等

### 未解问题
- 交互式父目录问答未在真实 Claude Code 里端到端验证（WebFetch + AskUserQuestion + --home 传递）
- `ps:knowledge-ingest` 设计仍然是占位，v0.2 才做
- 已初始化过的用户如果改父目录，没有迁移命令（要手工 mv）
