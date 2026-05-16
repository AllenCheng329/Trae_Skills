#!/usr/bin/env python3
"""
Research Copilot - 选题相似度检测脚本
功能：检测拟选题目与已有文献的相似度，避免重复研究
原理：基于标题关键词重叠度和语义相似性评估
用法：
  python3 check_similarity.py --topic "基于深度学习的医学图像分割" --query "deep learning medical image segmentation"
  python3 check_similarity.py --topic "多模态大模型在教育中的应用" --query "multimodal LLM education" --limit 20
"""

import argparse
import json
import sys
import re
import math
from collections import Counter


# ============== 文本处理 ==============

STOPWORDS_EN = set([
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "or", "but", "if", "while", "about", "this", "that", "not",
    "no", "new", "based", "using", "used", "use", "via", "through",
    "propose", "proposed", "method", "approach", "study", "model",
    "data", "performance", "result", "results", "paper", "recent",
    "also", "two", "one", "three", "first", "second", "however",
    "therefore", "thus", "hence", "moreover", "furthermore",
])

STOPWORDS_CN = set([
    "的", "了", "在", "是", "和", "与", "对", "中", "为", "及", "等",
    "一种", "基于", "提出", "方法", "模型", "实验", "结果", "研究",
    "一个", "通过", "进行", "利用", "采用", "实现", "应用", "分析",
    "设计", "构建", "有效", "相关", "主要", "以及", "关于", "可以",
])


def tokenize(text):
    """分词：提取英文单词和中文词组"""
    tokens = []
    # 英文单词（至少2个字母）
    en_words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    for w in en_words:
        if w not in STOPWORDS_EN:
            tokens.append(w)
    # 中文（按单字/双字切分，简单处理）
    cn_chars = re.findall(r'[\u4e00-\u9fff]+', text)
    for segment in cn_chars:
        if len(segment) >= 2:
            # 提取2-4字词组
            for n in [2, 3, 4]:
                for i in range(len(segment) - n + 1):
                    word = segment[i:i + n]
                    if word not in STOPWORDS_CN:
                        tokens.append(word)
        elif segment not in STOPWORDS_CN:
            tokens.append(segment)
    return tokens


def compute_similarity(text1, text2):
    """
    计算两段文本的相似度（基于TF关键词重叠）
    返回 0-1 之间的相似度分数
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    counter1 = Counter(tokens1)
    counter2 = Counter(tokens2)

    # Jaccard 相似度
    set1 = set(tokens1)
    set2 = set(tokens2)
    intersection = set1 & set2
    union = set1 | set2
    jaccard = len(intersection) / len(union) if union else 0

    # TF 重叠度（考虑词频）
    shared = sum((counter1[w] * counter2[w]) for w in intersection)
    norm1 = math.sqrt(sum(v ** 2 for v in counter1.values()))
    norm2 = math.sqrt(sum(v ** 2 for v in counter2.values()))
    cosine = shared / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0

    # 综合分数（加权平均）
    return round(jaccard * 0.4 + cosine * 0.6, 4)


def check_topic_similarity(topic, papers, threshold_high=0.6, threshold_medium=0.3):
    """
    检测选题与已有文献的相似度

    参数:
        topic: 拟选题目
        papers: 已有文献列表（来自 search_papers 的输出）
        threshold_high: 高相似度阈值（可能重复）
        threshold_medium: 中等相似度阈值（需要关注）

    返回:
        dict: {
            topic: str,
            total_checked: int,
            high_similarity: [{title, score, risk}],
            medium_similarity: [{title, score, risk}],
            low_similarity_count: int,
            overall_risk: str,
            suggestions: [str]
        }
    """
    results_high = []
    results_medium = []
    results_low = 0

    for paper in papers:
        title = paper.get("title", "")
        abstract = paper.get("abstract", "") or ""
        paper_text = f"{title} {abstract}"

        score = compute_similarity(topic, paper_text)

        entry = {
            "title": title,
            "authors": paper.get("authors", [])[:3],
            "year": paper.get("year"),
            "similarity_score": score,
            "venue": paper.get("venue", ""),
            "doi": paper.get("doi", ""),
            "url": paper.get("url", ""),
        }

        if score >= threshold_high:
            entry["risk"] = "🔴 高风险 - 可能与已有工作高度重复"
            results_high.append(entry)
        elif score >= threshold_medium:
            entry["risk"] = "🟡 中风险 - 存在部分重叠，需差异化"
            results_medium.append(entry)
        else:
            results_low += 1

    # 按相似度排序
    results_high.sort(key=lambda x: x["similarity_score"], reverse=True)
    results_medium.sort(key=lambda x: x["similarity_score"], reverse=True)

    # 总体风险评估
    if len(results_high) >= 3:
        overall_risk = "🔴 高风险"
        risk_desc = "检测到多篇高度相似文献，建议重新考虑选题方向或寻找差异化切入点"
    elif len(results_high) >= 1:
        overall_risk = "🟡 中风险"
        risk_desc = "存在高度相似文献，建议明确与已有工作的区别和创新点"
    elif len(results_medium) >= 5:
        overall_risk = "🟡 中风险"
        risk_desc = "中等相似文献较多，建议进一步细化选题方向"
    else:
        overall_risk = "🟢 低风险"
        risk_desc = "未检测到高度重复，选题具有一定新颖性"

    # 生成建议
    suggestions = []
    if results_high:
        suggestions.append(f"有 {len(results_high)} 篇文献与你的选题高度相似，建议仔细阅读并明确差异化")
        suggestions.append("考虑从以下角度差异化：新数据集、新方法、新应用场景、新评价指标")
    if results_medium:
        suggestions.append(f"有 {len(results_medium)} 篇文献存在部分重叠，注意避免方法上的重复")
    if not results_high and not results_medium:
        suggestions.append("选题新颖性较好，建议进一步通过文献综述确认研究空白")
    suggestions.append("建议结合 GAP 分析结果，选择饱和度低的方向")

    return {
        "topic": topic,
        "total_checked": len(papers),
        "high_similarity": results_high[:5],
        "medium_similarity": results_medium[:10],
        "low_similarity_count": results_low,
        "overall_risk": overall_risk,
        "risk_description": risk_desc,
        "suggestions": suggestions,
    }


def format_similarity_report(result):
    """格式化相似度检测报告为 Markdown"""
    lines = [f"## 选题相似度检测: 「{result['topic']}」\n"]
    lines.append(f"**检测文献数**: {result['total_checked']} 篇")
    lines.append(f"**总体风险评估**: {result['overall_risk']}")
    lines.append(f"**评估说明**: {result['risk_description']}\n")

    # 高相似度
    if result.get("high_similarity"):
        lines.append("### 🔴 高度相似文献（需重点关注）\n")
        lines.append("| 相似度 | 标题 | 作者 | 年份 | 期刊/会议 |")
        lines.append("|--------|------|------|------|----------|")
        for item in result["high_similarity"]:
            score = f"{item['similarity_score']:.1%}"
            title = item["title"][:40] + "..." if len(item["title"]) > 40 else item["title"]
            authors = ", ".join(item.get("authors", [])[:2])
            if len(item.get("authors", [])) > 2:
                authors += " 等"
            year = item.get("year") or "N/A"
            venue = (item.get("venue", "") or "N/A")[:20]
            lines.append(f"| {score} | {title} | {authors} | {year} | {venue} |")
        lines.append("")

    # 中等相似度
    if result.get("medium_similarity"):
        lines.append("### 🟡 中等相似文献（需注意差异化）\n")
        lines.append("| 相似度 | 标题 | 年份 |")
        lines.append("|--------|------|------|")
        for item in result["medium_similarity"][:5]:
            score = f"{item['similarity_score']:.1%}"
            title = item["title"][:50] + "..." if len(item["title"]) > 50 else item["title"]
            year = item.get("year") or "N/A"
            lines.append(f"| {score} | {title} | {year} |")
        lines.append("")

    # 建议
    if result.get("suggestions"):
        lines.append("### 💡 建议\n")
        for i, s in enumerate(result["suggestions"], 1):
            lines.append(f"{i}. {s}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Research Copilot - 选题相似度检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 check_similarity.py --topic "基于深度学习的医学图像分割" --query "deep learning medical image segmentation"
  python3 check_similarity.py --topic "多模态大模型在教育中的应用" --query "multimodal LLM education" --limit 20
  # 从文件读取已有文献
  python3 check_similarity.py --topic "联邦学习隐私保护" --input papers.json
        """,
    )
    parser.add_argument("--topic", "-t", required=True, help="拟选题目")
    parser.add_argument("--query", "-q", help="用于检索相关文献的关键词（与 --input 二选一）")
    parser.add_argument("--input", "-i", help="已有文献 JSON 文件路径（来自 search_papers 输出）")
    parser.add_argument("--year-from", "-yf", type=int, help="起始年份")
    parser.add_argument("--limit", "-l", type=int, default=20, help="检索文献数量（默认20）")
    parser.add_argument("--format", "-f", choices=["json", "report"], default="json")

    args = parser.parse_args()

    if not args.query and not args.input:
        parser.error("请提供 --query（搜索关键词）或 --input（文献文件）")

    # 获取文献数据
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)
            papers = data if isinstance(data, list) else data.get("papers", [])
            print(f"从文件加载了 {len(papers)} 篇文献", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 无法读取文件: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 调用 search_papers 获取文献
        import subprocess
        cmd = [
            "python3", "scripts/search_papers.py",
            "--query", args.query,
            "--limit", str(args.limit),
        ]
        if args.year_from:
            cmd.extend(["--year-from", str(args.year_from)])

        print(f"正在检索相关文献以进行相似度比对...", file=sys.stderr)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[WARN] 文献检索失败: {result.stderr}", file=sys.stderr)
                print("[WARN] 将使用空文献列表进行演示", file=sys.stderr)
                papers = []
            else:
                data = json.loads(result.stdout)
                papers = data.get("papers", [])
                print(f"检索到 {len(papers)} 篇文献", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 检索失败: {e}", file=sys.stderr)
            papers = []

    # 执行相似度检测
    print(f"正在检测选题「{args.topic}」的相似度...", file=sys.stderr)

    result = check_topic_similarity(args.topic, papers)

    if args.format == "report":
        print(format_similarity_report(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
