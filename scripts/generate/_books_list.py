# -*- coding: utf-8 -*-
from pathlib import Path
import json
import csv
import re
from collections import Counter, defaultdict

BASE = Path(__file__).resolve().parents[2]   # D:\f
DATA = BASE / "data" / "books" / "books.json"  # 这里保持与你当前流程一致
OUT_CSV = BASE / "data" / "books" / "books_list.csv"
OUT_MD  = BASE / "data" / "books" / "books_list.md"

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[·•\-—（）()【】\[\]「」『』《》]", "", s)
    return s

def load_books(path: Path):
    """
    兼容两种格式：
    - JSON array: [ {...}, {...} ]
    - JSONL: 每行一个 {...}
    """
    text = path.read_text(encoding="utf-8", errors="strict").lstrip()
    if text.startswith("["):
        return json.loads(text)
    # JSONL fallback
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    return items

books = load_books(DATA)
if not isinstance(books, list):
    raise SystemExit("books.json 不是列表/JSONL，无法生成清单。")

rows = []
missing_title = 0
missing_author = 0
missing_slug = 0

for i, b in enumerate(books, 1):
    slug = (b.get("slug") or b.get("id") or "").strip()
    title = (b.get("title") or "").strip()
    author = (b.get("author") or "").strip()
    isbn = (b.get("isbn") or "").strip()
    summary = (b.get("summary") or b.get("intro") or "").strip()
    tags = b.get("tags") if isinstance(b.get("tags"), list) else []
    tags_str = " / ".join([str(t).strip() for t in tags if str(t).strip()])

    if not title:  missing_title += 1
    if not author: missing_author += 1
    if not slug:   missing_slug += 1

    rows.append({
        "idx": i,
        "slug": slug,
        "title": title,
        "author": author,
        "isbn": isbn,
        "tags": tags_str,
        "summary": summary[:120],  # 只截取前120字便于浏览
    })

# 统计重复：以 title+author 作为“同一本”的近似主键
key_counter = Counter()
key_to_items = defaultdict(list)
for r in rows:
    k = norm(r["title"]) + "::" + norm(r["author"])
    key_counter[k] += 1
    key_to_items[k].append(r)

dups = [k for k, c in key_counter.items() if c > 1]

# 输出 CSV（Excel 友好）
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["idx","slug","title","author","isbn","tags","summary"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# 输出 MD（人眼浏览）
with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(f"# Books List (count={len(rows)})\n\n")
    f.write(f"- missing title: {missing_title}\n")
    f.write(f"- missing author: {missing_author}\n")
    f.write(f"- missing slug: {missing_slug}\n")
    f.write(f"- duplicate title+author groups: {len(dups)}\n\n")

    if dups:
        f.write("## Duplicates (title+author)\n\n")
        for k in dups:
            items = key_to_items[k]
            f.write(f"### {items[0]['title']} — {items[0]['author']}  (x{len(items)})\n\n")
            for it in items:
                f.write(f"- #{it['idx']:03d} `{it['slug']}` | tags: {it['tags']}\n")
            f.write("\n")

    f.write("## All Books\n\n")
    for r in rows:
        f.write(f"- #{r['idx']:03d} `{r['slug']}` | **{r['title']}** — {r['author']} | {r['tags']}\n")

print("LIST DONE")
print("DATA     :", DATA)
print("COUNT    :", len(rows))
print("CSV OUT  :", OUT_CSV)
print("MD OUT   :", OUT_MD)
print("MISSING  : title", missing_title, "| author", missing_author, "| slug", missing_slug)
print("DUP GROUP:", len(dups))
