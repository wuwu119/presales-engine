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
- P1 Finding #10（`--force` 未文档化）— 等 #8 一起改
- P1 Finding #11（`--check --format json`）— 独立小改，延后
- P2 全部 14 条 — 留作 v0.2 backlog
- P3 10 条（除去已应用的 2 条）— 留作低优先级
