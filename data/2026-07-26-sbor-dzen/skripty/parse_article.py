import re, json

h = open("raw/article_page.html", encoding="utf-8").read()
print("len", len(h))

# 1) find comment-related API urls
urls = set(re.findall(r'https://[a-zA-Z0-9./_\-]*comment[a-zA-Z0-9./_\-]*', h))
print("\n--- comment-ish URLs ---")
for u in sorted(urls)[:40]:
    print(" ", u)

# 2) find any api hosts
hosts = set(re.findall(r'https://([a-z0-9.\-]+)/', h))
print("\n--- hosts ---", sorted(hosts)[:40])

# 3) big JSON blobs in script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', h, re.S)
print("\nscripts:", len(scripts), "sizes:", sorted((len(s) for s in scripts), reverse=True)[:8])
for i, s in enumerate(scripts):
    if len(s) > 50000:
        print(f"\n### big script #{i} len={len(s)} head:")
        print(s[:400].replace("\n", " "))

# 4) look for article body markers
for probe in ('"content":[', 'article-body', 'w-article', '"blocks"', '"paragraph"',
              'itemprop="articleBody"', 'class="article-render', 'data-testid'):
    print(f"probe {probe!r}: {h.count(probe)}")

# 5) og / meta
for m in re.findall(r'<meta[^>]+(?:property|name)="(og:[^"]+|description)"[^>]*content="([^"]{0,300})"', h)[:15]:
    print("META", m[0], "=", m[1][:200])
