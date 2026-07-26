import re, json, sys

fn = sys.argv[1]
h = open(fn, encoding='utf-8', errors='replace').read()
raw = re.findall(r'"title":("(?:[^"\\]|\\.)*")', h)
seen = []
for r in raw:
    try:
        t = json.loads(r)
    except Exception:
        continue
    if 5 < len(t) < 220 and t not in seen:
        seen.append(t)
print('TITLE COUNT', len(seen))
for t in seen:
    print(' -', t)

ids = sorted(set(re.findall(r'dzen\.ru/a/([A-Za-z0-9_-]{10,30})', h)))
print('ARTICLE IDS', len(ids))
for i in ids:
    print('  a/', i)
