# -*- coding: utf-8 -*-
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data" / "books" / "books.json"
OUT  = BASE / "content" / "books"

# 读取当前合法 slug
valid = set()
with open(DATA, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        slug = obj.get("slug")
        if slug:
            valid.add(slug + ".md")

# 找出多余文件
removed = []
for md in OUT.glob("*.md"):
    if md.name not in valid:
        removed.append(md.name)
        md.unlink()

print("Removed:", len(removed))
for x in removed:
    print(" -", x)
