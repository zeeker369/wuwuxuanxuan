# -*- coding: utf-8 -*-
print("SCRIPT STARTED")

from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "books" / "books.json"
OUT  = BASE / "content" / "books"

def y(s):
    if not s:
        return ""
    return str(s).replace('"', '\\"')

def load_books(path):
    text = path.read_text(encoding="utf-8").lstrip()
    if text.startswith("["):
        return json.loads(text)
    books = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            books.append(json.loads(line))
    return books

books = load_books(DATA)
OUT.mkdir(parents=True, exist_ok=True)

print("BOOKS:", len(books))

for i, b in enumerate(books, 1):
    slug = b.get("slug", f"book-{i:06d}")
    out = OUT / f"{slug}.md"

    lines = []
    lines.append("---")
    lines.append(f'title: "{y(b.get("title",""))}"')
    if b.get("author"):
        lines.append(f'author: "{y(b["author"])}"')
    if b.get("isbn"):
        lines.append(f'isbn: "{y(b["isbn"])}"')
    if b.get("tags"):
        lines.append("tags: [" + ", ".join(f'"{y(t)}"' for t in b["tags"]) + "]")
    if b.get("summary"):
        lines.append(f'summary: "{y(b["summary"])}"')
    if b.get("cover"):
        lines.append(f'cover: "{y(b["cover"])}"')
    lines.append("buy:")
    lines.append("---\n")

    # ===== 正文模块（严格按 v2 顺序） =====

    if b.get("read_position"):
        lines.append("## 阅读定位\n")
        lines.append(b["read_position"] + "\n")

    if b.get("not_for"):
        lines.append("## 这本书不做什么\n")
        for item in b["not_for"]:
            lines.append(f"- {item}")
        lines.append("")

    if b.get("recommend_reasons"):
        lines.append("## 推荐理由\n")
        for item in b["recommend_reasons"]:
            lines.append(f"- {item}")
        lines.append("")

    if b.get("for_readers"):
        lines.append("## 适合阅读的人群\n")
        for item in b["for_readers"]:
            lines.append(f"- {item}")
        lines.append("")

    if b.get("reading_notice"):
        lines.append("## 阅读提醒\n")
        lines.append(b["reading_notice"] + "\n")

    if b.get("quotes"):
        lines.append("## 书中经典句子（节选）\n")
        for q in b["quotes"]:
            lines.append(f"- {q}")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print("generated:", out.name)

print("DONE")
