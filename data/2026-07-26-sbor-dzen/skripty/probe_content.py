import gzip, http.cookiejar, json, re, urllib.request, urllib.error, os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [
    ("User-Agent", UA),
    ("Accept", "*/*"),
    ("Accept-Language", "ru-RU,ru;q=0.9"),
    ("Accept-Encoding", "gzip, deflate"),
]

def get(url, timeout=40, extra=None):
    req = urllib.request.Request(url)
    if extra:
        for k, v in extra.items():
            req.add_header(k, v)
    with op.open(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return r.status, r.geturl(), raw.decode("utf-8", "replace")

try:
    get("https://dzen.ru/")
except Exception:
    pass

OID = "6a6340679e17237ef9dd0aff"
SHORT = "amNAZ54XI3753Qr_"

# 1) Look inside the SSR script for the article body
h = open("raw/article_page.html", encoding="utf-8").read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', h, re.S)
big = max(scripts, key=len)
open("raw/big_script.js", "w", encoding="utf-8").write(big)
tail = "ничего не нужно"
i = big.find(tail)
print("tail marker in big script at:", i)
if i > 0:
    print(repr(big[i:i+1500]))

# Find the SSR JSON assignment
m = re.search(r'setSSRDataToReqContext\((.{200,})\)', big, re.S)
print("ssr fn match:", bool(m))
for pat in (r'window\.__(\w+)__\s*=', r'window\.(\w+)\s*=\s*\{'):
    print(pat, set(re.findall(pat, big))or None)

# 2) try content APIs
cands = [
    ("export_pubid", f"https://dzen.ru/api/v3/launcher/export?publication_id=native:{OID}"),
    ("export_pubid2", f"https://dzen.ru/api/v3/launcher/export?item_id=native:{OID}"),
    ("article_json", f"https://dzen.ru/a/{SHORT}?format=json"),
    ("api_article", f"https://dzen.ru/api/v3/articles/{OID}"),
    ("editor_api", f"https://dzen.ru/api/publisher/v1/publications/{OID}"),
    ("turbo", f"https://dzen.ru/a/{SHORT}?turbo=true"),
    ("brief", f"https://dzen.ru/api/v3/launcher/brief?publication_id=native:{OID}"),
    ("pub_content", f"https://dzen.ru/media-api/publication-view-stat-vitrina?publicationId={OID}"),
]
for name, url in cands:
    try:
        st, fin, body = get(url)
        mark = tail in body
        print(f"[{name}] {st} len={len(body)} bodyHasText={mark} :: {body[:160]!r}")
        open(f"raw/c_{name}.txt", "w", encoding="utf-8").write(body)
    except urllib.error.HTTPError as e:
        print(f"[{name}] HTTP {e.code}")
    except Exception as e:
        print(f"[{name}] ERR {type(e).__name__} {e}")
