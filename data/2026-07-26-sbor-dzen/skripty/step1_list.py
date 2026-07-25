"""Шаг 1: перечислить ВСЕ публикации канала через launcher API (вкладка «Статьи» + общая лента)."""
import json, os, random, sys, time
from dzenlib import Dzen, jsonl_write

CHANNEL = "valentinahli"
OUT = "out"
os.makedirs(OUT, exist_ok=True)

d = Dzen()

START = f"https://dzen.ru/api/v3/launcher/export?channel_name={CHANNEL}"


def norm(item):
    """Вытащить только нужное из карточки."""
    si = item.get("socialInfo") or {}
    ci = item.get("common_image") or {}
    return {
        "oid": item.get("publication_object_id"),
        "pub_id": item.get("publication_id"),
        "item_type": item.get("item_type"),
        "type": item.get("type"),
        "title": item.get("title"),
        "preview": item.get("text"),
        "share_link": item.get("share_link"),
        "publication_date": item.get("publication_date"),
        "views": item.get("views"),
        "likes": si.get("likesCount"),
        "comments": si.get("commentCount"),
        "comments_enabled": si.get("commentsEnabled"),
        "time_to_read_s": item.get("timeToReadSeconds"),
        "cover_url": item.get("image"),
        "cover_tpl": ci.get("url_template"),
        "cover_size": ci.get("orig_size"),
        "cover_main_color": (ci.get("meta") or {}).get("main_color"),
        "publisher_id": item.get("publisher_id"),
        "suites": [s.get("name") if isinstance(s, dict) else s for s in (item.get("suites") or [])],
    }


def crawl(start_url, tag, max_pages=400):
    seen = {}
    url = start_url
    page = 0
    empty_streak = 0
    while url and page < max_pages:
        page += 1
        try:
            data = d.get_json(url)
        except Exception as e:
            print(f"[{tag}] page {page} ERR {type(e).__name__} {e}", flush=True)
            break
        items = data.get("items") or []
        new = 0
        for it in items:
            if it.get("item_type") != "native":
                continue
            oid = it.get("publication_object_id")
            if not oid or oid in seen:
                continue
            seen[oid] = norm(it)
            new += 1
        nxt = (data.get("more") or {}).get("link")
        print(f"[{tag}] page {page}: items={len(items)} new={new} total={len(seen)} more={bool(nxt)}", flush=True)
        if new == 0:
            empty_streak += 1
            if empty_streak >= 4:
                print(f"[{tag}] 4 пустые страницы подряд — стоп", flush=True)
                break
        else:
            empty_streak = 0
        if not nxt:
            break
        url = nxt
        time.sleep(0.35 + random.random() * 0.4)
    return seen


# 1) вкладка «Статьи»
root = d.get_json(START)
tabs = {t["id"]: t["url"] for t in (root.get("tabs") or [])}
print("TABS:", list(tabs), flush=True)

all_items = {}

if "article" in tabs:
    got = crawl(tabs["article"], "articles")
    all_items.update(got)
    print("articles collected:", len(got), flush=True)

# 2) общая лента канала — добирает всё, что не попало во вкладку
got2 = crawl(START, "feed")
before = len(all_items)
for k, v in got2.items():
    all_items.setdefault(k, v)
print(f"feed added {len(all_items) - before}, total {len(all_items)}", flush=True)

# 3) остальные вкладки — для полноты картины (ролики/видео/подборки)
for tid in ("long_video", "short_video"):
    if tid in tabs:
        g = crawl(tabs[tid], tid)
        b = len(all_items)
        for k, v in g.items():
            all_items.setdefault(k, v)
        print(f"{tid} added {len(all_items) - b}, total {len(all_items)}", flush=True)

rows = sorted(all_items.values(), key=lambda r: -int(r.get("publication_date") or 0))
jsonl_write(f"{OUT}/publications.jsonl", rows)
print("SAVED", len(rows), "->", f"{OUT}/publications.jsonl", flush=True)

from collections import Counter
print("by type:", Counter(r["type"] for r in rows), flush=True)
