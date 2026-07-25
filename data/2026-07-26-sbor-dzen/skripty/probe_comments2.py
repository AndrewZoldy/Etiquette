import gzip, http.cookiejar, json, re, urllib.request, urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", UA), ("Accept", "*/*"),
                 ("Accept-Language", "ru-RU,ru;q=0.9"), ("Accept-Encoding", "gzip, deflate")]

def get(url, timeout=60):
    with op.open(url, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return r.status, raw.decode("utf-8", "replace")

# grep the SSR html for comments config object
h = open("raw/article_page.html", encoding="utf-8").read()
for m in re.finditer(r'commentsToken', h):
    s = max(0, m.start() - 1200)
    print("=== context around commentsToken ===")
    print(h[s:m.start() + 600].replace("\\\"", '"')[-1600:])
    print()
    break

# comments2 bundle listing attempts
b = "https://static.dzeninfra.ru/s3/zen-apps/comments2/1.40.0/"
for f in ("comments2.modern.bundle.js", "client.modern.bundle.js",
          "comments2.bundle.js", "comments.modern.bundle.js",
          "comments2-desktop.modern.bundle.js"):
    try:
        st, body = get(b + f)
        eps = set(re.findall(r'["\'`](/api/[a-zA-Z0-9/_\-{}$.:]+)["\'`]', body))
        print(f"[OK {f}] len={len(body)} endpoints:")
        for e in sorted(eps)[:80]:
            print("   ", e)
        open("raw/comments_bundle.js", "w", encoding="utf-8").write(body)
        break
    except Exception as e:
        print(f"[{f}] {type(e).__name__} {e}")

# also grep dzen-root client bundle
try:
    st, body = get("https://static.dzeninfra.ru/s3/zen-apps/dzen-root/1.21.1/client.modern.bundle.js")
    print("\ndzen-root bundle len", len(body))
    eps = set(re.findall(r'["\'`](/api/[a-zA-Z0-9/_\-{}$.:]*comment[a-zA-Z0-9/_\-{}$.:]*)["\'`]', body))
    eps |= set(re.findall(r'["\'`](/api/v\d/[a-zA-Z0-9/_\-]+)["\'`]', body))
    for e in sorted(eps)[:100]:
        print("   ", e)
except Exception as e:
    print("root bundle ERR", e)
