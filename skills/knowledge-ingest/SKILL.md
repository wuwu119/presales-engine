---
name: ps:knowledge-ingest
description: 把 知识库/资质证书/ 下的证书 PDF 批量登记进 company-profile.yaml。扫描未登记文件，LLM 抽取元数据，用户确认后 append 进 qualifications[]。v0.2 MVP 只支持 certs。当用户说"入库证书"、"登记资质"、"knowledge ingest"、"扫描证书目录"时触发。
argument-hint: "certs"
---

# ps:knowledge-ingest — 资质证书入库

## 前置条件

- `ps:setup` 已执行，`${PRESALES_HOME}/知识库/资质证书/` 存在
- 用户已把证书 PDF 拷贝到上述目录（文件名建议英文或简单中文，例如 `iso27001.pdf` / `等保三级.pdf`）

## 输入

`${PRESALES_HOME}/知识库/资质证书/` 下的 `.pdf` 文件。非 PDF / `.DS_Store` / `README.md` 自动忽略。

## 输出

| 文件 | 变更 |
|------|------|
| `知识库/company-profile.yaml` | `qualifications[]` append 新条目 |
| `知识库/company-profile.yaml.bak` | 写入前的备份 |

原 PDF 文件不移动、不改名、不拷贝。

## 参数

v0.2 仅支持一个参数：`certs`。传其他值 / 不传都按 certs 处理。

## 行为流程

### Phase 0: 扫描差分

调用 scan 子命令拿到待处理列表：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_ingest.py" scan --type certs
```

解析 stdout JSON。根据结果分支：

- `new_files == []` 且 `already_registered == 0` → 提示用户 "资质证书目录为空，请把 PDF 放进 `知识库/资质证书/` 后重跑"，退出
- `new_files == []` 且 `already_registered > 0` → 提示 "所有证书已登记（共 N 条），无需操作"，退出
- `over_limit == true` → 先警告 "检测到超过 20 个新文件，本次只处理前 20 个，完成后再跑一次处理剩余"，继续 Phase 1
- `new_files` 非空 → 进入 Phase 1

脚本非零退出（代码 2/3/4/5）时直接把 stderr 中文化透传给用户，不进入后续阶段。

### Phase 1: LLM 抽取（Claude 执行）

对 `new_files` 中每个文件：

1. 用 Read 工具读取 `${PRESALES_HOME}/知识库/资质证书/<file>`（PDF 最多 20 页 / 次，单张证书足够）
2. 按 `references/cert-extraction-prompt.md` 的 schema 输出 JSON
3. 每个字段标 `high` / `medium` / `low` 置信度
4. 按 schema 文档的 `overall_confidence` 规则计算整体置信度
5. 扫描件 PDF 读取失败 → 按 schema 的"扫描件检测"规则输出 low + notes

**禁止**：凭经验猜测、改写原文、合并多张证书、翻译 issuer。

### Phase 2: 表格呈现 + 用户确认

把 Phase 1 结果整理成紧凑 Markdown 表（不折行，≤ 6 列）：

```
| # | 文件 | 证书名 | 发证机构 | 有效期至 | 置信度 |
|---|------|--------|----------|----------|--------|
| 1 | iso27001.pdf | ISO 27001 信息安全管理体系 | CNAS | 2027-06-30 | ✅ |
| 2 | 等保三级.pdf | 信息系统安全等级保护三级 | ⚠️ 未识别 | ⚠️ 未识别 | ⚠️ |
```

置信度列：`high` → ✅，`medium` → ⚠️，`low` → ⚠️。

表格下方显示每条低置信度项的 `notes` 字段（如有），帮助用户判断。

然后用 `AskUserQuestion` 批量确认，选项设计为：

- **全部批准**（仅当所有行都是 ✅ 时作为推荐项）
- **只批准高置信度条目**（跳过所有 ⚠️ 行）
- **逐条确认**（进入循环，每条单独问批准 / 跳过 / 用户手修 YAML）
- **全部放弃**（本次 session 不写任何条目）

用户选择 "逐条确认" 且某条需要手修时，提示用户："脚本不接受手修的条目，请先跳过，本轮完成后手动编辑 `知识库/company-profile.yaml` 添加。"

### Phase 3: 写入

把用户批准的条目构造成 payload 数组（字段映射见下），调 apply：

```bash
echo "$PAYLOAD_JSON" | python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_ingest.py" apply --payload-file -
```

**payload 字段映射**（每条）：

| payload 字段 | 来源 | 必填 |
|--------------|------|------|
| `file` | Phase 1 JSON 的 `file` | 是 |
| `name` | 同 | 是 |
| `issuer` | 同 | 是 |
| `cert_no` | 同（可 null） | 否 |
| `valid_from` | 同（可 null） | 否 |
| `valid_until` | 同 | 是 |
| `subject` | 同（可 null） | 否 |
| `confidence` | 映射 `overall_confidence` | 否，默认 high |

脚本写入成功后 stdout 返回 `{"added": N, "ids": [...]}`。

### Phase 4: 结果汇报

必须输出：

> ✅ 登记完成
> - 新增条目：{N} 条（{ids}）
> - 跳过已登记：{M} 条
> - 用户放弃：{K} 条（其中 ⚠️ 低置信度 {L} 条）
> - 备份文件：`知识库/company-profile.yaml.bak`
>
> 下一步：`/ps:rfp-analyze <slug>` 现在可以基于真实资质证据判断 Go/No-Go。

## 失败处理

| 情况 | 处理 |
|------|------|
| 资质证书目录不存在（脚本退出码 3） | 提示用户运行 `/ps:setup` 初始化知识库 |
| `company-profile.yaml` YAML 损坏（码 4） | 报错 + 显示脚本 stderr，建议用户从 `.bak` 恢复或手修后重跑 |
| payload 校验失败（码 5） | 这是 skill 构造 payload 的 bug，直接把 stderr 抛给用户 + 请求反馈 |
| Read 工具读 PDF 失败 / 扫描件无文本 | 按 schema "扫描件检测" 规则整行标 ⚠️，让用户决定跳过 |
| 用户要求处理 cases/ 或 products/ | 明确拒绝："v0.2 MVP 只支持 certs，其他类型将在 v0.3 加入" |

## 约束（强制）

- **禁止编造字段** — LLM 无法从原文直接看出的字段必须 null + low，不猜测
- **禁止不经用户确认写入** — 所有写入必须走 Phase 2 确认
- **禁止移动或改名原 PDF** — evidence_file 路径始终指向用户原始位置
- **禁止在 知识库/ 下创建隐藏状态文件** — 登记状态只存在 `company-profile.yaml.qualifications[].evidence_file`
- **禁止跳过 .bak 备份** — 脚本已自动生成，skill 不得删除
