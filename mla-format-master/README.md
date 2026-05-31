# MLA Format Master

基于 MLA Handbook 9th Edition (2021) 的学术论文字格式自动化工具。

## 功能特性

- ✅ **精准触发**：仅通过上传.docx文件 + 明确MLA关键词触发
- ✅ **智能分析**：自动分析文档内容，判断是否为学术论文
- ✅ **多轮确认**：所有信息确认无误后才执行转换
- ✅ **完整MLA格式**：
  - 页面设置（US Letter, 1英寸边距, 双倍行距）
  - 标题页生成
  - 页眉页脚（姓氏 + 页码）
  - 文内引用格式化
  - Works Cited页面生成
- ✅ **中英混排支持**：处理中文作者名、中文出版物

## 使用流程

1. **上传文档**：上传需要格式化的.docx文件
2. **明确意图**：输入包含"MLA"和"格式/转换"等关键词
3. **文档分析**：系统自动分析文档类型和内容
4. **确认继续**：确认是否为学术论文
5. **信息收集**：提供学生姓名、教师、课程、日期、标题等信息
6. **引用确认**：确认文档中的引用来源
7. **格式选项**：选择首页页码、章节标题等选项
8. **最终确认**：查看确认单，确认无误后执行转换
9. **下载文件**：获取格式化后的MLA标准文档

## 技术实现

- **文档读取**：使用 pandoc 提取.docx内容
- **文档生成**：使用 docx-js 生成符合MLA标准的Word文档
- **格式规范**：严格遵循 MLA Handbook 9th Edition

## 文件结构

```
mla-format-master/
├── skill.md           # Skill架构文档
├── prompt.md          # Skill Prompt定义
├── src/
│   └── index.js       # 核心实现代码
├── package.json       # 项目配置
└── README.md          # 说明文档
```

## MLA格式规范要点

### 页面设置
- 纸张：US Letter (8.5 x 11 inch)
- 边距：1 inch (2.54cm) 四边
- 字体：Times New Roman 12pt
- 行距：双倍行距
- 段落：首行缩进0.5 inch

### 标题页
```
Your Name
Professor's Name
Course Name/Number
Day Month Year

[居中]
Title in Title Case
```

### 页眉
- 位置：右上角
- 内容：姓氏 + 空格 + 页码
- 示例：`Smith 1`

### 文内引用
- 基础格式：`(作者 页码)`
- 两位作者：`(Author1 and Author2 Page)`
- 三位及以上：`(Author1 et al. Page)`

### Works Cited
- 单独一页，标题居中
- 悬挂缩进0.5 inch
- 按作者姓名字母顺序排列

## 限制说明

1. 仅支持.docx格式
2. 基于MLA 9th Edition (2021)
3. 主要适用于人文社科学术论文
4. 无法自动查找所有引用来源的完整信息

## 参考资料

- [MLA Handbook, 9th Edition](https://style.mla.org/)
- [Purdue OWL MLA Guide](https://owl.purdue.edu/owl/research_and_citation/mla_style/)
