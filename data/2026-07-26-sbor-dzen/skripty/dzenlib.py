"""Общий транспорт для сбора данных с Дзена (прямой HTTP, без браузера)."""
import gzip, http.cookiejar, json, random, ssl, time, urllib.error, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


class Dzen:
    def __init__(self, referer="https://dzen.ru/valentinahli"):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=CTX),
        )
        self.referer = referer
        self.op.addheaders = [
            ("User-Agent", UA),
            ("Accept", "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"),
            ("Accept-Language", "ru-RU,ru;q=0.9,en-US;q=0.8"),
            ("Accept-Encoding", "gzip, deflate"),
        ]
        self.warm()

    def warm(self):
        try:
            self.get("https://dzen.ru/")
        except Exception:
            pass

    def get(self, url, timeout=45, headers=None, tries=4, binary=False):
        last = None
        for attempt in range(tries):
            try:
                req = urllib.request.Request(url)
                if self.referer:
                    req.add_header("Referer", self.referer)
                for k, v in (headers or {}).items():
                    req.add_header(k, v)
                with self.op.open(req, timeout=timeout) as r:
                    raw = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    return raw if binary else raw.decode("utf-8", "replace")
            except Exception as e:
                last = e
                code = getattr(e, "code", None)
                if code in (404, 403, 410):
                    raise
                time.sleep(1.5 * (attempt + 1) + random.random())
        raise last

    def get_json(self, url, **kw):
        return json.loads(self.get(url, **kw))


def jsonl_write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def jsonl_read(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
