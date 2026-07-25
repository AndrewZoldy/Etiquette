"""Шаг 2: скачать страницы статей, извлечь полный текст и все блоки иллюстраций."""
import json, os, random, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from dzenlib import Dzen, jsonl_read

OUT = "out"
PAGES = os.path.join(OUT, "pages")
os.makedirs(PAGES, exist_ok=True)

DEC = json.JSONDecoder()
IMG_TPL = "https://avatars.dzeninfra.ru/get-zen_doc/271828/pub_{oid}_{img}/{size}"


def extract(html, oid):
    """Достать из SSR-данных публикацию и раскодировать draftJsState."""
    res = {"oid": oid}

    # 1) publication meta
    key = '"publication":{"id":"%s"' % oid
    i = html.find(key)
    if i < 0:
        i = html.find('"publication":{')
    if i >= 0:
        j = html.find("{", i + len('"publication":') - 1)
        try:
            pub, _ = DEC.raw_decode(html, html.index("{", i + 14))
        except Exception:
            pub = None
        if isinstance(pub, dict):
            res["publishTime"] = pub.get("publishTime")
            res["addTime"] = pub.get("addTime")
            res["modificationTime"] = pub.get("modificationTime")
            content = pub.get("content") or {}
            ac = content.get("articleContent") or {}
            res["content_type"] = content.get("type")
            res["tags"] = pub.get("tags") or content.get("tags")
            res["article_title"] = ac.get("title") or content.get("title")
            res["preview_text"] = ac.get("preview") or content.get("preview")
            cs = ac.get("contentState")
            if isinstance(cs, str):
                try:
                    res["draft"] = json.loads(cs)
                except Exception:
                    res["draft"] = None

    # 2) fallback: вытащить contentState напрямую
    if not res.get("draft"):
        k = html.find('"contentState":')
        if k >= 0:
            try:
                s, _ = DEC.raw_decode(html, html.index('"', k + len('"contentState":')))
                res["draft"] = json.loads(s)
            except Exception:
                pass

    # 3) заголовок / метрики из socialMetaResponse
    m = re.search(r'"metaInfo":\{[^}]*"commentsCount":(\d+),"likeCount":(\d+)', html)
    if m:
        res["comments_count_page"] = int(m.group(1))
        res["likes_count_page"] = int(m.group(2))
    m = re.search(r'<meta property="og:title" content="([^"]*)"', html)
    if m:
        res["og_title"] = m.group(1)
    m = re.search(r'"viewsCount":(\d+)', html)
    if m:
        res["views_page"] = int(m.group(1))

    # 4) разложить draft на текст и картинки
    blocks = ((res.get("draft") or {}).get("draftJsState") or {}).get("blocks") or []
    entity = ((res.get("draft") or {}).get("draftJsState") or {}).get("entityMap") or {}
    paras, images, headers, quotes, lists = [], [], [], [], []
    seq = []
    for b in blocks:
        bt = b.get("type") or ""
        txt = (b.get("text") or "").strip()
        if bt.startswith("atomic:image") or (b.get("data") or {}).get("image"):
            img = ((b.get("data") or {}).get("image") or {})
            iid = img.get("id")
            if iid:
                images.append({"id": iid,
                               "url": IMG_TPL.format(oid=oid, img=iid, size="scale_1200"),
                               "caption": txt or None,
                               "pos": len(seq)})
                seq.append({"k": "image", "id": iid})
            continue
        if not txt:
            continue
        if bt.startswith("header"):
            headers.append(txt); seq.append({"k": "header", "t": txt})
        elif bt == "blockquote":
            quotes.append(txt); seq.append({"k": "quote", "t": txt})
        elif "list-item" in bt:
            lists.append(txt); seq.append({"k": "li", "t": txt})
        else:
            paras.append(txt); seq.append({"k": "p", "t": txt})

    links = []
    for v in entity.values():
        if isinstance(v, dict) and (v.get("type") or "").lower() == "link":
            links.append(((v.get("data") or {}).get("url") or ""))

    full = "\n\n".join(paras)
    res.pop("draft", None)
    res.update({
        "paragraphs": paras,
        "headers": headers,
        "quotes": quotes,
        "list_items": lists,
        "images": images,
        "links": links,
        "sequence": seq,
        "n_paragraphs": len(paras),
        "n_images": len(images),
        "n_headers": len(headers),
        "n_chars": len(full),
        "n_words": len(full.split()),
        "text": full,
    })
    return res


def main():
    pubs = jsonl_read(os.path.join(OUT, "publications.jsonl"))
    todo = [p for p in pubs if not os.path.exists(os.path.join(PAGES, p["oid"] + ".json"))]
    print(f"всего {len(pubs)}, осталось {len(todo)}", flush=True)

    lock = threading.Lock()
    done = [0]
    sessions = threading.local()

    def worker(p):
        if not hasattr(sessions, "d"):
            sessions.d = Dzen()
        oid, link = p["oid"], p.get("share_link")
        if not link:
            return
        try:
            html = sessions.d.get(link, timeout=60)
            rec = extract(html, oid)
            rec["title"] = p.get("title")
            rec["share_link"] = link
            with open(os.path.join(PAGES, oid + ".json"), "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False)
            with lock:
                done[0] += 1
                if done[0] % 20 == 0 or done[0] < 5:
                    print(f"  {done[0]}/{len(todo)} last={rec['n_words']}w {rec['n_images']}img "
                          f"«{str(p.get('title'))[:45]}»", flush=True)
        except Exception as e:
            with lock:
                print(f"  FAIL {oid} {type(e).__name__} {e}", flush=True)
        time.sleep(0.25 + random.random() * 0.35)

    with ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(worker, todo))

    print("ГОТОВО. файлов:", len(os.listdir(PAGES)), flush=True)


if __name__ == "__main__":
    main()
