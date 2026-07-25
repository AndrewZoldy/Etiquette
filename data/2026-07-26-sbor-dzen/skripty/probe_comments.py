import gzip, http.cookiejar, json, re, urllib.request, urllib.error, os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", UA), ("Accept", "*/*"),
                 ("Accept-Language", "ru-RU,ru;q=0.9"), ("Accept-Encoding", "gzip, deflate")]

def get(url, timeout=40):
    with op.open(url, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return r.status, raw.decode("utf-8", "replace")

h = open("raw/article_page.html", encoding="utf-8").read()

# 1) all script srcs, esp comments bundle
srcs = re.findall(r'<script[^>]+src="([^"]+)"', h)
print("--- script srcs ---")
for s in srcs:
    print(" ", s)

# 2) any comments config in the html (escaped JSON)
for pat in (r'\\?"commentsToken\\?":\\?"([^"\\]+)', r'\\?"documentId\\?":\\?"([^"\\]+)',
            r'\\?"commentsCount\\?":(\d+)', r'\\?"commentsApi[^"]*\\?":\\?"([^"\\]+)',
            r'commentsHost\\?":\\?"([^"\\]+)', r'\\?"origin\\?":\\?"(https[^"\\]+)'):
    found = set(re.findall(pat, h))
    print(f"{pat} -> {list(found)[:6]}")

# 3) try to fetch the comments bundle and grep endpoints
cands = [u for u in srcs if "comment" in u]
cands += ["https://static.dzeninfra.ru/s3/zen-apps/comments2/1.40.0/comments2.js",
          "https://static.dzeninfra.ru/s3/zen-apps/comments2/1.40.0/index.js"]
for u in dict.fromkeys(cands):
    if u.startswith("//"):
        u = "https:" + u
    try:
        st, body = get(u)
        eps = set(re.findall(r'["\'`](/api/[a-zA-Z0-9/_\-{}$.:]+)["\'`]', body))
        eps |= set(re.findall(r'["\'`](https://[a-z0-9.\-]*dzen[a-z0-9.\-]*/api/[a-zA-Z0-9/_\-{}$.:]+)', body))
        print(f"\n[{u[:100]}] {st} len={len(body)}")
        for e in sorted(eps)[:60]:
            print("    ", e)
    except Exception as e:
        print(f"\n[{u[:100]}] ERR {type(e).__name__} {e}")
