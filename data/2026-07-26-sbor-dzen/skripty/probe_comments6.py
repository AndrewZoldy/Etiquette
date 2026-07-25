import gzip, http.cookiejar, json, urllib.parse, urllib.request, urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", UA), ("Accept", "application/json, text/plain, */*"),
                 ("Accept-Language", "ru-RU,ru;q=0.9"), ("Accept-Encoding", "gzip, deflate"),
                 ("Referer", "https://dzen.ru/a/amNAZ54XI3753Qr_"),
                 ("X-Zen-Comments-Clid", "300"),
                 ("X-Zen-Comments-Place", "article"),
                 ("X-Zen-Comments-Product", "zen")]

def get(url, timeout=40):
    with op.open(url, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return r.status, raw.decode("utf-8", "replace")

try:
    get("https://dzen.ru/")
except Exception as e:
    print("warm", e)

OID = "6a6340679e17237ef9dd0aff"
PUB = "63dd27aac30ab522dcce48b3"

variants = [
    dict(documentId=f"native:{OID}", publicationPublisherId=PUB, batchSize="30", withConfig="true"),
    dict(documentId=f"native:{OID}", batchSize="30"),
    dict(documentId=f"native:{OID}", publicationPublisherId=PUB, batchSize="30",
         sorting="popular", withConfig="true", clientTs="1785017561184"),
]
for i, params in enumerate(variants):
    url = "https://dzen.ru/api/comments/v2/root-comments?" + urllib.parse.urlencode(params)
    try:
        st, body = get(url)
        print(f"\n[v{i}] {st} len={len(body)}")
        print(body[:600])
        open(f"raw/comments_v{i}.json", "w", encoding="utf-8").write(body)
        try:
            d = json.loads(body)
            print("KEYS:", list(d.keys()))
        except Exception:
            pass
    except urllib.error.HTTPError as e:
        eb = e.read().decode("utf-8", "replace")
        print(f"\n[v{i}] HTTP {e.code} :: {eb[:300]}")
    except Exception as e:
        print(f"\n[v{i}] ERR {type(e).__name__} {e}")
