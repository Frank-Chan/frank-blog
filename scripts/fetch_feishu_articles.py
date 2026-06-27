#!/usr/bin/env python3
"""
fetch_feishu_articles.py
从飞书知识库「🌐 公开发表」目录拉取文章到本地 Hugo content/ 目录。

用法:
    python scripts/fetch_feishu_articles.py [--dry-run]

流程:
    1. 列出 🌐 公开发表 下的所有 docx 节点
    2. 对比本地已有文章（通过 frontmatter feishu_token 去重）
    3. 拉取新文档的 Markdown 内容
    4. 写入 content/YYYY-MM-DD-{slug}.md，自动生成 frontmatter
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# === 配置 ===
SPACE_ID = "7533880381343285250"          # 技术沉淀 知识空间
PUBLIC_DIR_TOKEN = "A1IWwKPZ6i7U3xkOGSKcZBXDnlq"  # 🌐 公开发表 目录 node_token
CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
LARK_CLI = "lark-cli"

# Hugo content 目录中文章文件名格式: YYYY-MM-DD-{slug}.md
CONTENT_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")


def run_lark(*args, timeout=60):
    """运行 lark-cli 命令，返回 parsed JSON。"""
    cmd = [LARK_CLI, *args, "--as", "user", "--format", "json"]
    # Windows: shell=True 让系统找到对应的 .cmd 包装器
    result = subprocess.run(
        cmd if sys.platform != "win32" else " ".join(cmd),
        capture_output=True, text=True, timeout=timeout,
        shell=(sys.platform == "win32"),
        encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        print(f"[ERROR] lark-cli 失败: {' '.join(cmd)}")
        if stderr:
            print(f"  stderr: {stderr}")
        return None

    # lark-cli 输出可能包含状态行，找到 JSON 起始位置
    raw = result.stdout
    json_start = raw.find("{")
    if json_start < 0:
        print(f"[ERROR] lark-cli 输出中未找到 JSON: {raw[:200]}")
        return None
    try:
        return json.loads(raw[json_start:])
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析失败: {e}")
        return None


def list_public_articles():
    """列出 🌐 公开发表 下的所有 docx 文档节点。"""
    data = run_lark(
        "wiki", "+node-list",
        "--space-id", SPACE_ID,
        "--parent-node-token", PUBLIC_DIR_TOKEN,
        "--page-all", "--page-limit", "10",
        timeout=30,
    )
    if not data or not data.get("ok"):
        print("[ERROR] 无法列出 🌐 公开发表 节点")
        return []

    nodes = data.get("data", {}).get("nodes", [])
    articles = []
    for n in nodes:
        if n.get("obj_type") == "docx":
            articles.append({
                "title": n["title"],
                "node_token": n["node_token"],
                "obj_token": n["obj_token"],
            })
    print(f"[INFO] 🌐 公开发表 下有 {len(articles)} 篇 docx 文章")
    return articles


def fetch_article_markdown(node_token):
    """拉取单篇文章的 Markdown 内容。"""
    data = run_lark(
        "docs", "+fetch",
        "--api-version", "v2",
        "--doc", node_token,
        "--doc-format", "markdown",
        timeout=60,
    )
    if not data or not data.get("ok"):
        print(f"[ERROR] 拉取文档失败: {node_token}")
        return None

    doc = data.get("data", {}).get("document", {})
    return {
        "content": doc.get("content", ""),
        "document_id": doc.get("document_id", ""),
        "revision_id": doc.get("revision_id", 0),
    }


def get_existing_feishu_tokens():
    """扫描 content/ 目录，返回已有文章的 feishu_token 集合。"""
    tokens = set()
    if not CONTENT_DIR.exists():
        return tokens

    for f in CONTENT_DIR.glob("*.md"):
        if f.name == "_index.md":
            continue
        try:
            text = f.read_text(encoding="utf-8")
            m = re.search(r"^feishu_token:\s*(\S+)", text, re.MULTILINE)
            if m:
                tokens.add(m.group(1))
        except Exception:
            pass
    return tokens


def slugify(title):
    """将中文标题转成英文 slug（拼音简化）或保留关键词。"""
    # 简单的 slug 生成：移除特殊字符，空格转连字符，转小写
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug.lower()[:80]


def generate_frontmatter(title, node_token, obj_token):
    """生成 Hugo 文章 frontmatter。"""
    slug = slugify(title)
    today = datetime.now().strftime("%Y-%m-%d")

    fm = f"""---
title: "{title}"
slug: "{slug}"
date: {today}
status: fetched
feishu_token: "{node_token}"
feishu_obj_token: "{obj_token}"
tags: []
categories: []
publish:
  github: null
  wechat: null
  csdn: null
---

"""
    return fm


def write_article(title, node_token, obj_token, markdown_content):
    """写入文章到 content/ 目录。"""
    slug = slugify(title)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}-{slug}.md"
    filepath = CONTENT_DIR / filename

    # 移除 markdown 内容开头的与标题重复的 h1
    content = markdown_content
    title_h1 = f"# {title}"
    if content.startswith(title_h1):
        content = content[len(title_h1):].lstrip("\n")

    frontmatter = generate_frontmatter(title, node_token, obj_token)
    full_content = frontmatter + content

    filepath.write_text(full_content, encoding="utf-8")
    print(f"[INFO] 写入: {filepath}")
    return filepath


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("fetch_feishu_articles.py — 飞书 → 本地拉取")
    print("=" * 60)

    # 1. 列出飞书文章
    articles = list_public_articles()
    if not articles:
        print("[INFO] 没有找到待拉取的文章")
        return 0

    # 2. 获取本地已有的 feishu_token
    existing_tokens = get_existing_feishu_tokens()
    print(f"[INFO] 本地已有 {len(existing_tokens)} 篇文章")

    # 3. 拉取新文章
    new_count = 0
    for art in articles:
        token = art["node_token"]
        if token in existing_tokens:
            print(f"[SKIP] 已存在: {art['title']}")
            continue

        print(f"\n[FETCH] {art['title']}")
        if dry_run:
            print(f"  [DRY-RUN] 跳过实际拉取")
            new_count += 1
            continue

        doc = fetch_article_markdown(token)
        if not doc or not doc["content"]:
            print(f"  [WARN] 内容为空，跳过")
            continue

        filepath = write_article(
            art["title"],
            art["node_token"],
            art["obj_token"],
            doc["content"],
        )
        print(f"  document_id: {doc['document_id']}")
        print(f"  revision_id: {doc['revision_id']}")
        new_count += 1

    print(f"\n{'=' * 60}")
    if dry_run:
        print(f"[DRY-RUN] 共发现 {new_count} 篇新文章（未实际拉取）")
    else:
        print(f"[DONE] 共拉取 {new_count} 篇新文章")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
