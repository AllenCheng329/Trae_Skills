#!/usr/bin/env python3
"""
Research Copilot - 研究趋势分析脚本
功能：基于检索结果分析研究趋势（年度分布、关键词频率、热点主题）
特性：限流保护、请求间隔、年份跨度上限、错误重试
用法：
  python3 analyze_trends.py --query "medical image analysis" --year-from 2020 --year-to 2024
  python3 analyze_trends.py --query "contrastive learning" --year-from 2019 --top-keywords 15
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import re
import time
from collections import Counter

API_BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,citationCount,year,authors,venue,fieldsOfStudy,tldr"

REQUEST_DELAY = 1.5    # 请求间隔（秒），避免触发限流
MAX_YEAR_SPAN = 6      # 年份跨度上限
MAX_RETRIES = 2        # 最大重试次数
TIMEOUT = 20           # 请求超时（秒）


def fetch_papers_by_year(query, year, limit=100):
    """获取某一年的论文（含限流保护和重试）"""
    params = {
        "query": query,
        "year": f"{year}-{year}",
        "limit": min(limit, 100),
        "fields": FIELDS,
        "sort": "citationCount:desc",
    }
    url = f"{API_BASE}/paper/search?{urllib.parse.urlencode(params)}"

    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "ResearchCopilot/3.0 (Academic Research Tool)")
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", []), data.get("total", 0)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"[WARN] Semantic Scholar 限流(429)，等待 {wait}秒后重试 (year={year}, attempt={attempt+1})", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"[ERROR] HTTP {e.code}: {e.reason} (year={year})", file=sys.stderr)
                return [], 0
        except Exception as e:
            print(f"[ERROR] 请求失败: {e} (year={year})", file=sys.stderr)
            if attempt < MAX_RETRIES:
                time.sleep(3)
            else:
                return [], 0

    return [], 0


def extract_keywords(papers, top_n=10):
    """从论文标题和摘要中提取高频关键词"""
    stopwords = set([
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
        "under", "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "because", "but", "and",
        "or", "if", "while", "about", "against", "this", "that", "these",
        "those", "it", "its", "we", "our", "you", "your", "he", "she", "they",
        "their", "what", "which", "who", "whom", "whose", "new", "based",
        "using", "used", "use", "propose", "proposed", "method", "methods",
        "approach", "result", "results", "show", "shows", "study", "model",
        "models", "data", "performance", "experiments", "experimental",
        "paper", "recent", "also", "two", "one", "three", "first", "second",
        "however", "therefore", "thus", "hence", "moreover", "furthermore",
        "although", "though", "even", "well", "often", "several", "many",
        "much", "different", "various", "specific", "particular", "general",
        "high", "low", "large", "small", "good", "best", "better",
        "的", "了", "在", "是", "和", "与", "对", "中", "为", "及", "等",
        "一种", "基于", "提出", "方法", "模型", "实验", "结果", "研究",
    ])

    words = Counter()
    for paper in papers:
        text = ""
        if paper.get("title"):
            text += " " + paper["title"]
        if paper.get("abstract"):
            text += " " + paper["abstract"]
        if paper.get("tldr", {}).get("text"):
            text += " " + paper["tldr"]["text"]

        en_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        for w in en_words:
            if w not in stopwords:
                words[w] += 1

    return words.most_common(top_n)


def analyze_trends(query, year_from, year_to, top_keywords=10):
    """分析研究趋势（含限流保护）"""
    trend_data = []
    all_papers = []
    grand_total = 0

    for year in range(year_from, year_to + 1):
        print(f"[INFO] 正在检索 {year} 年数据...", file=sys.stderr)
        papers, total = fetch_papers_by_year(query, year, limit=50)
        trend_data.append({
            "year": year,
            "count": len(papers),
            "total_in_db": total,
        })
        all_papers.extend(papers)
        grand_total += total

        # 请求间隔，避免限流
        if year < year_to:
            time.sleep(REQUEST_DELAY)

    # 计算增长率
    for i in range(1, len(trend_data)):
        prev = trend_data[i - 1]["total_in_db"]
        curr = trend_data[i]["total_in_db"]
        if prev > 0:
            trend_data[i]["growth_rate"] = round((curr - prev) / prev * 100, 1)
        else:
            trend_data[i]["growth_rate"] = None
    trend_data[0]["growth_rate"] = None

    keywords = extract_keywords(all_papers, top_keywords)

    venue_counter = Counter()
    for p in all_papers:
        v = p.get("venue", "")
        if v:
            venue_counter[v] += 1
    hot_venues = [{"venue": v, "count": c} for v, c in venue_counter.most_common(10)]

    field_counter = Counter()
    for p in all_papers:
        for f in p.get("fieldsOfStudy", []):
            if f:
                field_counter[f] += 1
    top_fields = [{"field": f, "count": c} for f, c in field_counter.most_common(10)]

    return {
        "query": query,
        "year_range": f"{year_from}-{year_to}",
        "grand_total": grand_total,
        "trend_data": trend_data,
        "top_keywords": [{"keyword": kw, "frequency": freq} for kw, freq in keywords],
        "hot_venues": hot_venues,
        "top_fields": top_fields,
    }


def format_trend_report(result):
    """格式化趋势报告为 Markdown"""
    lines = []
    lines.append(f"## 研究趋势分析: 「{result['query']}」")
    lines.append(f"**分析时间范围**: {result['year_range']}")
    lines.append(f"**数据库总量**: 约 {result['grand_total']:,} 篇\n")

    lines.append("### 年度发文趋势")
    lines.append("| 年份 | 数据库总量 | 增长率 | 趋势 |")
    lines.append("|------|-----------|--------|------|")
    for t in result["trend_data"]:
        growth = t["growth_rate"]
        if growth is None:
            growth_str = "-"
            trend_str = "基准年"
        elif growth > 30:
            growth_str = f"+{growth}%"
            trend_str = "🚀 快速上升"
        elif growth > 10:
            growth_str = f"+{growth}%"
            trend_str = "📈 上升"
        elif growth > 0:
            growth_str = f"+{growth}%"
            trend_str = "→ 平稳增长"
        elif growth == 0:
            growth_str = "0%"
            trend_str = "→ 持平"
        else:
            growth_str = f"{growth}%"
            trend_str = "📉 下降"
        lines.append(f"| {t['year']} | {t['total_in_db']:,} | {growth_str} | {trend_str} |")

    lines.append("\n### 热点关键词 TOP10")
    lines.append("| 排名 | 关键词 | 频次 |")
    lines.append("|------|--------|------|")
    for i, kw in enumerate(result["top_keywords"], 1):
        lines.append(f"| {i} | {kw['keyword']} | {kw['frequency']} |")

    if result["hot_venues"]:
        lines.append("\n### 热门发表渠道 TOP10")
        lines.append("| 排名 | 期刊/会议 | 论文数 |")
        lines.append("|------|----------|--------|")
        for i, v in enumerate(result["hot_venues"], 1):
            lines.append(f"| {i} | {v['venue']} | {v['count']} |")

    if result["top_fields"]:
        lines.append("\n### 涉及学科领域")
        lines.append("| 排名 | 领域 | 论文数 |")
        lines.append("|------|------|--------|")
        for i, f in enumerate(result["top_fields"], 1):
            lines.append(f"| {i} | {f['field']} | {f['count']} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Research Copilot - 研究趋势分析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--query", "-q", required=True, help="研究主题关键词")
    parser.add_argument("--year-from", "-yf", type=int, required=True, help="起始年份")
    parser.add_argument("--year-to", "-yt", type=int, required=True, help="结束年份")
    parser.add_argument("--top-keywords", "-k", type=int, default=10, help="关键词数量（默认10）")
    parser.add_argument("--format", "-f", choices=["json", "report"], default="json",
                        help="输出格式（默认 json）")

    args = parser.parse_args()

    # 年份跨度校验
    span = args.year_to - args.year_from + 1
    if span > MAX_YEAR_SPAN:
        print(f"[WARN] 年份跨度 {span} 年超过建议上限 {MAX_YEAR_SPAN} 年，可能导致限流", file=sys.stderr)
        print(f"[WARN] 建议缩小范围或分批分析", file=sys.stderr)

    print(f"正在分析「{args.query}」{args.year_from}-{args.year_to}年的研究趋势...", file=sys.stderr)

    result = analyze_trends(
        query=args.query,
        year_from=args.year_from,
        year_to=args.year_to,
        top_keywords=args.top_keywords,
    )

    if args.format == "report":
        print(format_trend_report(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
