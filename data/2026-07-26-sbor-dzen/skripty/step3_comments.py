"""Шаг 3: скачать все комментарии (корневые + ответы) по каждой статье."""
import json, os, random, threading, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dzenlib import Dzen, jsonl_read

OUT = "out"
CDIR = os.path.join(OUT, "comments")
os.makedirs(CDIR, exist_ok=True)
BASE = "https://dzen.ru/api/comments/v2/"
PUB = "63dd27aac30ab522dcce48b3"
MAX_ROOT_PAGES = 60
MAX_CHILD_PAGES = 40

tl = threading.local()


def sess(link):
    if not hasattr(tl, "d"):
        tl.d = Dzen(referer=link)
        tl.d.op.addheaders += [("X-Zen-Comments-Clid", "300"),
                               ("X-Zen-Comments-Place", "article"),
                               ("X-Zen-Comments-Product", "zen")]
    return tl.d


def call(d, method, params=None, more=None):
    q = more.lstrip("?&") if more else urllib.parse.urlencode(params)
    return d.get_json(BASE + method + "?" + q, timeout=45)


def harvest(d, oid, doc):
    """Вернуть (comments, users, meta)."""
    users, metas, out = {}, {}, []
    meta = {}

    def absorb(r):
        users.update(r.get("usersById") or {})
        metas.update(r.get("metaByCommentId") or {})

    # корневые
    roots = []
    more = None
    for page in range(MAX_ROOT_PAGES):
        if more:
            r = call(d, "root-comments", more=more)
        else:
            r = call(d, "root-comments", dict(documentId=doc, publicationPublisherId=PUB,
                                              sorting="oldest", batchSize="50", withConfig="true"))
        absorb(r)
        meta = r.get("meta") or meta
        items = r.get("items") or []
        for x in items:
            ed = x.get("entityData") or {}
            if ed.get("id"):
                roots.append(ed)
        more = r.get("moreItemsQueryString")
        if not more or not items:
            break
        time.sleep(0.15)

    for ed in roots:
        out.append(dict(ed, _level="root"))

    # ответы
    for ed in roots:
        cid = str(ed["id"])
        n = (metas.get(cid) or {}).get("childrenCount") or 0
        if not n:
            continue
        more = None
        for page in range(MAX_CHILD_PAGES):
            try:
                if more:
                    r = call(d, "child-comments", more=more)
                else:
                    r = call(d, "child-comments", dict(rootCommentId=cid, documentId=doc,
                                                       publicationPublisherId=PUB,
                                                       withConfig="true", batchSize="20"))
            except Exception:
                break
            absorb(r)
            items = r.get("items") or []
            for x in items:
                ced = x.get("entityData") or {}
                if ced.get("id"):
                    out.append(dict(ced, _level="child", _root=cid))
            more = r.get("moreItemsQueryString")
            if not more or not items:
                break
            time.sleep(0.15)

    # склеить с метриками и авторами
    res = []
    seen = set()
    for c in out:
        cid = str(c["id"])
        if cid in seen:
            continue
        seen.add(cid)
        m = metas.get(cid) or {}
        u = users.get(str(c.get("authorUid"))) or {}
        pubr = u.get("publisher") or {}
        res.append({
            "id": c["id"],
            "level": c["_level"],
            "root_id": c.get("_root") or (c.get("rootCommentId") if c["_level"] == "child" else None),
            "created_ts": c.get("createdTs"),
            "author_uid": c.get("authorUid"),
            "author_name": u.get("displayName") or u.get("name") or pubr.get("name") or "",
            "author_channel": pubr.get("name") or "",
            "author_channel_path": pubr.get("channelPath") or "",
            "published_by_channel": c.get("publishedByChannel"),
            "text": c.get("text") or "",
            "likes": m.get("likes"),
            "dislikes": m.get("dislikes"),
            "children": m.get("childrenCount"),
            "pinned": m.get("isPinned"),
            "state": m.get("state"),
            "owner_reaction": m.get("publicationChannelOwnerReaction"),
            "n_media": len(c.get("mediaItems") or []),
        })
    return res, meta


def main():
    pubs = jsonl_read(os.path.join(OUT, "publications.jsonl"))
    pubs = [p for p in pubs if (p.get("comments") or 0) > 0]
    todo = [p for p in pubs if not os.path.exists(os.path.join(CDIR, p["oid"] + ".json"))]
    print(f"статей с комментариями {len(pubs)}, осталось {len(todo)}", flush=True)

    lock = threading.Lock()
    st = {"done": 0, "coms": 0}

    def worker(p):
        oid = p["oid"]
        d = sess(p.get("share_link") or "https://dzen.ru/")
        try:
            rows, meta = harvest(d, oid, f"native:{oid}")
            with open(os.path.join(CDIR, oid + ".json"), "w", encoding="utf-8") as f:
                json.dump({"oid": oid, "title": p.get("title"), "meta": meta,
                           "expected": p.get("comments"), "got": len(rows),
                           "comments": rows}, f, ensure_ascii=False)
            with lock:
                st["done"] += 1
                st["coms"] += len(rows)
                if st["done"] % 20 == 0 or st["done"] < 4:
                    print(f"  {st['done']}/{len(todo)} собрано {st['coms']} комм. "
                          f"(последняя: {len(rows)}/{p.get('comments')}) «{str(p.get('title'))[:40]}»",
                          flush=True)
        except Exception as e:
            with lock:
                print(f"  FAIL {oid} {type(e).__name__} {e}", flush=True)
        time.sleep(0.2 + random.random() * 0.3)

    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(worker, todo))
    print(f"ГОТОВО. файлов {len(os.listdir(CDIR))}, комментариев {st['coms']}", flush=True)


if __name__ == "__main__":
    main()
