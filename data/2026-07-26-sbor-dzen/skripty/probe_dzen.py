import json, sys, os
import urllib.request, urllib.error, gzip, io

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}

CHANNEL = "valentinahli"
CHANNEL_ID = "63dd27aac30ab522dcce48b3"

urls = [
    ("channel_html", f"https://dzen.ru/{CHANNEL}"),
    ("channel_html_noredir", f"https://dzen.ru/{CHANNEL}?is_autologin_ya=false"),
    ("launcher_more", f"https://dzen.ru/api/v3/launcher/more?channel_name={CHANNEL}&clid=300&country_code=ru"),
    ("launcher_more_id", f"https://dzen.ru/api/v3/launcher/more?channel_id={CHANNEL_ID}&clid=300&country_code=ru"),
    ("launcher_export", f"https://dzen.ru/api/v3/launcher/export?channel_name={CHANNEL}"),
    ("api_channel", f"https://dzen.ru/api/v1/channels/{CHANNEL}"),
    ("rss_media", f"https://dzen.ru/media/id/{CHANNEL_ID}/rss"),
    ("rss_plain", f"https://dzen.ru/{CHANNEL}.rss"),
    ("robots", "https://dzen.ru/robots.txt"),
]

os.makedirs("raw", exist_ok=True)

for name, url in urls:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            body = raw.decode("utf-8", "replace")
            final = r.geturl()
            print(f"[{name}] {r.status} len={len(body)} final={final[:120]}")
            print("   head:", body[:200].replace("\n", " "))
            with open(f"raw/{name}.txt", "w", encoding="utf-8") as f:
                f.write(body)
    except urllib.error.HTTPError as e:
        print(f"[{name}] HTTP {e.code} {e.reason}")
    except Exception as e:
        print(f"[{name}] ERR {type(e).__name__}: {e}")
