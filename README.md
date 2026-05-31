# Trae Skills Collection

> 基于 Trae SOLO 平台的 AI Skills 合集 — 提供科研辅助、学术写作、低碳生活等多领域智能工具

## 📦 Skills 概览

| Skill | 描述 | 适用场景 |
|-------|------|---------|
| [research-copilot](./research-copilot/) | 科研论文选题与文献综述助手 | 研究生、博士生、科研人员 |
| [mla-format-master](./mla-format-master/) | MLA 9th Edition 学术论文格式化工具 | 人文社科论文写作 |
| [carbon-footprint-auditor](./carbon-footprint-auditor/) | 个人/家庭碳排放追踪与减碳建议 | 低碳生活、环保意识培养 |

---

## 🔬 research-copilot

科研论文选题与文献综述助手，帮助研究生和科研人员高效完成论文选题、文献检索、趋势分析和综述撰写。

### 核心功能

- 🔍 **多源文献检索** — 支持 Semantic Scholar、CrossRef、PubMed、OpenAlex、arXiv 五大数据库
- 🇨🇳 **中文文献检索** — 支持知网、万方、百度学术搜索建议
- 📈 **研究趋势分析** — 识别年度发文趋势、热点关键词、热门期刊/会议
- 🎯 **研究 GAP 识别** — 发现领域内饱和方向与空白机会
- 🔬 **选题相似度检测** — 避免重复研究
- 📝 **文献综述框架生成** — 支持理工科和人文社科定制
- 📚 **引用格式化** — 支持 GB/T 7714、APA、IEEE、BibTeX

### 快速开始

```bash
# 文献检索
python3 research-copilot/scripts/search_papers.py --query "transformer attention" --year-from 2020 --limit 10

# 趋势分析
python3 research-copilot/scripts/analyze_trends.py --query "medical image analysis" --year-from 2020 --year-to 2024

# 研究 GAP 识别
python3 research-copilot/scripts/identify_gaps.py --query "deep learning" --year-from 2020 --year-to 2024
```

📖 [查看完整文档](./research-copilot/README.md)

---

## 📝 mla-format-master

基于 MLA Handbook 9th Edition (2021) 的学术论文格式自动化工具。

### 核心功能

- ✅ **精准触发** — 仅通过上传 .docx 文件 + 明确 MLA 关键词触发
- ✅ **智能分析** — 自动分析文档内容，判断是否为学术论文
- ✅ **完整 MLA 格式** — 页面设置、标题页、页眉页脚、文内引用、Works Cited
- ✅ **中英混排支持** — 处理中文作者名、中文出版物

### MLA 格式规范

| 项目 | 规范 |
|------|------|
| 纸张 | US Letter (8.5 x 11 inch) |
| 边距 | 1 inch (2.54cm) 四边 |
| 字体 | Times New Roman 12pt |
| 行距 | 双倍行距 |
| 页眉 | 姓氏 + 页码（右上角） |

📖 [查看完整文档](./mla-format-master/README.md)

---

## 🌱 carbon-footprint-auditor

个人/家庭碳排放追踪与减碳建议工具，帮助用户建立碳账户，追踪日常消费产生的碳排放。

### 核心功能

- 📊 **碳排放计算** — 支持出行、饮食、居住、购物四大类别
- 📈 **报告生成** — 日报、周报、月报多维度分析
- 🏆 **成就系统** — 30个成就徽章，8个等级称号
- 💡 **减碳建议** — 基于真实数据的个性化建议

### 碳排放计算方法

| 类别 | 计算公式 |
|------|---------|
| 出行 | 排放因子(kgCO₂/km) × 里程(km) / 乘车人数 |
| 饮食 | Σ(食材因子 × 份量) × 烹饪系数 |
| 居住 | 用电量(kWh) × 电网排放因子 + 用气量(m³) × 燃气因子 |
| 购物 | 商品生产排放 + 物流排放 |

### 等级系统

| 等级 | 称号 | 累计减碳值 |
|------|------|------------|
| Lv.1 | 碳足迹新手 🌱 | 0-50kg |
| Lv.2 | 环保学徒 🌿 | 50-200kg |
| Lv.3 | 绿色践行者 🍃 | 200-500kg |
| Lv.4 | 低碳达人 ♻️ | 500-1000kg |
| Lv.5 | 环保先锋 🌍 | 1000-2000kg |
| Lv.6 | 碳中和卫士 🏆 | 2000-5000kg |
| Lv.7 | 地球守护者 🌎 | 5000-10000kg |
| Lv.8 | 碳减排大师 👑 | 10000kg+ |

📖 [查看完整文档](./carbon-footprint-auditor/SKILL.md)

---

## 📁 项目结构

```
Trae-Skills/
├── research-copilot/                   # 科研论文助手
│   ├── scripts/                        # Python 脚本
│   │   ├── search_papers.py            # 多源文献检索
│   │   ├── search_chinese.py           # 中文文献检索
│   │   ├── analyze_trends.py           # 趋势分析
│   │   ├── identify_gaps.py            # GAP 识别
│   │   ├── check_similarity.py         # 相似度检测
│   │   └── format_citations.py         # 引用格式化
│   ├── SKILL.md                        # Skill 定义
│   ├── research-copilot.zip            # 打包好的skill
│   └── README.md
│
├── mla-format-master/                  # MLA 格式化工具
│   ├── src/
│   │   └── index.js                    # 核心实现
│   ├── skill.md                        # Skill 定义
│   ├── prompt.md                       # Prompt 模板
│   ├── mla-format-master.zip           # 打包好的skill
│   └── README.md
│
├── carbon-footprint-auditor/           # 碳足迹审计员
│   ├── data/
│   │   ├── emission_factors.json       # 排放因子库
│   │   ├── achievements.json           # 成就系统配置
│   │   ├── user_config.json            # 用户档案
│   │   └── records.csv                 # 消费记录
│   ├── carbon-footprint-auditor.zip    # 打包好的skill
│   └── SKILL.md                        # Skill 定义
│
├── .gitignore
└── README.md
```

---

## 🚀 使用方式

这些 Skills 设计用于 Trae SOLO 等 AI Agent 平台：

1. **在 Trae SOLO 中安装** — 将对应 Skill 文件夹部署到平台
2. **触发关键词** — 通过特定关键词激活对应 Skill
3. **交互式使用** — 按照引导完成操作

### 触发关键词参考

| Skill | 触发关键词 |
|-------|-----------|
| research-copilot | 论文选题、文献检索、研究趋势、文献综述、GAP分析 |
| mla-format-master | MLA格式、MLA转换、论文格式化（需上传.docx文件） |
| carbon-footprint-auditor | 碳足迹、碳排放、减碳、低碳生活、碳账户 |

---

## 🛠️ 技术栈

| Skill | 语言 | 依赖 |
|-------|------|------|
| research-copilot | Python 3.7+ | 标准库 |
| mla-format-master | Node.js | docx-js, pandoc |
| carbon-footprint-auditor | - | JSON/CSV 数据文件 |

---


## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这些 Skills。

---

**版本**: v3.0 | **适用平台**: Trae SOLO 等 AI Agent 平台 | **更新日期**: 2026-05
