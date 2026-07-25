import json

d = json.load(open("raw/launcher_export.txt", encoding="utf-8"))
print("TOP KEYS:", list(d.keys()))
for k, v in d.items():
    t = type(v).__name__
    n = len(v) if isinstance(v, (list, dict, str)) else ""
    print(f"  {k}: {t} {n}")

items = d.get("items")
if items is None:
    # look for nested items
    for k, v in d.items():
        if isinstance(v, dict) and "items" in v:
            print(f"\n{k}.items -> {len(v['items'])}")

print("\n--- items count:", len(d.get("items", [])))
it = d.get("items", [])
if it:
    print("\nFIRST ITEM KEYS:")
    print(json.dumps(sorted(it[0].keys()), ensure_ascii=False))
    print("\nFIRST ITEM (truncated):")
    s = json.dumps(it[0], ensure_ascii=False, indent=1)
    print(s[:4000])
    from collections import Counter
    print("\nTYPES:", Counter(x.get("type") for x in it))
    print("OBJECT TYPES:", Counter(x.get("object_type") for x in it))

print("\n--- pagination-ish keys ---")
for k in ("more", "link", "next", "feed"):
    if k in d:
        print(k, json.dumps(d[k], ensure_ascii=False)[:500])
