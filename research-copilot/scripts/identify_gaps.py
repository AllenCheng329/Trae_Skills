#!/usr/bin/env python3
"""
Research Copilot - 研究空白(GAP)识别脚本
功能：基于文献检索结果，分析研究饱和度、识别空白领域
特性：限流保护、请求间隔、错误重试
用法：
  python3 identify_gaps.py --query "medical image analysis" --year-from 2020 --year-to 2024
  python3 identify_gaps.py --query "contrastive learning vision" --year-from 2022 --top-keywords 20
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
FIELDS = "title,abstract,citationCount,year,authors,venue,fieldsOfStudy,tldr,referenceCount"

MAX_RETRIES = 2
TIMEOUT = 20


def fetch_papers(query, year_from, year_to, limit=100):
    """获取论文列表（含限流保护和重试）"""
    params = {
        "query": query,
        "year": f"{year_from}-{year_to}",
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
                print(f"[WARN] Semantic Scholar 限流(429)，等待 {wait}秒后重试 (attempt={attempt+1})", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"[ERROR] HTTP {e.code}: {e.reason}", file=sys.stderr)
                return [], 0
        except Exception as e:
            print(f"[ERROR] 请求失败: {e}", file=sys.stderr)
            if attempt < MAX_RETRIES:
                time.sleep(3)
            else:
                return [], 0

    return [], 0


def extract_title_phrases(papers, min_freq=2):
    """从标题中提取高频短语（2-4词组合）"""
    phrases = Counter()
    for paper in papers:
        title = paper.get("title", "")
        if not title:
            continue
        # 转小写，提取词组
        words = re.findall(r'[a-zA-Z]{2,}', title.lower())
        # 提取2-3词组合
        for n in [2, 3]:
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i + n])
                phrases[phrase] += 1
    return {p: c for p, c in phrases.items() if c >= min_freq}


def extract_abstract_patterns(papers):
    """从摘要中提取研究模式（方法、任务、数据集）"""
    method_patterns = Counter()
    task_patterns = Counter()
    dataset_patterns = Counter()

    # 常见方法关键词
    method_keywords = [
        "transformer", "attention", "CNN", "RNN", "LSTM", "GAN", "VAE",
        "BERT", "GPT", "diffusion", "reinforcement learning", "graph neural",
        "contrastive learning", "self-supervised", "semi-supervised",
        "federated learning", "knowledge distillation", "meta-learning",
        "prompt", "fine-tuning", "pre-training", "transfer learning",
        "clustering", "classification", "regression", "segmentation",
        "detection", "generation", "encoder", "decoder", "autoencoder",
    ]

    # 常见任务关键词
    task_keywords = [
        "classification", "detection", "segmentation", "generation",
        "recognition", "prediction", "estimation", "clustering",
        "retrieval", "summarization", "translation", "question answering",
        "anomaly detection", "recommendation", "denoising",
        "registration", "localization", "tracking",
    ]

    # 常见数据集关键词
    dataset_keywords = [
        "ImageNet", "COCO", "VOC", "CIFAR", "MNIST",
        "MIMIC", "CheXpert", "IU X-Ray", "BRATS", "ISIC",
        "SQuAD", "GLUE", "SuperGLUE", "WikiText",
        "LibriSpeech", "CommonCrawl", "WMT",
    ]

    for paper in papers:
        abstract = (paper.get("abstract") or "").lower()
        title = (paper.get("title") or "").lower()
        text = title + " " + abstract

        for kw in method_keywords:
            if kw.lower() in text:
                method_patterns[kw] += 1

        for kw in task_keywords:
            if kw.lower() in text:
                task_patterns[kw] += 1

        for kw in dataset_keywords:
            if kw.lower() in text:
                dataset_patterns[kw] += 1

    return method_patterns, task_patterns, dataset_patterns


def analyze_recency(papers):
    """分析论文的时间分布，识别新兴和衰退主题"""
    if not papers:
        return {}

    year_counts = Counter()
    for p in papers:
        y = p.get("year")
        if y:
            year_counts[y] += 1

    years = sorted(year_counts.keys())
    if len(years) < 2:
        return {"trend": "insufficient_data"}

    recent = sum(year_counts.get(y, 0) for y in years[-2:])  # 最近2年
    earlier = sum(year_counts.get(y, 0) for y in years[:-2])  # 之前

    if earlier == 0:
        return {"trend": "emerging", "recent_count": recent}

    growth = (recent - earlier) / earlier * 100
    if growth > 50:
        return {"trend": "rapid_growth", "growth_pct": round(growth, 1)}
    elif growth > 10:
        return {"trend": "steady_growth", "growth_pct": round(growth, 1)}
    elif growth > -10:
        return {"trend": "stable", "growth_pct": round(growth, 1)}
    else:
        return {"trend": "declining", "growth_pct": round(growth, 1)}


def identify_gaps(query, year_from, year_to, top_n=10):
    """
    识别研究空白
    
    返回:
        dict: {
            saturated_areas: [...],
            emerging_areas: [...],
            research_gaps: [...],
            method_distribution: [...],
            task_distribution: [...],
            dataset_usage: [...]
        }
    """
    papers, total = fetch_papers(query, year_from, year_to, limit=100)

    if not papers:
        return {"error": "未找到相关论文", "total": total}

    # 提取标题短语（高频=饱和，低频=空白）
    title_phrases = extract_title_phrases(papers, min_freq=3)

    # 提取方法/任务/数据集分布
    methods, tasks, datasets = extract_abstract_patterns(papers)

    # 识别饱和领域（高频短语）
    sorted_phrases = sorted(title_phrases.items(), key=lambda x: x[1], reverse=True)
    saturated = []
    for phrase, count in sorted_phrases[:top_n]:
        saturated.append({
            "topic": phrase.title(),
            "frequency": count,
            "assessment": "高度饱和" if count > 10 else "较饱和",
        })

    # 识别新兴领域（近2年增长快的主题）
    recent_papers = [p for p in papers if p.get("year", 0) >= year_to - 1]
    older_papers = [p for p in papers if p.get("year", 0) < year_to - 1]

    recent_phrases = extract_title_phrases(recent_papers, min_freq=1)
    older_phrases = extract_title_phrases(older_papers, min_freq=1)

    emerging = []
    for phrase, count in recent_phrases.items():
        old_count = older_phrases.get(phrase, 0)
        if old_count == 0 and count >= 2:
            # 全新出现
            emerging.append({
                "topic": phrase.title(),
                "recent_count": count,
                "old_count": 0,
                "type": "全新方向",
                "opportunity_score": min(10, 5 + count),
            })
        elif old_count > 0 and count > old_count * 1.5:
            # 快速增长
            growth = round((count - old_count) / old_count * 100)
            emerging.append({
                "topic": phrase.title(),
                "recent_count": count,
                "old_count": old_count,
                "type": "快速增长",
                "growth_rate": growth,
                "opportunity_score": min(10, 4 + growth // 20),
            })

    emerging.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

    # 生成研究空白建议
    gaps = []
    for item in emerging[:5]:
        gap = {
            "description": f"「{item['topic']}」是一个值得关注的潜在研究方向",
            "evidence": f"近2年出现 {item['recent_count']} 次（之前仅 {item.get('old_count', 0)} 次）" if item.get('old_count', 0) > 0 else f"近2年新出现 {item['recent_count']} 次，之前未见",
            "opportunity_level": "高" if item.get("opportunity_score", 0) >= 7 else "中",
            "difficulty": "中" if item.get("opportunity_score", 0) >= 7 else "低-中",
        }
        gaps.append(gap)

    # 如果没有发现新兴方向，基于低频短语生成建议
    if not gaps:
        low_freq = [p for p, c in sorted_phrases if c <= 2]
        for phrase in low_freq[:3]:
            gaps.append({
                "description": f"「{phrase.title()}」研究较少，可能存在探索空间",
                "evidence": f"在检索结果中仅出现 {title_phrases[phrase]} 次",
                "opportunity_level": "中",
                "difficulty": "需进一步调研",
            })

    return {
        "query": query,
        "year_range": f"{year_from}-{year_to}",
        "total_papers_analyzed": len(papers),
        "total_in_database": total,
        "saturated_areas": saturated[:5],
        "emerging_areas": emerging[:5],
        "research_gaps": gaps,
        "method_distribution": [{"method": m, "count": c} for m, c in methods.most_common(10)],
        "task_distribution": [{"task": t, "count": c} for t, c in tasks.most_common(10)],
        "dataset_usage": [{"dataset": d, "count": c} for d, c in datasets.most_common(10)],
    }


def format_gap_report(result):
    """格式化GAP分析报告为 Markdown"""
    lines = []
    lines.append(f"## 研究空白(GAP)分析: 「{result['query']}」")
    lines.append(f"**分析范围**: {result['year_range']}（分析了 {result['total_papers_analyzed']} 篇论文）\n")

    # 饱和领域
    if result.get("saturated_areas"):
        lines.append("### ⚠️ 饱和领域（竞争激烈）")
        lines.append("以下主题已有大量研究，新手进入需谨慎：\n")
        for area in result["saturated_areas"]:
            bar = "█" * min(area["frequency"], 20)
            lines.append(f"- **{area['topic']}** `{bar}` ({area['frequency']}次) — {area['assessment']}")
        lines.append("")

    # 新兴领域
    if result.get("emerging_areas"):
        lines.append("### ✨ 新兴领域（值得关注）")
        lines.append("以下主题近年来快速增长，存在机会：\n")
        for area in result["emerging_areas"]:
            score = area.get("opportunity_score", "?")
            if area.get("type") == "全新方向":
                lines.append(f"- **{area['topic']}** 🔥 全新方向 | 近2年 {area['recent_count']} 次 | 机会评分: {score}/10")
            else:
                lines.append(f"- **{area['topic']}** 📈 快速增长(+{area.get('growth_rate', '?')}%) | 近2年 {area['recent_count']} 次 | 机会评分: {score}/10")
        lines.append("")

    # 研究空白
    if result.get("research_gaps"):
        lines.append("### 🎯 推荐研究方向")
        lines.append("")
        for i, gap in enumerate(result["research_gaps"], 1):
            lines.append(f"**方向{i}: {gap['description']}**")
            lines.append(f"- 证据: {gap['evidence']}")
            lines.append(f"- 机会程度: {gap['opportunity_level']}")
            lines.append(f"- 难度: {gap['difficulty']}")
            lines.append("")

    # 方法分布
    if result.get("method_distribution"):
        lines.append("### 常用方法分布")
        lines.append("| 方法 | 出现次数 |")
        lines.append("|------|---------|")
        for m in result["method_distribution"]:
            lines.append(f"| {m['method']} | {m['count']} |")
        lines.append("")

    # 任务分布
    if result.get("task_distribution"):
        lines.append("### 常见研究任务")
        lines.append("| 任务 | 出现次数 |")
        lines.append("|------|---------|")
        for t in result["task_distribution"]:
            lines.append(f"| {t['task']} | {t['count']} |")
        lines.append("")

    # 数据集使用
    if result.get("dataset_usage"):
        lines.append("### 常用数据集")
        lines.append("| 数据集 | 出现次数 |")
        lines.append("|--------|---------|")
        for d in result["dataset_usage"]:
            lines.append(f"| {d['dataset']} | {d['count']} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Research Copilot - 研究空白(GAP)识别",
    )
    parser.add_argument("--query", "-q", required=True, help="研究主题关键词")
    parser.add_argument("--year-from", "-yf", type=int, required=True, help="起始年份")
    parser.add_argument("--year-to", "-yt", type=int, required=True, help="结束年份")
    parser.add_argument("--format", "-f", choices=["json", "report"], default="json")

    args = parser.parse_args()

    print(f"正在分析「{args.query}」的研究空白...", file=sys.stderr)

    result = identify_gaps(
        query=args.query,
        year_from=args.year_from,
        year_to=args.year_to,
    )

    if args.format == "report":
        print(format_gap_report(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
