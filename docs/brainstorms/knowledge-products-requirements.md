---
date: 2026-04-17
topic: knowledge-products-ingest
---

# 产品知识库构建

## Problem Frame

当前 presales-engine 的知识库中产品档案为空（0 个结构化产品文件），导致 `bid-draft` 写技术方案章节只能瞎编，`rfp-analyze` 做产品匹配没有数据。用户手头有 20+ 产品的成套材料（PPT/Word/PDF/Excel），但手工按产品魔方 41 模块标准填写不现实。

通过天擎防病毒 SDK 的端到端原型验证，发现：
- 核心事实库（19 模块）约 60% 可从材料自动提取
- 证据库（13 模块）部分可提取（案例方案描述），但量化成果和客户证言必须人工
- 策略库（9 模块）完全无法从材料提取
- 每个产品入库约需 1 个 session（含材料阅读、提取、质量检查）

## Requirements

**存储结构（破坏性变更）**

- R1. 每个产品一个独立子目录：`知识库/产品档案/{slug}/`。**这是对现有扁平 `{slug}.yaml` 结构的破坏性变更**，需同步更新以下下游消费者：
  - `ps_knowledge_doctor.py._diagnose_products()`：从 `_count_yaml_files()` 改为扫描子目录中的 `facts.yaml`
  - `templates/产品档案/example.yaml`：废弃，替换为 `templates/产品档案/example/facts.yaml` + `facts.md`
  - `knowledge-seed/产品档案/README.md`：更新目录结构说明
  - `ps:rfp-analyze` 和 `ps:bid-draft`：产品发现逻辑从 `产品档案/*.yaml` 改为 `产品档案/*/facts.yaml`
- R2. 每个库两个文件：YAML（结构化索引：标签、枚举值、数字、缺口标记）+ MD（段落级内容：bid-draft 直接引用的文本）
- R3. 本期只做核心事实库（`facts.yaml` + `facts.md`）和证据库（`evidence.yaml` + `evidence.md`）。策略库目录预留交由 `ps:setup` 的 knowledge-seed 骨架处理，不在本 skill 范围内
- R4. YAML 中每个模块带 `_q` 质量元数据：`confidence`（high/medium/low）、`source`（材料来源）、`gap`（缺口描述）

**产品魔方对标**

- R5. 核心事实库覆盖产品魔方 19 个子模块（产品概述 5 + 产品功能 3 + 应用价值 4 + 关键能力 3 + 典型场景 4）
- R6. 证据库覆盖产品魔方 13 个子模块（权威背书 3 + 荣誉奖项 3 + 成功案例 7）
- R7. 产品魔方 41 模块的完整 schema（模块 ID、名称、所属库、写作公式、一票否决项、标签定义）须作为参考文档固化到 `skills/knowledge-ingest/references/product-cube-schema.md`，实现时以该文档为单一真相源
- R7a. v1.0 质量检查采用结构性检查（字段是否存在、字数是否达标、三要素是否齐全），不做 LLM 语义质量评分。写作公式用于指导 LLM 提取时的 prompt，不作为自动化验收门控
- R8. MD 中缺失的子模块用 `> ❌` 引用块标注缺失原因和补充指引（找谁、从哪获取）

**分级可用**

- R9. 四级可用门槛（"达标"定义为：字段非空 + 结构性检查通过，不做语义质量评分）：
  - **已录入**：facts.yaml 存在，核心事实库 < 60% 子模块达标 → 批量提取后的初始状态
  - **可查**：核心事实库 ≥ 60% 子模块达标（产品概述+功能基本完整）→ bid-draft 可初步引用
  - **可投**：核心事实库 ≥ 80% + 证据库 ≥ 50% 达标（至少有第三方测评或成功案例）→ 标书有说服力
  - **可竞**：可投 + 策略库 ≥ 50% 达标 → 能打竞品（本期不做）
- R10. `knowledge-doctor` 升级：产品维度从"数文件数"改为按分级可用标准诊断，报告中展示每个产品的当前等级。注意：这要求 doctor 突破现有"禁止评估内容质量"约束，改为读取 `facts.yaml` 的 `_q` 字段做结构性检查（非语义评分）。doctor JSON schema 需新增 `products_detail` 列表字段（每项含 slug + tier + gap_count），同时保留 `value` 字段向后兼容

**入库流程（通过 `ps:knowledge-ingest products` 触发）**

- R11. 本功能作为 `ps:knowledge-ingest` 的扩展，新增 `products` 子命令（与现有 `certs` 并列）。触发方式：`/ps:knowledge-ingest products --source <材料目录>`。skill 自动读取所有支持格式的文件，脚本负责文本提取（PDF/Word/Excel/PPT → 纯文本），LLM 负责语义映射（纯文本 → 产品魔方模块），生成 `facts.yaml` + `facts.md`
- R12. 提取结果质量检查：提取完成后对照产品魔方写作公式逐模块检查，展示完整度报告（类似我们做的审计表）
- R13. 交互补全阶段：针对缺失/不达标的模块，通过对话逐个补全。自动提取能补的先补，需要人工输入的明确告诉用户"这个信息找谁要"
- R14. 证据库半自动：案例方案描述从白皮书/案例文档提取，量化成果和客户证言标记为 ❌ 待人工补充
- R15. 批量模式支持：一个目录下有多个产品子目录时，支持连续处理，每个产品提取完展示完整度摘要，全部完成后汇总

**输入支持**

- R16. 支持的材料格式：PDF、Word（.docx）、Excel（.xlsx）、PPT（.pptx）、Markdown
- R17. 材料不移动、不复制，只读取。生成的 YAML/MD 写入 `知识库/产品档案/{slug}/`
- R18. 产品 slug 由用户确认，skill 根据材料目录名建议默认值

**knowledge-doctor 联动**

- R19. 产品入库完成后自动追加 mini 诊断（当前等级 + 缺什么 + 下一步建议），复用 `ps_knowledge_doctor.py diagnose --mode mini` 接口，与 certs 入库 Phase 5 相同模式

## Success Criteria

1. **冷启动可用**：给定一个产品材料目录（含 PDF/Word），运行一次入库命令，生成的 facts.md 覆盖产品魔方核心事实库 ≥ 60% 子模块达标（测试须覆盖至少 3 个不同类型产品，不限于天擎 SDK 单一验证）
2. **质量可审计**：生成的 facts.yaml 中每个模块都有 `_q` 标记，完整度报告通过结构性检查准确反映达标情况
3. **缺口可行动**：每个 ❌ 缺失项有明确的"找谁补、从哪补"指引
4. **20+ 产品可批量**：批量模式下连续处理 5 个产品不中断，每个产品独立上下文（产品间清空），全部完成后输出汇总摘要（产品数 + 各产品等级）
5. **bid-draft 可消费**：更新 `ps:bid-draft` 的产品发现逻辑，从 `产品档案/*/facts.md` 按章节标题拉取段落写入标书草稿（本期仅更新发现路径，不改 bid-draft 生成逻辑）

## Scope Boundaries

- **不做策略库**：竞争策略库的 9 个子模块（竞争优势 4 + 机会发现 5）本期不做交互补全，目录预留交由 `ps:setup`
- **不做材料迁移**：不移动/复制/重命名用户的原始材料文件
- **不做跨产品关联**：产品间的竞品对标、产品组合推荐等不在本期
- **不做自动更新**：材料更新后不自动触发重新提取，需用户手动重跑
- **不做 OCR**：扫描件 PDF 先报错，不做 OCR 识别

## Key Decisions

- **产品魔方全面对标**：不自创 schema，完全参考产品魔方三库 41 模块体系。原因：产品魔方是经过实战验证的售前内容方法论，自创会遗漏关键维度
- **YAML + MD 双文件**：YAML 只存结构化索引（标签/数字/枚举/缺口标记），MD 存段落级叙述。原因：标书生成需要直接引用的段落，不是从 YAML 字符串拼接
- **分级可用**：可查→可投→可竞三级，而非一次性全部填满。原因：20+ 产品全部按魔方 41 模块填满不现实，分级让用户能渐进式完善
- **先批量后补全**：先对 20+ 产品跑批量提取（达到"可查"），再按投标需要逐个补全到"可投"。原因：效率最优，避免在不急用的产品上花时间
- **策略库 v1.0 不做**：策略库内容（竞品对比、销售话术、质疑应答）完全来自人工经验，无法自动提取，延后到有明确需求时做。原因：投入产出比低，先解决"有没有"再解决"打不打得赢"
- **指向原始目录**：用户告知材料位置，skill 去读，不要求用户预先整理到知识库目录下。原因：降低入库门槛，用户不需要改变现有文件管理习惯

## Dependencies / Assumptions

- 依赖 `ps:setup` 已创建 `知识库/产品档案/` 目录结构
- 依赖 Python 第三方库：`openpyxl`（读 xlsx）、`python-docx`（读 docx）、`python-pptx`（读 pptx），需 pip 安装，按现有 `ps_knowledge_extract.py` 的 lazy-import + 友好报错模式处理
- 假设每个产品的材料在一个目录下，不跨目录散布
- 假设产品魔方的写作标准适用于安全行业产品（已通过天擎 SDK 验证）

## Outstanding Questions

### Deferred to Planning

- [Affects R11][Technical] 批量提取时 LLM 单次可处理的材料总量上限是多少？天擎 SDK 8 个文件约 60 页，是否需要分批送入？
- [Affects R16][Technical] PPT 文件的结构化提取效果如何？是否需要先转图片再用多模态识别？PPT 在 v1.0 作为实验性支持（best-effort，不承诺覆盖率达标）
- [Affects R10][Technical] knowledge-doctor `_diagnose_products` 函数从 `_count_yaml_files` 改为扫描子目录 + 解析 `_q` 字段，需更新现有测试用例
- [Affects R1][Technical] 现有扁平 `{slug}.yaml` 产品文件（如有）的迁移策略：是否提供一次性迁移脚本？
- [Affects R11][Technical] 重跑已有产品的提取行为：覆盖、合并还是报错？建议与 certs 入库保持一致（幂等跳过已存在）

## Next Steps

-> `/ce:plan` for structured implementation planning
