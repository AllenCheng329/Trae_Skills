#!/usr/bin/env python3
"""
Research Copilot - 引用格式化脚本
功能：将文献列表格式化为标准引用格式（GB/T 7714, APA, IEEE, BibTeX）
用法：
  echo '[{"title":"...","authors":["A","B"],"year":2023,"venue":"CVPR"}]' | python3 format_citations.py --style gb
  python3 format_citations.py --input papers.json --style apa
"""

import argparse
import json
import sys


def format_gb7714(papers):
    """GB/T 7714 格式（中国国标）"""
    results = []
    for i, p in enumerate(papers, 1):
        authors = p.get("authors", [])
        if len(authors) <= 3:
            author_str = ", ".join(authors)
        else:
            author_str = ", ".join(authors[:3]) + ", 等"

        title = p.get("title", "N/A")
        year = p.get("year", "N/A")
        venue = p.get("venue", "")
        doi = p.get("doi", "")

        ref = f"[{i}] {author_str}. {title}[J]. {venue}, {year}."
        if doi:
            ref += f" DOI: {doi}"
        results.append(ref)
    return results


def format_apa(papers):
    """APA 第7版格式"""
    results = []
    for p in papers:
        authors = p.get("authors", [])
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]}, & {authors[1]}"
        elif len(authors) <= 20:
            author_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
        else:
            author_str = ", ".join(authors[:19]) + ", ... & " + authors[-1]

        title = p.get("title", "N/A")
        year = p.get("year", "N/A")
        venue = p.get("venue", "")
        doi = p.get("doi", "")

        ref = f"{author_str} ({year}). {title}. *{venue}*."
        if doi:
            ref += f" https://doi.org/{doi}"
        results.append(ref)
    return results


def format_ieee(papers):
    """IEEE 格式"""
    results = []
    for i, p in enumerate(papers, 1):
        authors = p.get("authors", [])
        if len(authors) <= 6:
            author_str = ", ".join(authors)
        else:
            author_str = ", ".join(authors[:6]) + ", et al."

        title = p.get("title", "N/A")
        year = p.get("year", "N/A")
        venue = p.get("venue", "")
        doi = p.get("doi", "")

        ref = f'[{i}] {author_str}, "{title}," in *Proc. {venue}*, {year}.'
        if doi:
            ref += f" doi: {doi}"
        results.append(ref)
    return results


def format_bibtex(papers):
    """BibTeX 格式"""
    results = []
    for i, p in enumerate(papers):
        # 生成 citation key
        authors = p.get("authors", [])
        year = p.get("year", "XXXX")
        first_author = authors[0].split()[-1].lower() if authors else "unknown"
        # 移除标题中的特殊字符
        title_words = p.get("title", "").lower().split()[:3]
        key_words = "".join(w for w in title_words if w.isalpha())
        cite_key = f"{first_author}{year}{key_words}"

        venue = p.get("venue", "")
        doi = p.get("doi", "")
        url = p.get("url", "")

        # 判断类型
        pub_type = "article"
        if "conference" in venue.lower() or any(x in venue for x in ["CVPR", "ICML", "NeurIPS", "ACL", "ICCV", "ECCV", "AAAI", "IJCAI", "MICCAI"]):
            pub_type = "inproceedings"

        entry = f"@{pub_type}{{{cite_key},\n"
        entry += f"  title = {{{p.get('title', 'N/A')}}},\n"
        entry += f"  author = {{{' and '.join(authors)}}},\n"
        entry += f"  year = {{{year}}},\n"
        if venue:
            entry += f"  booktitle = {{{venue}}},\n" if pub_type == "inproceedings" else f"  journal = {{{venue}}},\n"
        if doi:
            entry += f"  doi = {{{doi}}},\n"
        if url:
            entry += f"  url = {{{url}}},\n"
        entry += "}"
        results.append(entry)
    return results


def main():
    parser = argparse.ArgumentParser(description="Research Copilot - 引用格式化")
    parser.add_argument("--input", "-i", help="输入 JSON 文件路径（不指定则从 stdin 读取）")
    parser.add_argument("--style", "-s", choices=["gb", "apa", "ieee", "bibtex"],
                        default="gb", help="引用格式（默认 gb 即 GB/T 7714）")

    args = parser.parse_args()

    # 读取输入
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # 兼容 search_papers 的输出格式
    if isinstance(data, dict) and "papers" in data:
        papers = data["papers"]
    elif isinstance(data, list):
        papers = data
    else:
        print("错误: 输入必须是 JSON 数组或包含 'papers' 字段的对象", file=sys.stderr)
        sys.exit(1)

    # 格式化
    formatters = {
        "gb": format_gb7714,
        "apa": format_apa,
        "ieee": format_ieee,
        "bibtex": format_bibtex,
    }

    formatter = formatters[args.style]
    results = formatter(papers)

    print("\n\n".join(results))


if __name__ == "__main__":
    main()
