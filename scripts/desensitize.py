#!/usr/bin/env python3
"""
desensitize.py
对 content/ 下所有 status: fetched 的文章做自动脱敏处理。

用法:
    python scripts/desensitize.py [--dry-run]

脱敏规则：
    - 替换公司名、人名、内部链接
    - 只改正文，不改 frontmatter
    - 脱敏后自动列出所有被替换的内容
    - 备份原文件到 .backup/
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# === 配置 ===
CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
BACKUP_DIR = Path(__file__).resolve().parent.parent / ".backup"

# 脱敏替换规则（按顺序应用）
REPLACEMENTS = [
    # 公司/产品名
    (r"赛尔智控", "某科技公司"),
    (r"赛尔\s*(?:智能|科技|公司)?", "某公司"),
    (r"点云管家(?!某)", "点云平台"),
    (r"QNAP", "某品牌NAS"),
    (r"Qu405", "某型号NAS"),

    # 人名
    (r"范恩强", "公司领导"),
    (r"王奎元|老王", "算法负责人"),
    (r"frank_chan|Frank Chan", "技术负责人"),

    # 内部链接
    (r"https://[^\s]*\.feishu\.cn[^\s]*", "[内部链接]"),
    (r"https://[^\s]*\.dingtalk\.com[^\s]*", "[内部链接]"),
    (r"https://internal-api-drive-stream\.feishu\.cn[^\s]*", "[内部图片]"),

    # 内部 IP 地址
    (r"10\.\d+\.\d+\.\d+(:\d+)?", "[内部地址]"),
    (r"192\.168\.\d+\.\d+(:\d+)?", "[内部地址]"),

    # 内部域名/IP
    (r"myQNAPcloud", "远程管理服务"),
    (r"100\.\d+\.\d+\.\d+", "[Tailscale IP]"),
    (r"shenfrank", "我的设备"),
]


def extract_frontmatter(text):
    """解析 frontmatter 和正文分界。返回 (frontmatter_dict, body_start_offset)。"""
    if not text.startswith("---\n"):
        return {}, 0

    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, 0

    fm_text = text[4:end]
    body_start = end + 5  # 跳过 "\n---\n"

    fm = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            fm[key] = val

    return fm, body_start


def update_frontmatter(text, body_start, updates):
    """更新 frontmatter 中的字段。"""
    end = text.find("\n---\n", 4)
    if end < 0:
        return text

    fm_text = text[4:end]
    lines = fm_text.split("\n")
    new_lines = []

    updated_keys = set()
    for line in lines:
        stripped = line.strip()
        if ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}: {updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in updated_keys:
            new_lines.append(f"{k}: {v}")

    new_fm = "\n".join(new_lines)
    return "---\n" + new_fm + text[end:]


def desensitize_article(filepath, dry_run=False):
    """对单篇文章执行脱敏。返回替换统计。"""
    text = filepath.read_text(encoding="utf-8")

    # 分离 frontmatter 和正文
    fm, body_start = extract_frontmatter(text)
    if not fm:
        print(f"  [WARN] 无 frontmatter，跳过")
        return None

    status = fm.get("status", "")
    if status != "fetched":
        print(f"  [SKIP] status={status}，不需要脱敏")
        return None

    frontmatter = text[:body_start]
    body = text[body_start:]

    # 应用替换规则
    replacements_made = []
    desensitized_body = body
    for pattern, replacement in REPLACEMENTS:
        matches = re.findall(pattern, desensitized_body)
        if matches:
            desensitized_body = re.sub(pattern, replacement, desensitized_body)
            replacements_made.append((pattern, replacement, len(matches)))

    if not replacements_made:
        print(f"  [INFO] 无需脱敏，内容安全")
        return {"filepath": filepath, "replacements": []}

    # 更新 status
    new_fm = frontmatter.replace(
        "status: fetched",
        f"status: desensitized"
    )
    # 添加脱敏时间戳
    if "desensitized_at:" not in new_fm:
        new_fm = new_fm.rstrip() + f"\ndesensitized_at: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    if dry_run:
        print(f"  [DRY-RUN] 将做 {len(replacements_made)} 处替换:")
        for pat, rep, count in replacements_made:
            print(f"    {pat} → {rep} ({count} 处)")
        return {"filepath": filepath, "replacements": replacements_made}

    # 备份原文件
    BACKUP_DIR.mkdir(exist_ok=True)
    backup_path = BACKUP_DIR / filepath.name
    shutil.copy2(str(filepath), str(backup_path))

    # 写入脱敏后内容
    new_content = new_fm + desensitized_body
    filepath.write_text(new_content, encoding="utf-8")

    print(f"  [DESENSITIZED] {len(replacements_made)} 类替换:")
    for pat, rep, count in replacements_made:
        print(f"    {pat} → {rep} ({count} 处)")
    print(f"  [BACKUP] {backup_path}")

    return {"filepath": filepath, "replacements": replacements_made}


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("desensitize.py — 自动脱敏处理")
    print("=" * 60)

    if not CONTENT_DIR.exists():
        print("[ERROR] content/ 目录不存在")
        return 1

    md_files = sorted(CONTENT_DIR.glob("*.md"))
    articles_to_process = [f for f in md_files if f.name != "_index.md"]
    print(f"[INFO] content/ 共 {len(articles_to_process)} 篇 md 文件")

    total_replaced = 0
    processed = 0

    for filepath in articles_to_process:
        print(f"\n--- {filepath.name} ---")
        result = desensitize_article(filepath, dry_run=dry_run)
        if result:
            processed += 1
            total_replaced += len(result["replacements"])

    print(f"\n{'=' * 60}")
    if dry_run:
        print(f"[DRY-RUN] 预览完成：{processed} 篇需处理，{total_replaced} 类替换")
    else:
        print(f"[DONE] 脱敏完成：{processed} 篇已处理，{total_replaced} 类替换")
        print(f"[BACKUP] 备份在 {BACKUP_DIR}/")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
