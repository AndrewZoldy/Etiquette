import gzip, http.cookiejar, json, re, urllib.request, urllib.error, os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HDRS = [
    ("User-Agent", UA),
    ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"),
    ("Accept-Language", "ru-RU,ru;q=0.9,en-US;q=0.8"),
    ("Accept-Encoding", "gzip, deflate"),
    ("Upgrade-Insecure-Requests", "1"),
    ("Sec-Fetch-Dest", "document"),
    ("Sec-Fetch-Mode", "navigate"),
    ("Sec-Fetch-Site", "none"),
]

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = HDRS


def get(url, timeout=40):
    with op.open(url, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return r.status, r.geturl(), raw.decode("utf-8", "replace")


os.makedirs("raw", exist_ok=True)

# warm up session (this follows the SSO push and should set cookies)
for step in ("https://dzen.ru/", "https://dzen.ru/"):
    try:
        st, fin, body = get(step)
        print(f"warmup {st} -> {fin[:90]} len={len(body)}")
    except Exception as e:
        print("warmup ERR", e)
print("cookies:", [c.name for c in cj])

ART = "https://dzen.ru/a/amNAZ54XI3753Qr_"
try:
    st, fin, body = get(ART)
    print(f"\nARTICLE {st} -> {fin[:110]} len={len(body)}")
    open("raw/article_page.html", "w", encoding="utf-8").write(body)
    # look for signs of full text
    for probe in ("Лицемерная помощь", "article-render", "\"content\"", "Bookmate",
                  "comments", "commentsCount", "__PRELOADED", "serverSideData", "window._"):
        print(f"  contains {probe!r}: {probe in body}")
except urllib.error.HTTPError as e:
    print("ARTICLE HTTP", e.code, e.reason)
except Exception as e:
    print("ARTICLE ERR", type(e).__name__, e)
