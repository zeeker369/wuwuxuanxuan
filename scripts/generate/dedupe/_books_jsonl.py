# -*- coding: utf-8 -*-
from pathlib import Path
import json
import re

print("SCRIPT: dedupe_books_jsonl (soft-dedupe) START")

BASE = Path(__file__).resolve().parents[3]   # D:\f
SRC  = BASE / "data" / "books" / "books.json"
DST  = BASE / "data" / "books" / "books.clean.jsonl"

print("BASE:", BASE)
print("SRC :", SRC)
print("DST :", DST)


def norm(s: str) -> str:
    """用于 title / author 的归一化"""
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[·•\-—（）()【】\[\]]", "", s)
    return s


def key_title_author(obj):
    return norm(obj.get("title")) + "::" + norm(obj.get("author"))


def score(obj):
    """信息丰富度评分（用于保留更好版本）"""
    s = 0
    if obj.get("summary"): s += 2
    if obj.get("read_position"): s += 2
    if obj.get("recommend_reasons"): s += 3
    if obj.get("for_readers"): s += 2
    if obj.get("quotes"): s += 2
    s += len(obj.get("tags", []))
    return s


seen = {}
total = 0
bad = 0

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    for line_no, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue

        total += 1
        try:
            obj = json.loads(line)
        except Exception:
            bad += 1
            continue

        # 软去重 key：title + author
        key = key_title_author(obj)

        # 极端兜底（几乎不会用到）
        if not key.strip("::"):
            key = f"__line_{line_no}"

        if key not in seen:
            seen[key] = obj
        else:
            # 保留信息更丰富的
            if score(obj) > score(seen[key]):
                seen[key] = obj


with open(DST, "w", encoding="utf-8") as w:
    for obj in seen.values():
        w.write(json.dumps(obj, ensure_ascii=False) + "\n")

print("SRC total:", total)
print("Bad lines:", bad)
print("After dedupe:", len(seen))
print("Wrote:", DST)
