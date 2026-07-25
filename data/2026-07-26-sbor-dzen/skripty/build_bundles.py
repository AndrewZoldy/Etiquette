"""Собрать по одному пакету на статью: текст + обложка + полотно + кадры в контексте + комментарии."""
import glob, json, os

OUT = "out"
BD = os.path.join(OUT, "bundles")
os.makedirs(BD, exist_ok=True)
SH = os.path.abspath(os.path.join(OUT, "img", "sheets")).replace("\\", "/")
CV = os.path.abspath(os.path.join(OUT, "img", "covers_512")).replace("\\", "/")


def frame_context(seq, images):
    out, k = [], 0
    for i, el in enumerate(seq):
        if el.get("k") != "image":
            continue
        before = next((seq[j].get("t") or "" for j in range(i - 1, -1, -1)
                       if seq[j].get("k") in ("p", "header", "li", "quote")), "")
        after = next((seq[j].get("t") or "" for j in range(i + 1, len(seq))
                      if seq[j].get("k") in ("p", "header", "li", "quote")), "")
        out.append({"n": k, "текст_перед": before[:350], "текст_после": after[:350],
                    "подпись": images[k].get("caption") if k < len(images) else None})
        k += 1
    return out


def pick_comments(path, oid):
    """Отобрать представительный набор: топ по лайкам, топ по дизлайкам, свежие, длинные ветки."""
    p = os.path.join(OUT, "comments", oid + ".json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    cs = d.get("comments") or []
    if not cs:
        return {"всего": 0, "корневых": 0, "ответов": 0, "выборка": []}
    for c in cs:
        c["likes"] = c.get("likes") or 0
        c["dislikes"] = c.get("dislikes") or 0
        c["children"] = c.get("children") or 0
    top = sorted(cs, key=lambda c: -c["likes"])[:30]
    dis = sorted(cs, key=lambda c: -c["dislikes"])[:10]
    fresh = sorted(cs, key=lambda c: -(c.get("created_ts") or 0))[:15]
    threads = sorted([c for c in cs if c["level"] == "root"],
                     key=lambda c: -c["children"])[:8]
    seen, sample = set(), []
    for group, tag in ((top, "залайкан"), (dis, "заминусован"),
                       (threads, "длинная ветка"), (fresh, "свежий")):
        for c in group:
            if c["id"] in seen:
                continue
            seen.add(c["id"])
            sample.append({"метка": tag, "уровень": c["level"], "автор": c.get("author_name"),
                           "лайков": c["likes"], "дизлайков": c["dislikes"],
                           "ответов": c["children"], "от_автора_канала": c.get("published_by_channel"),
                           "текст": (c.get("text") or "")[:900]})
    return {"всего": len(cs),
            "корневых": sum(1 for c in cs if c["level"] == "root"),
            "ответов": sum(1 for c in cs if c["level"] == "child"),
            "выборка": sample[:70]}


made, no_comments = 0, 0
index = []
for fn in sorted(glob.glob("out/pages/*.json")):
    d = json.load(open(fn, encoding="utf-8"))
    oid = d["oid"]
    imgs = d.get("images") or []
    bundle = {
        "oid": oid,
        "заголовок": d.get("title"),
        "слов": d.get("n_words"),
        "абзацев": d.get("n_paragraphs"),
        "подзаголовки": d.get("headers") or [],
        "цитаты": d.get("quotes") or [],
        "списки": d.get("list_items") or [],
        "текст": d.get("text") or "",
        "обложка_файл": f"{CV}/{oid}.jpg" if os.path.exists(f"out/img/covers_512/{oid}.jpg") else None,
        "полотно_файл": f"{SH}/{oid}.jpg" if os.path.exists(f"out/img/sheets/{oid}.jpg") else None,
        "кадров": len(imgs),
        "кадры_в_контексте": frame_context(d.get("sequence") or [], imgs),
    }
    c = pick_comments(None, oid)
    if c is None:
        no_comments += 1
        bundle["комментарии"] = {"всего": 0, "примечание": "комментарии не собраны"}
    else:
        bundle["комментарии"] = c
    p = os.path.join(BD, oid + ".json")
    json.dump(bundle, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    index.append({"oid": oid, "заголовок": bundle["заголовок"],
                  "пакет": os.path.abspath(p).replace("\\", "/"),
                  "комментариев": bundle["комментарии"].get("всего", 0)})
    made += 1

json.dump(index, open(os.path.join(BD, "_index.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
sz = sum(os.path.getsize(os.path.join(BD, f)) for f in os.listdir(BD)) / 1048576
print(f"пакетов собрано {made}, без комментариев {no_comments}, объём {sz:.0f} МБ")
print(f"средний пакет {sz*1024/max(made,1):.0f} КБ")
print("каталог:", os.path.abspath(BD))
