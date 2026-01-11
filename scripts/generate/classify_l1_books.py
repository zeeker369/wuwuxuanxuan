# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]  # D:\f
BOOKDIR = BASE / "data" / "books"

# 按优先级自动选输入（你不用再手改）
CANDIDATES = [
    BOOKDIR / "books.jsonl",
    BOOKDIR / "books.clean.jsonl",
    BOOKDIR / "douban_top250_l1.jsonl",
    BOOKDIR / "books.json",         # 兜底：可能是 JSONL 或 JSON array
    BOOKDIR / "books.bak.json",
]

SRC = next((p for p in CANDIDATES if p.exists()), None)
if SRC is None:
    raise SystemExit(f"找不到输入文件。请把数据放到 {BOOKDIR}，或检查文件名。")

DST = BOOKDIR / "books.classified.jsonl"

print("BASE:", BASE)
print("SRC :", SRC)
print("DST :", DST)

def load_books(path: Path):
    """
    兼容两种格式：
    - JSON array: [ {...}, {...} ]
    - JSONL: 每行一个 {...}
    """
    text = path.read_text(encoding="utf-8").lstrip()
    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON array 解析后不是 list")
        return data
    # JSONL
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items

def dump_jsonl(path: Path, items):
    with open(path, "w", encoding="utf-8") as w:
        for obj in items:
            w.write(json.dumps(obj, ensure_ascii=False) + "\n")

def has_any(text: str, keywords):
    if not text:
        return False
    return any(k in text for k in keywords)

books = load_books(SRC)

count = 0
hit_literature = 0
hit_history = 0
hit_thought = 0

out_items = []

for book in books:
    title = (book.get("title") or "").strip()
    summary = (book.get("summary") or book.get("intro") or "").strip()
    author = (book.get("author") or "").strip()

    tags = book.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    tags = set([str(t).strip() for t in tags if str(t).strip()])

    # 规则 3：历史（仅标题）
    if has_any(title, ["简史", "通史", "史"]):
        tags.add("历史")
        hit_history += 1

    # 规则 4：思想（标题或简介）
    if has_any(title, ["哲学", "思维", "自我"]) or has_any(summary, ["哲学", "思维", "自我"]):
        tags.add("思想")
        hit_thought += 1

    # 规则 1/2：文学（保守兜底）
    # 你给的两条“当代小说/外国经典 → 文学”，在 L1 数据里没法稳定识别，
    # 所以用更稳的策略：只要不是历史/思想，且有作者，就归入“文学”
    if "历史" not in tags and "思想" not in tags and author:
        tags.add("文学")
        hit_literature += 1

    book["tags"] = sorted(tags)
    out_items.append(book)
    count += 1

dump_jsonl(DST, out_items)

print("\nDONE")
print("TOTAL        :", count)
print("文学 hit     :", hit_literature)
print("历史 hit     :", hit_history)
print("思想 hit     :", hit_thought)
print("OUT FILE     :", DST)
