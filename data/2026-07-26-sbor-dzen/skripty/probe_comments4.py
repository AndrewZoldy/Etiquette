import re

b = open("raw/comments_bundle.js", encoding="utf-8").read()
BT = chr(96)  # backtick

# all template literals mentioning Fc or /api/comments
pat = BT + r"([^" + BT + r"]{0,160}?(?:\$\{Fc\}|/api/comments)[^" + BT + r"]{0,160})" + BT
found = set(re.findall(pat, b))
print("--- template literals ---")
for p in sorted(found):
    print(repr(p))

print("\n--- contexts around ${Fc} ---")
seen = set()
for m in re.finditer(re.escape("${Fc}"), b):
    ctx = b[max(0, m.start() - 200):m.start() + 200]
    if ctx not in seen:
        seen.add(ctx)
        print("...", ctx.replace("\n", " "), "...\n")
