import json
from collections import Counter

d = json.load(open("raw/launcher_export.txt", encoding="utf-8"))
print("MORE:", json.dumps(d["more"], ensure_ascii=False)[:600])
print("\nTABS:", json.dumps(d["tabs"], ensure_ascii=False)[:1500])
print("\nLINKS:", json.dumps(d["links"], ensure_ascii=False)[:800])
print("\nCHANNEL:", json.dumps(d["channel"], ensure_ascii=False)[:2500])

it = d["items"]
print("\nITEM TYPES:", Counter(x.get("item_type") for x in it))
print("TYPES:", Counter(x.get("type") for x in it))
for x in it:
    print("-", x.get("item_type"), "|", x.get("type"), "|", str(x.get("title"))[:70])

# find an article item and dump keys
for x in it:
    if x.get("item_type") in ("article", "gif", "post") or "text" in x:
        print("\n=== SAMPLE PUBLICATION ITEM ===")
        print(json.dumps(sorted(x.keys()), ensure_ascii=False))
        print(json.dumps(x, ensure_ascii=False, indent=1)[:5000])
        break
