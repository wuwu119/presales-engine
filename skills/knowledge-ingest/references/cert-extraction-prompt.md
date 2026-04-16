# 资质证书元数据抽取参考

本文件由 `skills/knowledge-ingest/SKILL.md` Phase 1 引用。Claude 用 Read 读取单个证书 PDF 后，按本文档约定输出结构化 JSON。

## 抽取输出 Schema

每个证书 PDF 产出一条 JSON：

```json
{
  "file": "iso27001-2024.pdf",
  "name": "信息安全管理体系认证 ISO/IEC 27001:2022",
  "issuer": "CNAS 中国合格评定国家认可委员会",
  "cert_no": "IS-2024-12345",
  "valid_from": "2024-07-01",
  "valid_until": "2027-06-30",
  "subject": "北京某某科技有限公司",
  "per_field_confidence": {
    "name": "high",
    "issuer": "high",
    "cert_no": "high",
    "valid_from": "high",
    "valid_until": "high",
    "subject": "medium"
  },
  "overall_confidence": "high",
  "notes": "subject 与公司名略有差异，建议用户核对"
}
```

### 字段规则

| 字段 | 含义 | 缺失处理 |
|------|------|---------|
| `file` | 文件名（basename，不含目录） | 必填 |
| `name` | 证书全称，保留版本号（如 ISO 27001:2022） | 缺失 → confidence=low |
| `issuer` | 发证机构中文全称（常见：CNAS / CQC / 公安部 / 工信部 / 信通院 / 中国网络安全审查技术与认证中心） | 缺失 → low |
| `cert_no` | 证书编号原文（保留连字符、空格原样） | 缺失 → medium，不一定所有证书都打印编号 |
| `valid_from` | 发证日期 ISO（YYYY-MM-DD） | 有些证书只写"有效期 3 年" → 可空，medium |
| `valid_until` | 有效期截止 ISO（YYYY-MM-DD） | 缺失 → low（rfp-analyze 判断资质必须看这个） |
| `subject` | 被发证主体名称（用于与 company.name_zh 核对） | 缺失 → medium |
| `per_field_confidence` | 每个字段的自评 `high` / `medium` / `low` | 必填 |
| `overall_confidence` | 整体置信度，规则见下 | 必填 |
| `notes` | 任何对用户有用的提示（主体名不一致、日期格式异常、扫描件质量差） | 可空 |

### overall_confidence 计算规则

- `name / issuer / valid_until` 任一为 `low` → `overall_confidence = low`
- 其余任一关键字段（`cert_no / valid_from / subject`）为 `low` → `overall_confidence = medium`
- 全部 `high` → `overall_confidence = high`
- 只有 `medium` 与 `high` 混合 → `overall_confidence = medium`

### 日期规范化

- 原文 "2024年7月1日" → `2024-07-01`
- 原文 "2024.07.01" → `2024-07-01`
- 原文只有"有效期 3 年"但有发证日期 → 推算 valid_until，标 confidence=medium，在 notes 说明"按 3 年推算"
- 完全无法推算 → 字段设为 null，confidence=low

### 发证机构识别提示

常见关键词（非穷举，用于辅助识别）：
- 信息安全类：CNAS、CQC、方圆标志、中国网络安全审查技术与认证中心（ISCCC）、中国信息安全测评中心
- 等级保护：公安部 / 某省公安厅网安总队
- 资质类：工信部、信通院、中国信息通信研究院
- 质量管理：CNAS、方圆标志、ISO 认证机构

若 PDF 里同时出现"申请方 / 受理方"与"发证方"，`issuer` 取**发证方**。

### 扫描件检测

Read 工具读取 PDF 时若返回纯图像无文本：
- `name` 等字段全部置 null
- `per_field_confidence` 全部 low
- `overall_confidence = low`
- `notes` 填写："扫描件 PDF，当前版本不支持 OCR，请提供原生 PDF 或手动录入"

## Few-Shot 样本占位符

<!-- 实现期验收（Unit 5）时用真实证书样本替换下列占位。先保留结构，让 prompt 在无样本时也能跑。 -->

### 样本 1（ISO 27001 示例）
```
<待填充：真实证书 PDF 的节选文本 + 期望输出 JSON>
```

### 样本 2（等保三级示例）
```
<待填充：真实证书 PDF 的节选文本 + 期望输出 JSON>
```

### 样本 3（扫描件失败示例）
```
<待填充：扫描件 PDF 节选 + 期望输出 JSON 含 notes>
```

## 禁止项

- **禁止猜测**：任何字段 LLM 无法从原文直接看出，必须 null + low，不能臆造
- **禁止翻译 issuer**：发证机构中文就是中文，英文就是英文，保留原文
- **禁止改写 cert_no**：连字符 / 空格 / 大小写按原文
- **禁止合并多张证书**：一个 PDF 文件 = 一条 JSON。若 PDF 里包含多张证书（如年审副本），只抽第一张并在 notes 说明
