---
name: ps:knowledge-ingest
description: 把知识库材料结构化入库。支持 certs（资质证书→company-profile.yaml）和 products（产品材料→产品档案/{slug}/）两种类型。当用户说"入库证书"、"入库产品"、"knowledge ingest"时触发。
argument-hint: "certs | products --source <材料目录>"
---

# ps:knowledge-ingest

## 类型路由

| 参数 | 触发 | 流程 |
|------|------|------|
| `certs` | 入库证书、登记资质 | → Certs 流程（下方） |
| `products --source <路径>` | 入库产品、产品入库 | → Products 流程（下方） |

---

## Certs 流程 — 资质证书入库

### 前置条件

- `ps:setup` 已执行，`${PRESALES_HOME}/知识库/资质证书/` 存在
- 用户已把证书 PDF 拷贝到上述目录

### 行为流程

**Phase 0 (scan):** `python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_ingest.py" scan --type certs`。空目录/全已登记→退出。

**Phase 1 (extract):** 逐个 Read PDF，按 `references/cert-extraction-prompt.md` 输出 JSON，标置信度。禁止猜测。

**Phase 2 (confirm):** Markdown 表 + AskUserQuestion 批量确认（全部批准/只批高置信/逐条/放弃）。

**Phase 3 (apply):** `echo "$PAYLOAD" | python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_ingest.py" apply --payload-file -`

**Phase 4 (report):** 输出新增条目数、跳过数、放弃数、备份路径。

**Phase 5 (diagnose):** `python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_doctor.py" diagnose --mode mini`，渲染 mini 摘要。

### 约束

- 禁止编造字段、禁止不经确认写入、禁止移动原 PDF、禁止删 .bak

---

## Products 流程 — 产品材料入库

### 前置条件

- `ps:setup` 已执行，`${PRESALES_HOME}/知识库/产品档案/` 存在
- 用户提供产品材料目录路径（含 PDF/Word/Excel/PPT/MD）

### 输入/输出

| 输入 | 输出 |
|------|------|
| `--source <外部材料目录>` | `知识库/产品档案/{slug}/facts.yaml` |
| 支持: PDF, docx, xlsx, pptx, md | `知识库/产品档案/{slug}/facts.md` |
| 材料只读，不移动不复制 | `知识库/产品档案/{slug}/evidence.yaml` |
| | `知识库/产品档案/{slug}/evidence.md` |

### 行为流程

**Phase 1 (scan):**

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_ingest.py" scan --type products --source <路径> [--slug <slug>]
```

解析 stdout JSON。`status == "exists"` 且无 `--force` → 提示"产品已存在，跳过或用 --force 覆盖"。展示文件清单，请用户确认 slug。

**Phase 2 (extract):**

逐个 Read 材料文件，按 `references/product-extraction-prompt.md` 提取：
1. 先提取核心事实库 19 模块 → facts JSON
2. 再提取可信证据库 13 模块 → evidence JSON
3. 生成 facts.md 和 evidence.md（叙述性段落，缺失项标 `> ❌`）
4. 每个模块标 `_q`（confidence + source + gap）

材料文件多时分批读取，避免单次上下文过长。PPT 为实验性支持（best-effort）。

**Phase 3 (review):**

展示产品魔方审计表：

```
产品魔方审计 — {slug}
  核心事实库 (19): ✅ 12  ⚠️ 3  ❌ 4  → 可查级
  证据库 (13):     ✅ 2   ⚠️ 1  ❌ 10

  模块明细:
  ✅ M01 整体介绍     high  白皮书§1
  ✅ M02 产品定位     high  白皮书§2
  ⚠️ M03 应用现状     medium  缺客户数
  ❌ M05 演进路线     —  需产品经理输入
  ...
```

用户选择："确认写入" / "补全后写入" / "放弃"。

选"补全后写入" → 进入 Phase 3a。

**Phase 3a (interactive fill):** 对话式逐模块补全。自动提取能补的先补，需要人工的提示"这个信息找谁要"。补全后更新审计表。

**Phase 4 (apply):**

构造 payload JSON（含 facts_yaml, facts_md, evidence_yaml, evidence_md 四个字符串），调用：

```bash
echo "$PAYLOAD" | python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_ingest.py" apply --type products --slug <slug> --payload-file -
```

**Phase 5 (diagnose):**

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_doctor.py" diagnose --mode mini
```

输出产品当前等级、缺什么、下一步建议。

### 批量模式

`--source` 指向包含多个产品子目录的父目录时，循环执行 Phase 1-5。每个产品独立上下文（产品间清空），产品间输出分隔线 + 等级摘要。全部完成后汇总：

```
批量入库完成: 5 个产品
  ✅ firewall-pro     可投
  ✅ siem-enterprise   可查
  ⚠️ edr-agent        已录入（核心事实 45%）
  ...
```

### 约束

- **禁止编造** — 材料未提及的信息标 null + `_q.confidence: null`
- **禁止不经确认写入** — Phase 3 审计表确认后才进 Phase 4
- **禁止移动材料** — 只读取，不动原始文件
- **幂等跳过** — 已存在的产品默认跳过，`--force` 覆盖

### 失败处理

| 情况 | 处理 |
|------|------|
| 材料目录不存在 | 脚本退出码 3，提示检查路径 |
| 材料为空（无支持格式） | 提示"目录下没有支持的文件格式" |
| 产品已存在且无 --force | 提��跳过或用 --force |
| Read 读 PDF 失败 | 跳过该文件，提示提供替代格式 |
| PPT 提取效果差 | 提示"PPT 为实验性支持，建议提供 PDF/Word" |
