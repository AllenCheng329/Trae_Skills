#!/usr/bin/env python3
"""
Research Copilot - 多源学术文献检索脚本
功能：从多个学术数据库检索论文，自动处理限流和降级
支持数据源：Semantic Scholar → CrossRef → PubMed → OpenAlex → arXiv
特性：
  - 多源自动降级：当某API限流时自动切换到备用源
  - WebSearch降级建议：当所有API都不可用时返回WebSearch查询建议
  - PubMed支持：医学/生物医学文献检索
用法：
  python3 search_papers.py --query "transformer attention" --year-from 2020 --limit 10
  python3 search_papers.py --query "medical image" --source pubmed --limit 20
  python3 search_papers.py --query "deep learning" --fallback  # 启用自动降级
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import time
import re
import xml.etree.ElementTree as ET

# ============== 配置 ==============
RATE_LIMIT_DELAY = 3.0  # 请求间隔（秒）
MAX_RETRIES = 2         # 最大重试次数
TIMEOUT = 20            # 请求超时（秒）

# API 端点
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
CROSSREF_BASE = "https://api.crossref.org/works"
OPENALEX_BASE = "https://api.openalex.org/works"
ARXIV_BASE = "http://export.arxiv.org/api/query"
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# 默认字段
SS_FIELDS = "title,abstract,citationCount,year,authors,externalIds,openAccessPdf,url,venue,fieldsOfStudy,tldr"


# ============== 限流检测 ==============
class RateLimitHandler:
    """限流处理器：记录各 API 的限流状态"""
    
    def __init__(self):
        self.blocked = {}  # {api_name: unblock_time}
    
    def is_blocked(self, api_name):
        """检查 API 是否被限流"""
        if api_name in self.blocked:
            if time.time() < self.blocked[api_name]:
                return True
            else:
                del self.blocked[api_name]
        return False
    
    def mark_blocked(self, api_name, wait_seconds=60):
        """标记 API 被限流"""
        self.blocked[api_name] = time.time() + wait_seconds
        print(f"[WARN] {api_name} 被限流，{wait_seconds}秒后重试", file=sys.stderr)
    
    def get_available(self, preferred_order):
        """获取第一个可用的 API"""
        for api in preferred_order:
            if not self.is_blocked(api):
                return api
        return None


rate_handler = RateLimitHandler()


# ============== Semantic Scholar ==============
def search_semantic_scholar(query, year_from=None, year_to=None, limit=10, sort="citation_count"):
    """Semantic Scholar API 检索"""
    if rate_handler.is_blocked("semantic_scholar"):
        return None
    
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": SS_FIELDS,
    }
    if year_from and year_to:
        params["year"] = f"{year_from}-{year_to}"
    elif year_from:
        params["year"] = f"{year_from}-"
    
    sort_map = {
        "citation_count": "citationCount:desc",
        "relevance": "relevance",
        "year": "publicationDate:desc",
    }
    params["sort"] = sort_map.get(sort, "citationCount:desc")
    
    url = f"{SEMANTIC_SCHOLAR_BASE}/paper/search?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "ResearchCopilot/2.0 (Academic Research Tool)")
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        papers = []
        for p in data.get("data", []):
            authors = [a.get("name", "") for a in p.get("authors", []) if a.get("name")]
            ext_ids = p.get("externalIds", {}) or {}
            papers.append({
                "title": p.get("title", "N/A"),
                "authors": authors[:5],
                "year": p.get("year"),
                "citation_count": p.get("citationCount", 0),
                "venue": p.get("venue", ""),
                "abstract": (p.get("abstract") or "")[:500],
                "tldr": (p.get("tldr", {}) or {}).get("text", ""),
                "doi": ext_ids.get("DOI", ""),
                "arxiv_id": ext_ids.get("ArXiv", ""),
                "pubmed_id": ext_ids.get("PubMed", ""),
                "url": p.get("url", ""),
                "pdf_url": (p.get("openAccessPdf") or {}).get("url", ""),
                "source": "Semantic Scholar",
            })
        
        return {"total": data.get("total", 0), "papers": papers, "source": "Semantic Scholar"}
    
    except urllib.error.HTTPError as e:
        if e.code == 429:
            rate_handler.mark_blocked("semantic_scholar", 60)
            return None
        return {"error": f"HTTP {e.code}: {e.reason}", "total": 0, "papers": []}
    except Exception as e:
        return {"error": str(e), "total": 0, "papers": []}


# ============== CrossRef ==============
def search_crossref(query, year_from=None, year_to=None, limit=10):
    """CrossRef API 检索"""
    if rate_handler.is_blocked("crossref"):
        return None
    
    filters = []
    if year_from:
        filters.append(f"from-pub-date:{year_from}")
    if year_to:
        filters.append(f"until-pub-date:{year_to}")
    filters.append("type:journal-article")
    
    params = {
        "query": query,
        "rows": min(limit, 100),
        "sort": "is-referenced-by-count",
        "order": "desc",
        "select": "DOI,title,author,published,abstract,container-title,is-referenced-by-count,URL",
    }
    if filters:
        params["filter"] = ",".join(filters)
    
    url = f"{CROSSREF_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "ResearchCopilot/2.0 (mailto:research@example.com)")
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        papers = []
        items = data.get("message", {}).get("items", [])
        for item in items:
            authors = []
            for a in item.get("author", []):
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    authors.append(name)
            
            year = None
            pub_date = item.get("published", {}).get("date-parts", [[]])
            if pub_date and pub_date[0]:
                year = pub_date[0][0]
            
            # 清理 abstract 中的 HTML 标签
            abstract = item.get("abstract", "") or ""
            abstract = re.sub(r'<[^>]+>', '', abstract)[:500]
            
            papers.append({
                "title": (item.get("title") or ["N/A"])[0],
                "authors": authors[:5],
                "year": year,
                "citation_count": item.get("is-referenced-by-count", 0),
                "venue": (item.get("container-title") or [""])[0],
                "abstract": abstract,
                "doi": item.get("DOI", ""),
                "url": item.get("URL", ""),
                "pdf_url": "",
                "source": "CrossRef",
            })
        
        total = data.get("message", {}).get("total-results", 0)
        return {"total": total, "papers": papers, "source": "CrossRef"}
    
    except urllib.error.HTTPError as e:
        if e.code == 429:
            rate_handler.mark_blocked("crossref", 30)
            return None
        return {"error": f"HTTP {e.code}: {e.reason}", "total": 0, "papers": []}
    except Exception as e:
        return {"error": str(e), "total": 0, "papers": []}


# ============== OpenAlex ==============
def search_openalex(query, year_from=None, year_to=None, limit=10):
    """OpenAlex API 检索"""
    if rate_handler.is_blocked("openalex"):
        return None
    
    filters = []
    if year_from:
        filters.append(f"publication_year:>={year_from}")
    if year_to:
        filters.append(f"publication_year:<={year_to}")
    
    params = {
        "search": query,
        "per_page": min(limit, 100),
        "sort": "cited_by_count:desc",
        "select": "id,doi,title,authorships,publication_year,cited_by_count,primary_location,abstract_inverted_index",
    }
    if filters:
        params["filter"] = ",".join(filters)
    
    url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "ResearchCopilot/2.0")
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        papers = []
        for item in data.get("results", []):
            authors = []
            for a in item.get("authorships", []):
                name = a.get("author", {}).get("name", "")
                if name:
                    authors.append(name)
            
            # 从 inverted index 恢复 abstract
            abstract = ""
            inv_idx = item.get("abstract_inverted_index", {})
            if inv_idx:
                positions = {}
                for word, pos_list in inv_idx.items():
                    for pos in pos_list:
                        positions[pos] = word
                abstract = " ".join(positions[i] for i in sorted(positions.keys())[:100])
            
            loc = item.get("primary_location", {}) or {}
            source = loc.get("source", {}) or {}
            
            papers.append({
                "title": item.get("title", "N/A"),
                "authors": authors[:5],
                "year": item.get("publication_year"),
                "citation_count": item.get("cited_by_count", 0),
                "venue": source.get("display_name", ""),
                "abstract": abstract[:500],
                "doi": (item.get("doi") or "").replace("https://doi.org/", ""),
                "url": item.get("doi", ""),
                "pdf_url": (loc.get("pdf_url") or ""),
                "source": "OpenAlex",
            })
        
        total = data.get("meta", {}).get("count", 0)
        return {"total": total, "papers": papers, "source": "OpenAlex"}
    
    except urllib.error.HTTPError as e:
        if e.code == 429:
            rate_handler.mark_blocked("openalex", 30)
            return None
        return {"error": f"HTTP {e.code}: {e.reason}", "total": 0, "papers": []}
    except Exception as e:
        return {"error": str(e), "total": 0, "papers": []}


# ============== arXiv ==============
def search_arxiv(query, year_from=None, year_to=None, limit=10):
    """arXiv API 检索（返回 Atom XML）"""
    if rate_handler.is_blocked("arxiv"):
        return None
    
    # arXiv 分类映射
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 100),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    
    url = f"{ARXIV_BASE}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "ResearchCopilot/2.0")
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            xml_content = resp.read().decode("utf-8")
        
        # 解析 Atom XML
        root = ET.fromstring(xml_content)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        
        papers = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            link = entry.find("atom:link[@title='html']", ns)
            pdf_link = entry.find("atom:link[@title='pdf']", ns)
            
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text)
            
            # 提取 arXiv ID
            entry_id = entry.find("atom:id", ns)
            arxiv_id = ""
            if entry_id is not None:
                match = re.search(r'(\d{4}\.\d{4,5})', entry_id.text)
                if match:
                    arxiv_id = match.group(1)
            
            year = None
            if published is not None:
                year = int(published.text[:4])
            
            # 年份过滤
            if year_from and year and year < year_from:
                continue
            if year_to and year and year > year_to:
                continue
            
            papers.append({
                "title": title.text if title is not None else "N/A",
                "authors": authors[:5],
                "year": year,
                "citation_count": 0,  # arXiv 不提供引用数
                "venue": "arXiv",
                "abstract": (summary.text or "")[:500] if summary is not None else "",
                "arxiv_id": arxiv_id,
                "url": link.get("href", "") if link is not None else "",
                "pdf_url": pdf_link.get("href", "") if pdf_link is not None else "",
                "source": "arXiv",
            })
        
        return {"total": len(papers), "papers": papers, "source": "arXiv"}
    
    except Exception as e:
        return {"error": str(e), "total": 0, "papers": []}


# ============== PubMed/NCBI ==============
def search_pubmed(query, year_from=None, year_to=None, limit=10):
    """PubMed/NCBI E-utilities API 检索（医学/生物医学文献）"""
    if rate_handler.is_blocked("pubmed"):
        return None
    
    # 构建日期范围查询
    date_filter = ""
    if year_from and year_to:
        date_filter = f" AND {year_from}:{year_to}[pdat]"
    elif year_from:
        date_filter = f" AND {year_from}:3000[pdat]"
    
    # 步骤1: esearch 获取 PMID 列表
    search_params = {
        "db": "pubmed",
        "term": f"{query}{date_filter}",
        "retmax": min(limit, 100),
        "retmode": "json",
        "sort": "relevance",
    }
    
    try:
        # 搜索获取PMID列表
        search_url = f"{PUBMED_ESEARCH}?{urllib.parse.urlencode(search_params)}"
        req = urllib.request.Request(search_url)
        req.add_header("User-Agent", "ResearchCopilot/2.0 (mailto:research@example.com)")
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            search_data = json.loads(resp.read().decode("utf-8"))
        
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return {"total": 0, "papers": [], "source": "PubMed"}
        
        # 步骤2: esummary 获取文献摘要信息
        summary_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
        
        summary_url = f"{PUBMED_ESUMMARY}?{urllib.parse.urlencode(summary_params)}"
        req = urllib.request.Request(summary_url)
        req.add_header("User-Agent", "ResearchCopilot/2.0 (mailto:research@example.com)")
        
        time.sleep(0.4)  # NCBI 要求每秒不超过3次请求
        
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            summary_data = json.loads(resp.read().decode("utf-8"))
        
        papers = []
        result = summary_data.get("result", {})
        
        for pmid in pmids:
            item = result.get(pmid, {})
            if not item or "error" in item:
                continue
            
            # 解析作者
            authors = []
            for author in item.get("authors", []):
                name = author.get("name", "")
                if name:
                    authors.append(name)
            
            # 解析年份
            year = None
            pub_date = item.get("pubdate", "")
            if pub_date:
                match = re.search(r'(\d{4})', pub_date)
                if match:
                    year = int(match.group(1))
            
            # 解析期刊
            venue = ""
            source_info = item.get("source", "")
            if source_info:
                venue = source_info.split(".")[0] if "." in source_info else source_info
            
            papers.append({
                "title": item.get("title", "N/A"),
                "authors": authors[:5],
                "year": year,
                "citation_count": item.get("pmc_cited_count", 0) or 0,
                "venue": venue[:50],
                "abstract": "",  # esummary 不返回摘要，需要 efetch
                "doi": item.get("elocationid", "").replace("doi: ", "") if "doi:" in item.get("elocationid", "") else "",
                "pubmed_id": pmid,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "pdf_url": "",
                "source": "PubMed",
            })
        
        total = int(search_data.get("esearchresult", {}).get("count", 0))
        return {"total": total, "papers": papers, "source": "PubMed"}
    
    except urllib.error.HTTPError as e:
        if e.code == 429:
            rate_handler.mark_blocked("pubmed", 60)
            return None
        return {"error": f"HTTP {e.code}: {e.reason}", "total": 0, "papers": []}
    except Exception as e:
        return {"error": str(e), "total": 0, "papers": []}


# ============== 统一检索接口 ==============
def search_papers(query, year_from=None, year_to=None, limit=10, 
                  sort="citation_count", source="auto", fallback=True):
    """
    统一检索接口
    
    参数:
        source: 指定数据源 (semantic_scholar / crossref / openalex / arxiv / pubmed / auto)
        fallback: 是否在限流时自动降级到其他数据源
    
    返回:
        成功时返回 {"total": int, "papers": list, "source": str}
        失败时返回 {"error": str, "total": 0, "papers": [], "suggestion": str, "use_websearch": True}
    """
    # 数据源优先级（PubMed 对医学文献特别重要）
    sources_order = ["semantic_scholar", "crossref", "pubmed", "openalex", "arxiv"]
    
    if source != "auto":
        sources_order = [source]
    
    results = []
    errors = []
    all_blocked = True
    
    for src in sources_order:
        if rate_handler.is_blocked(src):
            errors.append(f"{src}: 被限流")
            continue
        
        all_blocked = False
        print(f"[INFO] 尝试 {src}...", file=sys.stderr)
        
        if src == "semantic_scholar":
            result = search_semantic_scholar(query, year_from, year_to, limit, sort)
        elif src == "crossref":
            result = search_crossref(query, year_from, year_to, limit)
        elif src == "pubmed":
            result = search_pubmed(query, year_from, year_to, limit)
        elif src == "openalex":
            result = search_openalex(query, year_from, year_to, limit)
        elif src == "arxiv":
            result = search_arxiv(query, year_from, year_to, limit)
        else:
            continue
        
        if result is None:
            # 被限流，继续尝试下一个
            errors.append(f"{src}: 被限流")
            continue
        
        if "error" in result:
            errors.append(f"{src}: {result['error']}")
            if not fallback:
                return result
            continue
        
        if result.get("papers"):
            result["sources_tried"] = sources_order[:sources_order.index(src) + 1]
            return result
    
    # 所有数据源都失败 - 返回 WebSearch 降级建议
    if all_blocked or errors:
        return {
            "error": "所有API数据源均被限流或不可用",
            "total": 0, 
            "papers": [], 
            "suggestion": "建议使用 WebSearch 工具直接搜索学术文献",
            "use_websearch": True,
            "websearch_query": f'学术论文 {query} site:semanticscholar.org OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov',
            "errors": errors
        }
    return {"error": "未找到相关文献", "total": 0, "papers": []}


# ============== 格式化输出 ==============
def format_papers_table(result):
    """格式化为 Markdown 表格"""
    papers = result.get("papers", [])
    total = result.get("total", 0)
    source = result.get("source", "未知")
    
    if not papers:
        suggestion = result.get("suggestion", "")
        return f"未找到相关论文（总计: {total}）\n{suggestion}"
    
    lines = [f"共找到 **{total:,}** 篇相关论文（数据源: {source}），以下为 Top {len(papers)}：\n"]
    lines.append("| # | 标题 | 作者 | 年份 | 引用数 | 来源 |")
    lines.append("|---|------|------|------|--------|------|")
    
    for i, p in enumerate(papers, 1):
        title = p["title"][:50] + "..." if len(p["title"]) > 50 else p["title"]
        authors = ", ".join(p["authors"][:2])
        if len(p["authors"]) > 2:
            authors += " et al."
        year = p.get("year") or "N/A"
        citations = p.get("citation_count", 0) or 0
        venue = p.get("venue", "")[:20] or "N/A"
        lines.append(f"| {i} | {title} | {authors} | {year} | {citations:,} | {venue} |")
    
    return "\n".join(lines)


# ============== 主函数 ==============
def main():
    parser = argparse.ArgumentParser(
        description="Research Copilot - 多源学术文献检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 search_papers.py --query "transformer attention" --year-from 2020 --limit 10
  python3 search_papers.py --query "medical image" --source crossref
  python3 search_papers.py --query "deep learning" --fallback
        """
    )
    parser.add_argument("--query", "-q", required=True, help="搜索关键词")
    parser.add_argument("--year-from", "-yf", type=int, help="起始年份")
    parser.add_argument("--year-to", "-yt", type=int, help="结束年份")
    parser.add_argument("--limit", "-l", type=int, default=10, help="返回数量")
    parser.add_argument("--sort", "-s", choices=["citation_count", "relevance", "year"],
                        default="citation_count", help="排序方式")
    parser.add_argument("--source", choices=["auto", "semantic_scholar", "crossref", "pubmed", "openalex", "arxiv"],
                        default="auto", help="指定数据源")
    parser.add_argument("--fallback", action=argparse.BooleanOptionalAction, default=True, help="自动降级（默认开启，--no-fallback 关闭）")
    parser.add_argument("--format", "-f", choices=["json", "table"], default="json")
    
    args = parser.parse_args()
    
    result = search_papers(
        query=args.query,
        year_from=args.year_from,
        year_to=args.year_to,
        limit=args.limit,
        sort=args.sort,
        source=args.source,
        fallback=args.fallback,
    )
    
    if "error" in result and not result.get("papers"):
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    if args.format == "table":
        print(format_papers_table(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
