---
name: ps:knowledge-doctor
description: 诊断知识库完整度，输出健康度报告（9 维度扫描 + 缺口指导 + 入库建议）。当用户说"知识库体检"、"知识库诊断"、"knowledge doctor"、"知识库健康度"、"知识库缺什么"时触发。
---

# ps:knowledge-doctor — 知识库完整度诊断

## 前置条件

- `ps:setup` 已执行，`${PRESALES_HOME}/知识库/` 存在

## 输入

无参数。自动扫描 `${PRESALES_HOME}/知识库/` 及 `company-profile.yaml`。

## 输出

终端输出格式化的健康度报告（Markdown），不写文件。

## 行为流程

### Phase 1: 扫描

调用脚本拿 JSON 诊断结果：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_doctor.py" diagnose --mode full
```

解析 stdout JSON。脚本非零退出时把 stderr 透传给用户。

### Phase 2: 渲染报告

根据 JSON 中每个 dimension 的 `status` 分组渲染：

**分组规则**：
- `sufficient` → 充足
- `insufficient` → 不足（达到最低基线但未充足）
- `empty` → 空缺

**报告格式**（严格按此模板）：

```
知识库健康度报告
━━━━━━━━━━━━━━━━━━
整体完整度: {completeness_pct}% ({passing_dimensions}/{total_dimensions} 维度达标)

充足 ({sufficient_count})
  {label}    {描述性统计}
  ...

不足 ({insufficient_count})
  {label}    {描述性统计}
    → {去哪找建议}
  ...

空缺 ({empty_count})
  {label}    {描述性统计}
    → {去哪找建议}
    → {怎么喂指令}
  ...

下次入库建议:
  优先级 1: {最影响 bid-draft 的空缺维度}
  优先级 2: {第二优先}
  优先级 3: {第三优先}
```

### Phase 3: 缺口指导

每个非充足维度必须提供：

| 字段 | 说明 |
|------|------|
| 现状 | 有什么、有多少（从 JSON 字段读取） |
| 差距 | 距离基线差多少 |
| 去哪找 | 建议找谁（角色/部门）、从哪个系统获取 |
| 怎么喂 | 入库命令或操作步骤 |

**缺口建议对照表**（`references/gap-guidance.md` 中维护完整版，以下为速查）：

| 维度 | 去哪找 | 怎么喂 |
|------|--------|--------|
| 公司资质 | 法务/行政部 | 扔 PDF 进 `知识库/资质证书/` → `/ps:knowledge-ingest certs` |
| 团队汇总 | HR / 项目管理部 | 人员资质 Excel → `ps_knowledge_extract.py team` |
| 团队明细 | 同上 | 同上（自动生成分片） |
| 产品档案 | 产品线负责人 | 每产品建 `知识库/产品档案/{slug}.yaml` |
| 竞品对比 | 市场部 / 投标同事 | 资质沙盘 Excel → `ps_knowledge_extract.py competitors` |
| 公司介绍 | 行政部 / 市场部 | 营业执照/宣传册放 `知识库/公司介绍/` |
| 客户案例 | 售前/项目经理 | 案例材料放 `知识库/客户案例/` |
| 案例引用 | 案例入库后手动 | 编辑 `company-profile.yaml` 添加 `case_references[]` |
| 差异化亮点 | 从资质/战绩提炼 | 编辑 `company-profile.yaml` 添加 `highlights[]` |

## Mini 模式（供 knowledge-ingest 集成调用）

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ps_knowledge_doctor.py" diagnose --mode mini
```

Mini 模式只返回非充足维度。knowledge-ingest Phase 4 结果汇报后追加简版摘要：

```
知识库状态更新
  公司资质  5→10 条有效（仍需 5 条达到充足）
  仍缺: 产品档案、客户案例、差异化亮点
```

## 失败处理

| 情况 | 处理 |
|------|------|
| 知识库目录不存在（退出码 3） | 提示用户运行 `/ps:setup` |
| YAML 损坏（退出码 4） | 透传 stderr + 建议从 `.bak` 恢复 |

## 约束

- **禁止写任何文件** — doctor 是只读诊断，不修改知识库
- **禁止评估内容质量** — 只做数量 + 结构检查
- **禁止自动拉取外部数据** — 只读本地文件系统
