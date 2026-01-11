# -*- coding: utf-8 -*-
from pathlib import Path
import json
from collections import defaultdict

BASE = Path(__file__).resolve().parent   # D:\f
SRC  = BASE / "data" / "books" / "books.json"

bucket = defaultdict(list)

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        slug = (obj.get("slug") or "").strip() or f"book-{i:06d}"
        bucket[slug].append(i)

dupes = {k:v for k,v in bucket.items() if len(v) > 1}
print("DUPES:", len(dupes))
for slug, lines in sorted(dupes.items(), key=lambda x: -len(x[1])):
    print(slug, "lines:", lines)
