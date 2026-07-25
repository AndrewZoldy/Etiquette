import re

b = open("raw/comments_bundle.js", encoding="utf-8").read()
print("len", len(b))

for m in re.finditer(r'/api/comments/v2', b):
    s = max(0, m.start() - 700)
    e = min(len(b), m.end() + 700)
    print("\n========== context ==========")
    print(b[s:e])

print("\n\n===== method-name-ish strings =====")
names = set(re.findall(r'["\'`](get[A-Za-z-]*[Cc]omment[A-Za-z-]*)["\'`]', b))
names |= set(re.findall(r'["\'`]([a-z\-]*comment[a-z\-]*)["\'`]', b))
for n in sorted(names)[:120]:
    print("  ", n)
