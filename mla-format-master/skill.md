---
name: mla-format-master
description: "MLA Format Master - Automatically format academic papers to MLA 9th Edition standard. When a user uploads a .docx file and explicitly requests MLA format conversion (keywords: mla + format/convert/citation/works cited), this skill analyzes the document content, confirms it is an academic paper, collects required metadata (student name, professor, course, date, title), verifies all citation sources, and generates a fully MLA-compliant Word document with proper page setup, title page, headers, in-text citations, and Works Cited page. Only triggers when both a .docx file is uploaded AND MLA-related keywords are present in the user's request."
---

# MLA Format Master

## 基本信息
- **版本**: 1.0.0
- **基于**: MLA Handbook 9th Edition (2021)
- **触发条件**: 用户上传 .docx 文件并明确请求MLA格式转换

## 触发词（精准匹配，不随意触发）

### 必须同时满足以下条件才会触发：
1. **文件条件**: 用户上传了 `.docx` 格式的Word文档
2. **意图条件**: 用户输入包含以下任一关键词组合：
   - "mla" / "MLA" + "format" / "格式" / "转换" / "修改" / "调整"
   - "论文格式" + "mla" / "MLA"
   - "学术格式" + "mla" / "MLA"
   - "引用格式" + "mla" / "MLA"
   - "works cited" / "文内引用" + "mla" / "MLA"

### 不触发的情况：
- 仅上传文件但未提及MLA相关关键词
- 仅询问MLA格式问题但未上传文档
- 上传非.docx格式文件（如.pdf, .txt等）
- 用户明确提到其他格式（APA, Chicago等）

## 执行流程

### Phase 1: 触发确认
```
当检测到触发条件时：
1. 确认收到文档
2. 告知用户即将进行MLA格式分析
3. 进入Phase 2
```

### Phase 2: 文档内容分析
```
1. 读取用户上传的.docx文档内容
2. 分析文档特征：
   - 文档长度（字数/页数）
   - 内容类型判断：
     * 是否包含学术性内容（引用、参考文献、论点等）
     * 是否已有标题页信息
     * 是否已有引用/参考文献部分
     * 主题领域（人文社科相关度）
   - 现有格式特征：
     * 当前字体/字号
     * 当前行距
     * 是否有页眉页脚
     * 段落缩进方式

3. 输出分析报告：
   ┌─────────────────────────────────────────┐
   │  📄 文档分析报告                         │
   ├─────────────────────────────────────────┤
   │  文档类型: [学术论文/普通文章/不确定]    │
   │  当前字数: [XXX] 字                      │
   │  检测到的引用: [有/无]                   │
   │  现有格式问题: [列出主要问题]            │
   └─────────────────────────────────────────┘
```

### Phase 3: 文档类型判断与用户确认

#### 情况A：判断为学术论文
```
系统输出：
"根据文档内容分析，这似乎是一篇学术论文/课程论文。
文档特征：
- 包含学术性论述
- 有引用/参考文献痕迹
- 内容符合人文社科领域特征

是否继续转换为MLA 9th Edition格式？
[继续] / [退出]"
```

#### 情况B：判断为非学术论文
```
系统输出：
"根据文档内容分析，这篇文档可能不是学术论文：
- [具体原因：如内容偏向商业/技术文档/个人随笔等]
- 缺少典型的学术写作特征

MLA格式主要适用于人文社科学术论文。
您确定要继续吗？
[仍要继续] / [退出]"
```

#### 情况C：无法确定
```
系统输出：
"无法确定文档类型。文档内容：
[简要描述文档主题和内容]

请问这是一篇需要格式化的学术论文吗？
[是，继续] / [否，退出]"
```

### Phase 4: 信息收集（如用户选择继续）

#### 必需信息清单：

**4.1 学生信息（用于标题页）**
```
请提供以下信息（用于MLA标题页）：

1. 您的姓名（Your Name）: [等待输入]
   ⚠️ 中文姓名请提供 Pinyin 格式（如 Li Mingming），MLA 要求按拼音字母顺序排列
   例如：Zhang Wei / Emily Johnson

2. 指导教师姓名（Professor's Name）: [等待输入]
   例如：Prof. Smith / Dr. Li Ming

3. 课程名称及编号（Course Name/Number）: [等待输入]
   例如：ENG 101 / Introduction to Literature

4. 提交日期（Date）: [等待输入]
   格式：Day Month Year
   例如：15 October 2024
   
   或使用当前日期？[是/否]
```

**4.2 论文标题确认**
```
检测到的论文标题：[自动提取的标题]

请确认或修改标题：
[保留原样] / [输入新标题]

注意：MLA标题使用Title Case（首字母大写，介词/连词小写）
```

**4.3 引用来源确认**
```
文档中检测到以下可能的引用来源：

[列出检测到的引用/参考文献]
1. [来源1描述]
2. [来源2描述]
...

请确认这些引用是否需要包含在Works Cited中：
- 对于每个来源：[确认] / [删除] / [修改]

是否有遗漏的引用来源需要添加？[是/否]
```

**4.4 格式选项确认**
```
请确认以下MLA格式选项：

1. 纸张大小？
   MLA标准：US Letter (8.5 x 11 inch)
   部分地区/学校要求：A4 (210 x 297mm)
   [US Letter（标准）] / [A4] / [自定义：宽 x 高]

2. 首页是否需要页码？
   MLA标准：首页有页码
   部分教授要求：首页省略页码
   [标准（有页码）] / [省略首页页码]

3. 是否包含章节标题？
   [无章节] / [有章节，使用数字编号] / [有章节，使用文字标题]

4. 是否有特殊格式要求？
   [无] / [有，请说明：_____]
```

### Phase 5: 信息确认与最终授权

```
═══════════════════════════════════════════════════
📋 MLA格式转换确认单
═══════════════════════════════════════════════════

【文档信息】
原文件名: [filename.docx]
预计输出: [filename_MLA.docx]

【标题页信息】
学生姓名: [XXX]
指导教师: [XXX]
课程信息: [XXX]
提交日期: [XXX]

【论文标题】
[Title in Title Case]

【Works Cited】
共 [N] 条引用
来源类型: [书籍/期刊/网页等]

【格式选项】
纸张大小: [US Letter/A4/自定义]
首页页码: [有/无]
章节标题: [无/数字/文字]
特殊要求: [无/XXX]

═══════════════════════════════════════════════════

请确认以上信息是否正确：
[✓ 全部正确，开始转换]
[✗ 需要修改，返回修改]
[取消，退出操作]

注意：转换过程将：
1. 修改页面设置（边距/行距/字体）
2. 添加/修正标题页
3. 修正文内引用格式
4. 生成/修正Works Cited页面
5. 添加页眉页脚
```

### Phase 6: 执行转换

#### 6.1 页面设置调整
- 纸张：US Letter (8.5 x 11 inch) / A4 (210 x 297mm) / 自定义（根据用户选择）
- 边距：1 inch (2.54cm) 四边
- 字体：Times New Roman 12pt
- 行距：双倍行距 (Double-space)
- 对齐：左对齐
- 段落：首行缩进0.5 inch (使用Tab)

#### 6.2 标题页生成
```
左上角（左对齐，双倍行距）：
Your Name
Professor's Name
Course Name/Number
Day Month Year

标题（居中，双倍行距后）：
Title in Title Case
（不使用引号/斜体/下划线）
```

#### 6.3 页眉设置
- 位置：右上角
- 内容：姓氏 + 空格 + 页码
- 距离：距顶部0.5 inch
- 首页：根据用户选择决定是否包含页码

#### 6.4 文内引用修正
- 扫描全文引用
- 按MLA Author-Page格式修正
- 特殊情况处理：
  * 两位作者 → (Author1 and Author2 Page)
  * 三位及以上 → (Author1 et al. Page)
  * 无作者 → ("Shortened Title" Page)
  * 无页码 → (Author) 或 ("Shortened Title")

#### 6.5 Works Cited页面生成
- 单独一页
- 标题 "Works Cited" 居中
- 悬挂缩进0.5 inch
- 按作者姓名字母顺序排列
- 双倍行距，条目间无额外空行

### Phase 7: 执行转换（生成初稿）

使用 docx-js 生成 MLA 格式文档。

**⚠️ 生成后必须立即进入 Phase 8 自检，不可跳过。**

### Phase 8: 自检与修复（必须执行）

**核心原则：生成文档后，解包检查 XML，对照 MLA 标准逐项验证，发现问题立即修复，修复后再次验证，直到全部通过。最多循环 3 轮。**

#### 自检流程
```
生成初稿 → unpack.py 解包 → 检查 XML → 发现问题 → 修复 → pack.py 重新打包 → 再次解包验证 → 全部通过 → 交付
```

#### 必检清单

**A. 页眉检查（最高优先级）**
- 检查 `word/_rels/document.xml.rels`：section 的 `<w:headerReference>` rId 是否指向正确的 header 文件
- 检查 `word/header1.xml`：是否包含用户姓氏 + PAGE_NUMBER 字段 + 右对齐
- 常见错误：rId 指向 watermark/空白文件 → 修正 rId 映射或创建正确 header 文件

**B. Works Cited 分页检查**
- 检查 `word/document.xml`："Works Cited" 标题前是否有 `<w:br w:type="page"/>`
- 常见错误：缺少分页符 → 插入分页符

**C. 页面设置检查**
- `<w:pgSz>` 尺寸是否匹配用户选择（Letter: 12240x15840, A4: 11906x16838）
- `<w:pgMar>` 四边距是否均为 1440

**D. 字体与行距检查**
- 默认字体 Times New Roman 12pt（w:sz="24"）
- 行距双倍（w:line="480"）

**E. 段落缩进检查**
- 正文首行缩进 720（0.5 inch）
- Works Cited 悬挂缩进 left=720 hanging=720
- 标题页四行无缩进

**F. 标题页检查**
- 四行信息左对齐无缩进
- 论文标题居中

#### 修复策略
1. 定位 XML 文件和具体位置
2. SearchReplace 精确修改
3. 缺失文件用 Write 创建
4. 修复后 pack.py 重新打包
5. 再次解包验证
6. 最多 3 轮，仍失败则提示用户手动检查

### Phase 9: 输出与交付

```
═══════════════════════════════════════════════════
✅ MLA格式转换完成（已通过自检验证）
═══════════════════════════════════════════════════

【转换摘要】
✓ 页面设置已调整为MLA标准
✓ 标题页已生成
✓ 页眉页脚已添加（姓氏 + 页码）← 已验证XML
✓ 文内引用已修正 [N] 处
✓ Works Cited已生成 [N] 条 ← 已验证分页

【自检结果】
✓ 页眉内容正确（姓氏 + 页码，右对齐）
✓ 页眉 rId 引用正确
✓ Works Cited 前有分页符
✓ 页面尺寸正确
✓ 四边距均为 1 inch
✓ 字体 Times New Roman 12pt
✓ 双倍行距
✓ 正文首行缩进 0.5 inch
✓ Works Cited 悬挂缩进 0.5 inch

【下载文件】
[点击下载 formatted_document_MLA.docx]

【后续建议】
1. 在Word中打开检查格式
2. 确认教授的特殊要求是否满足
3. 检查Works Cited是否完整
4. 如需修改，可重新上传调整

═══════════════════════════════════════════════════
```

## 技术实现说明

### 文档读取
使用平台内置docx Skill读取用户上传的.docx文件：
```bash
pandoc --track-changes=all document.docx -o content.md
```

### 文档生成
使用docx-js库生成符合MLA格式的新文档：
- 页面尺寸：US Letter (12240 x 15840 DXA)
- 边距：1440 DXA (1 inch) 四边
- 字体：Times New Roman 12pt
- 行距：双倍 (480 twips)
- 段落缩进：720 twips (0.5 inch)

### 引用检测逻辑
1. 正则表达式识别潜在引用：
   - 引号内容
   - 括号内作者-页码组合
   - 已存在的Works Cited条目

2. 自然语言分析：
   - 识别"According to..."等引用信号词
   - 识别人名+年份组合
   - 识别统计数据/事实陈述（可能需要引用）

## 错误处理

### 文件读取失败
```
无法读取文档内容。可能原因：
- 文件损坏
- 文件受密码保护
- 文件格式不兼容

请检查文件后重新上传，或转换为标准.docx格式。
```

### 信息收集不完整
```
以下信息尚未提供，无法继续：
- [缺失项列表]

请补充以上信息后继续。
```

### 引用来源不明确
```
检测到以下引用信息不完整：
[列出不完整的引用]

请选择处理方式：
[尝试自动查找完整信息]
[手动补充信息]
[暂时跳过，后续手动添加]
```

## 限制说明

1. **仅支持.docx格式**：不支持.doc, .pdf, .txt等其他格式
2. **MLA 9th Edition**：基于2021年最新版MLA手册
3. **人文社科适用**：MLA主要适用于文学、语言、文化研究等领域
4. **自动化限制**：
   - 无法自动查找所有引用来源的完整信息
   - 无法判断引用是否必要（仅格式化现有引用）
   - 复杂的表格/图表格式可能需要手动调整

## 版本规划

### v1.0 (当前)
- 基础MLA格式转换
- 标题页生成
- Works Cited生成
- 文内引用修正

### v2.0 (未来)
- APA格式支持
- Chicago格式支持
- 引用来源自动查找（DOI/ISBN解析）
- 批量文档处理

## 参考资料

- MLA Handbook, 9th Edition (2021)
- Purdue OWL MLA Guide: https://owl.purdue.edu/owl/research_and_citation/mla_style/
