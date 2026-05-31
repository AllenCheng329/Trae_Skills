# Trae Skills: Research Copilot

> 科研论文选题与文献综述助手 — 基于 Trae SOLO 平台的 AI Skill，帮助研究生和科研人员高效完成论文选题、文献检索、趋势分析和综述撰写。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 **多源文献检索** | 支持 Semantic Scholar、CrossRef、PubMed、OpenAlex、arXiv 五大数据库，自动限流降级 |
| 🇨🇳 **中文文献检索** | 支持知网、万方、百度学术搜索建议，Semantic Scholar 中文论文筛选 |
| 📈 **研究趋势分析** | 基于真实数据识别年度发文趋势、热点关键词、热门期刊/会议 |
| 🎯 **研究 GAP 识别** | 发现领域内饱和方向与空白机会，辅助选题决策 |
| 🔬 **选题相似度检测** | 检测拟选题目与已有文献的相似度，避免重复研究 |
| 📝 **文献综述框架生成** | 输出标准化的文献综述结构，支持理工科和人文社科定制 |
| 📚 **引用格式化** | 支持 GB/T 7714、APA、IEEE、BibTeX 四种引用格式 |
| 📤 **多格式输出** | 支持 Markdown / Word / PDF / HTML 格式导出 |

## 📁 项目结构

```
Trae_Skills/
├── SKILL.md                              # Skill 定义文件（触发规则 + 工具说明）
├── ResearchCopilot_SystemPrompt.md        # 系统提示词（角色定义 + 工作流程）
├── ResearchCopilot_ExampleCase.md         # 示例演示案例（完整对话流程）
├── research-copilot.zip                   # 打包文件
├── scripts/
│   ├── search_papers.py                  # 多源学术文献检索
│   ├── search_chinese.py                 # 中文文献检索
│   ├── analyze_trends.py                 # 研究趋势分析
│   ├── identify_gaps.py                  # 研究 GAP 识别
│   ├── check_similarity.py               # 选题相似度检测
│   └── format_citations.py               # 引用格式化
└── README.md
```

## 🚀 快速开始

### 环境要求

- Python 3.7+
- 无需额外依赖（仅使用标准库）

### 文献检索

```bash
# 基础检索（自动选择最优数据源）
python3 scripts/search_papers.py --query "transformer attention" --year-from 2020 --limit 10

# 指定 PubMed 检索医学文献
python3 scripts/search_papers.py --query "cancer immunotherapy" --source pubmed --limit 20

# 指定 arXiv 检索预印本
python3 scripts/search_papers.py --query "large language model" --source arxiv --limit 15
```

### 中文文献检索

```bash
# 自动模式（推荐）
python3 scripts/search_chinese.py --query "深度学习 医学图像" --year-from 2022

# Semantic Scholar 中文论文
python3 scripts/search_chinese.py --query "知识图谱" --source semantic --limit 15
```

### 趋势分析

```bash
python3 scripts/analyze_trends.py --query "medical image analysis" --year-from 2020 --year-to 2024

# 输出 Markdown 报告
python3 scripts/analyze_trends.py --query "contrastive learning" --year-from 2019 --year-to 2024 --format report
```

### 研究 GAP 识别

```bash
python3 scripts/identify_gaps.py --query "medical image analysis" --year-from 2020 --year-to 2024
```

### 选题相似度检测

```bash
python3 scripts/check_similarity.py --topic "基于深度学习的医学图像分割" --query "deep learning medical image segmentation"

# 输出报告格式
python3 scripts/check_similarity.py --topic "多模态大模型在教育中的应用" --query "multimodal LLM education" --format report
```

### 引用格式化

```bash
# GB/T 7714 格式（中国国标）
python3 scripts/format_citations.py --input papers.json --style gb

# APA 格式
python3 scripts/format_citations.py --input papers.json --style apa

# BibTeX 格式
python3 scripts/format_citations.py --input papers.json --style bibtex

# 管道输入
python3 scripts/search_papers.py --query "transformer" --limit 5 | python3 scripts/format_citations.py --style ieee
```

## 📖 脚本参数速查

### search_papers.py

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--query` | `-q` | ✅ | 搜索关键词 |
| `--year-from` | `-yf` | | 起始年份 |
| `--year-to` | `-yt` | | 结束年份 |
| `--limit` | `-l` | | 返回数量（默认10，最大100） |
| `--sort` | `-s` | | 排序：`citation_count` / `relevance` / `year` |
| `--source` | | | 数据源：`auto` / `semantic_scholar` / `crossref` / `pubmed` / `openalex` / `arxiv` |
| `--format` | `-f` | | 输出格式：`json`（默认）/ `table` |

### analyze_trends.py

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--query` | `-q` | ✅ | 研究主题关键词 |
| `--year-from` | `-yf` | ✅ | 起始年份 |
| `--year-to` | `-yt` | ✅ | 结束年份 |
| `--top-keywords` | `-k` | | 关键词数量（默认10） |
| `--format` | `-f` | | 输出格式：`json`（默认）/ `report` |

### identify_gaps.py

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--query` | `-q` | ✅ | 研究主题关键词 |
| `--year-from` | `-yf` | ✅ | 起始年份 |
| `--year-to` | `-yt` | ✅ | 结束年份 |
| `--format` | `-f` | | 输出格式：`json`（默认）/ `report` |

### check_similarity.py

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--topic` | `-t` | ✅ | 拟选题目 |
| `--query` | `-q` | | 检索关键词（与 `--input` 二选一） |
| `--input` | `-i` | | 已有文献 JSON 文件路径 |
| `--year-from` | `-yf` | | 起始年份 |
| `--limit` | `-l` | | 检索文献数量（默认20） |
| `--format` | `-f` | | 输出格式：`json`（默认）/ `report` |

### format_citations.py

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--input` | `-i` | | 输入 JSON 文件路径（不指定则从 stdin 读取） |
| `--style` | `-s` | | 引用格式：`gb`（默认）/ `apa` / `ieee` / `bibtex` |

### search_chinese.py

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--query` | `-q` | ✅ | 搜索关键词（中文） |
| `--year-from` | `-yf` | | 起始年份 |
| `--limit` | `-l` | | 返回数量（默认10） |
| `--source` | `-s` | | 数据源：`auto`（默认）/ `cnki` / `semantic` |
| `--format` | `-f` | | 输出格式：`json`（默认）/ `table` |

## 🔄 工作流程

```
用户提出选题需求
       │
       ▼
  ┌─────────────┐
  │  需求澄清    │  了解学科、阶段、资源、偏好
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  数据采集    │  search_papers → analyze_trends → identify_gaps
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  分析与推荐  │  生成选题报告（趋势 + GAP + 可行性评估）
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  深度服务    │  综述框架 / 相似度检测 / 引用格式化
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  格式导出    │  Markdown / Word / PDF / HTML
  └─────────────┘
```

## 🛡️ 设计原则

- **学术严谨** — 所有文献推荐基于真实数据库检索，绝不编造
- **实用优先** — 输出可直接用于实际研究，非空泛建议
- **结构化输出** — 标准模板 + 表格呈现，清晰易读
- **交互式引导** — 逐步明确需求，非一次性输出
- **自动降级** — API 限流时自动切换数据源，全不可用时回退 WebSearch

## 🎓 适用学科

本 Skill 内置多学科定制化规则：

| 学科 | 特殊关注 |
|------|---------|
| 计算机/AI | SOTA 对比、顶会录用、开源代码 |
| 医学/生物 | 临床意义、伦理审查、影响因子 |
| 人文社科 | 理论框架、质性研究、CSSCI/SSCI |
| 工程应用 | 实用性、专利、系统实现 |

## 📌 数据来源

| 数据源 | 类型 | 覆盖范围 |
|--------|------|---------|
| Semantic Scholar | 综合学术图谱 | 全学科 |
| CrossRef | DOI 官方数据库 | 期刊论文 |
| PubMed | 生物医学文献 | 医学/生物 |
| OpenAlex | 开放学术图谱 | 全学科 |
| arXiv | 预印本服务器 | CS/物理/数学 |
| 知网/万方/百度学术 | 中文文献（WebSearch 回退） | 中文学术 |

## ⚠️ 注意事项

1. **API 限流**：Semantic Scholar 等免费 API 有请求频率限制，脚本已内置自动降级机制
2. **数据时效性**：论文收录可能有 1-3 个月延迟
3. **趋势分析耗时**：`analyze_trends.py` 逐年检索，年份跨度建议不超过 6 年
4. **中文文献**：知网/万方无公开免费 API，脚本返回 WebSearch 查询建议
5. **学术诚信**：本工具提供选题建议，请遵守学术规范，最终研究决策需结合导师指导

## 📄 License

MIT

---

**版本**: v4.0 | **适用平台**: Trae SOLO | **更新日期**: 2026-05
