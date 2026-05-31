#!/usr/bin/env python3
"""
Research Copilot - 中文文献检索脚本
功能：通过 WebSearch 检索中文学术文献（知网/万方/百度学术）
说明：由于知网/万方无公开免费API，本脚本通过 WebSearch 工具间接检索
用法：
  python3 search_chinese.py --query "深度学习 医学图像" --year-from 2022 --limit 10
  python3 search_chinese.py --query "自然语言处理" --source cnki --limit 15
"""

import argparse
import json
import sys
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET


# ============== 配置 ==============
TIMEOUT = 15
MAX_RETRIES = 2

# 中文数据库搜索URL模板
SEARCH_TEMPLATES = {
    "cnki": "https://scholar.cnki.net/home/search?q={query}&p={page}&t=article",
    "wanfang": "https://s.wanfangdata.com.cn/paper?q={query}&style=detail",
    "baidu": "https://xueshu.baidu.com/s?wd={query}&ie=utf-8",
}

# 学术搜索引擎（有API的）
GOOGLE_SCHOLAR_BASE = "http://export.arxiv.org/api/query"  # arXiv支持中文标题
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"


def search_cnki_web(query, year_from=None, limit=10):
    """
    通过 WebSearch 风格的查询检索知网文献
    返回搜索建议URL，由模型调用 WebSearch 工具执行
    """
    year_filter = ""
    if year_from:
        year_filter = f" {year_from}-{time.strftime('%Y')}"

    # 构造多个搜索建议
    suggestions = []

    # 知网搜索
    cnki_query = f"{query}{year_filter}"
    suggestions.append({
        "source": "中国知网(CNKI)",
        "url": f"https://scholar.cnki.net/home/search?q={urllib.parse.quote(cnki_query)}",
        "websearch_query": f'知网 {query} site:cnki.net',
    })

    # 万方搜索
    suggestions.append({
        "source": "万方数据",
        "url": f"https://s.wanfangdata.com.cn/paper?q={urllib.parse.quote(query)}",
        "websearch_query": f'万方 {query} site:wanfangdata.com.cn',
    })

    # 百度学术
    suggestions.append({
        "source": "百度学术",
        "url": f"https://xueshu.baidu.com/s?wd={urllib.parse.quote(query)}&ie=utf-8",
        "websearch_query": f'学术论文 "{query}" site:xueshu.baidu.com',
    })

    # Google Scholar 中文
    suggestions.append({
        "source": "Google Scholar",
        "url": f"https://scholar.google.com/scholar?q={urllib.parse.quote(query)}&hl=zh-CN",
        "websearch_query": f'"{query}" 论文 filetype:pdf',
    })

    return {
        "query": query,
        "type": "chinese_literature",
        "suggestions": suggestions,
        "note": "请使用 WebSearch 工具执行上述查询，或直接访问URL",
        "recommended_query": f'学术论文 "{query}" site:cnki.net OR site:wanfangdata.com.cn OR site:xueshu.baidu.com',
    }


def search_semantic_scholar_chinese(query, year_from=None, limit=10):
    """
    通过 Semantic Scholar 搜索中文论文（部分中文论文有英文索引）
    """
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,abstract,citationCount,year,authors,venue,externalIds,url",
        "sort": "citationCount:desc",
    }
    if year_from:
        params["year"] = f"{year_from}-"

    url = f"{SEMANTIC_SCHOLAR_BASE}/paper/search?{urllib.parse.urlencode(params)}"

    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "ResearchCopilot/3.0 (Academic Research Tool)")
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            papers = []
            for p in data.get("data", []):
                title = p.get("title", "")
                # 检测是否包含中文
                has_chinese = bool(re.search(r'[\u4e00-\u9fff]', title + (p.get("abstract") or "")))
                if has_chinese or not papers:  # 优先中文论文，但也保留英文
                    authors = [a.get("name", "") for a in p.get("authors", []) if a.get("name")]
                    ext_ids = p.get("externalIds", {}) or {}
                    papers.append({
                        "title": title,
                        "authors": authors[:5],
                        "year": p.get("year"),
                        "citation_count": p.get("citationCount", 0),
                        "venue": p.get("venue", ""),
                        "abstract": (p.get("abstract") or "")[:500],
                        "doi": ext_ids.get("DOI", ""),
                        "url": p.get("url", ""),
                        "source": "Semantic Scholar",
                        "is_chinese": has_chinese,
                    })

            return {
                "total": data.get("total", 0),
                "papers": papers[:limit],
                "source": "Semantic Scholar (中文筛选)",
                "chinese_count": sum(1 for p in papers if p.get("is_chinese")),
            }

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"[WARN] 限流(429)，等待 {wait}秒", file=sys.stderr)
                time.sleep(wait)
            else:
                return {"error": f"HTTP {e.code}", "total": 0, "papers": []}
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(3)
            else:
                return {"error": str(e), "total": 0, "papers": []}

    return {"error": "请求失败", "total": 0, "papers": []}


def search_chinese(query, year_from=None, limit=10, source="auto"):
    """
    统一中文文献检索接口

    参数:
        source: cnki (知网推荐) / semantic (Semantic Scholar中文) / auto (两者都返回)
    """
    results = {}

    if source in ("auto", "cnki"):
        results["web_suggestions"] = search_cnki_web(query, year_from, limit)

    if source in ("auto", "semantic"):
        results["semantic_scholar"] = search_semantic_scholar_chinese(query, year_from, limit)

    return results


def format_chinese_results(result):
    """格式化中文检索结果为 Markdown"""
    lines = [f"## 中文文献检索: 「{result.get('query', '')}」\n"]

    # Semantic Scholar 中文结果
    ss = result.get("semantic_scholar", {})
    if ss and ss.get("papers"):
        lines.append(f"### Semantic Scholar 中文论文（共 {ss.get('chinese_count', 0)} 篇中文）\n")
        lines.append("| # | 标题 | 作者 | 年份 | 引用数 | 期刊/会议 |")
        lines.append("|---|------|------|------|--------|----------|")
        for i, p in enumerate(ss["papers"], 1):
            title = p["title"][:40] + "..." if len(p["title"]) > 40 else p["title"]
            authors = ", ".join(p["authors"][:2])
            if len(p["authors"]) > 2:
                authors += " 等"
            year = p.get("year") or "N/A"
            citations = p.get("citation_count", 0) or 0
            venue = (p.get("venue", "") or "N/A")[:20]
            lines.append(f"| {i} | {title} | {authors} | {year} | {citations} | {venue} |")
        lines.append("")

    # WebSearch 建议
    web = result.get("web_suggestions", {})
    if web and web.get("suggestions"):
        lines.append("### 推荐搜索渠道\n")
        lines.append("以下数据库需要通过 WebSearch 工具或浏览器访问：\n")
        for s in web["suggestions"]:
            lines.append(f"- **{s['source']}**: {s['url']}")
        lines.append("")
        lines.append(f"**推荐 WebSearch 查询**:\n```\n{web.get('recommended_query', '')}\n```")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Research Copilot - 中文文献检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 search_chinese.py --query "深度学习 医学图像" --year-from 2022
  python3 search_chinese.py --query "自然语言处理" --source cnki
  python3 search_chinese.py --query "知识图谱" --source semantic --limit 15
        """,
    )
    parser.add_argument("--query", "-q", required=True, help="搜索关键词（中文）")
    parser.add_argument("--year-from", "-yf", type=int, help="起始年份")
    parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量（默认10）")
    parser.add_argument("--source", "-s", choices=["auto", "cnki", "semantic"],
                        default="auto", help="数据源：auto/cnki/semantic")
    parser.add_argument("--format", "-f", choices=["json", "table"], default="json")

    args = parser.parse_args()

    print(f"正在检索中文文献「{args.query}」...", file=sys.stderr)

    result = search_chinese(
        query=args.query,
        year_from=args.year_from,
        limit=args.limit,
        source=args.source,
    )

    if args.format == "table":
        print(format_chinese_results(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
