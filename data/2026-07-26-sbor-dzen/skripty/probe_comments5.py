import re

b = open("raw/comments_bundle.js", encoding="utf-8").read()

# find all string literals passed as first arg to the request helpers Qc/Gc/qc
for helper in ("Qc", "Gc", "qc"):
    hits = set(re.findall(helper + r'\(\s*"([a-z0-9\-/]+)"', b))
    print(f"{helper}: {sorted(hits)}")

# any kebab-case endpoint-looking literals
kebab = set(re.findall(r'"([a-z]+(?:-[a-z0-9]+){1,4})"', b))
interesting = [k for k in kebab if any(w in k for w in
              ("comment", "tree", "list", "fetch", "get", "root", "child", "stat", "count"))]
print("\n--- endpoint-ish kebab literals ---")
for k in sorted(interesting):
    print("  ", k)

# find the params schema context (Kc)
i = b.find("Kc=")
print("\n--- schema ctx ---")
print(b[i-200:i+1400])
