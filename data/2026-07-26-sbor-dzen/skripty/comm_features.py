"""Машинная обработка комментариев: агрегаты по статьям, авторы, маркеры конфликта."""
import glob, json, os, re
from collections import Counter
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)

MARK = {
    "агрессия": r"(дур[аон]|идиот|бред|чушь|glupost|глупост|чепух|ерунд|бесит|достал|"
                r"противн|мерзк|отвратит|ненавиж|тошнит|фу\b|позор)",
    "снобизм_упрёк": r"(снобизм|высокомерн|поучает|поучени|учить жить|не учите|"
                     r"кто вы такая|возомнил|надуманн|напыщенн|манернича)",
    "бедность_упрёк": r"(не для наших|на такие зарплаты|у кого есть деньги|богат|барск|"
                      r"нищ|пенси|зарплат|не по карману|роскош)",
    "оторванность": r"(в реальной жизни|в жизни так не|где вы такое|кто так дела|"
                    r"устарел|прошл[ыо][йм] век|при царе|не актуальн)",
    "несогласие": r"(не согласн|ерунда|спорно|неправда|это не так|ничего подобного|"
                  r"почему нельзя|а если|с чего вы взяли|откуда это)",
    "поддержка": r"(спасибо|благодар|согласн|верно|正|прекрасн|отличн|полезн|"
                 r"интересн|люблю ваш|подписал|прав[аы] на всё)",
    "личный_опыт": r"(у меня|мой муж|моя мама|моя свекров|у нас в семье|когда я|"
                   r"однажды|помню|мы всегда)",
    "вопрос_автору": r"(а что если|подскажите|а как быть|скажите пожалуйста|"
                     r"а если гость|что делать если)",
    "обращение_к_автору": r"(валентин|автор|вы пишете|вы говорите|ваша статья)",
}
COMP = {k: re.compile(v, re.I) for k, v in MARK.items()}
WORD = re.compile(r"[А-Яа-яЁёA-Za-z]+")

rows, per_article = [], []
authors = Counter()
author_neg = Counter()

files = sorted(glob.glob("out/comments/*.json"))
print("файлов комментариев:", len(files))
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    cs = d.get("comments") or []
    if not cs:
        continue
    oid = d["oid"]
    n_root = sum(1 for c in cs if c["level"] == "root")
    n_child = len(cs) - n_root
    lens, likes, dislikes = [], [], []
    flags = Counter()
    author_replies = 0
    for c in cs:
        t = (c.get("text") or "")
        low = t.lower()
        lens.append(len(WORD.findall(t)))
        likes.append(c.get("likes") or 0)
        dislikes.append(c.get("dislikes") or 0)
        for k, rx in COMP.items():
            if rx.search(low):
                flags[k] += 1
        if c.get("published_by_channel"):
            author_replies += 1
        a = c.get("author_name") or c.get("author_uid")
        if a:
            authors[str(a)] += 1
            if COMP["агрессия"].search(low) or COMP["снобизм_упрёк"].search(low):
                author_neg[str(a)] += 1
        rows.append({"oid": oid, "id": c["id"], "level": c["level"],
                     "author": c.get("author_name"), "uid": c.get("author_uid"),
                     "text": t, "likes": c.get("likes"), "dislikes": c.get("dislikes"),
                     "children": c.get("children"), "ts": c.get("created_ts")})
    n = len(cs)
    rec = {"oid": oid, "комментариев": n, "корневых": n_root, "ответов": n_child,
           "глубина_обсуждения": round(n_child / max(n_root, 1), 2),
           "медиана_длины": float(np.median(lens)),
           "доля_длинных": round(float(np.mean([x > 50 for x in lens])), 3),
           "сумма_лайков": int(np.sum(likes)), "сумма_дизлайков": int(np.sum(dislikes)),
           "медиана_лайков": float(np.median(likes)),
           "ответов_автора": author_replies}
    for k in MARK:
        rec["доля_" + k] = round(flags[k] / n, 3)
    per_article.append(rec)

pa = pd.DataFrame(per_article)
cm = pd.DataFrame(rows)
pa.to_pickle("out/comm_per_article.pkl")
cm.to_pickle("out/comments_all.pkl")
print("статей с комментариями:", len(pa), "| комментариев всего:", len(cm))
print("\nсводка по статьям:")
print(pa.describe().T[["count", "mean", "50%", "max"]].round(3).to_string())

print("\n" + "=" * 130)
print("ТОП-25 самых активных комментаторов канала")
top = pd.DataFrame(authors.most_common(25), columns=["автор", "комментариев"])
top["из_них_резких"] = top["автор"].map(lambda a: author_neg.get(a, 0))
print(top.to_string(index=False))

print("\n" + "=" * 130)
print("САМЫЕ ЗАЛАЙКАННЫЕ КОММЕНТАРИИ КАНАЛА (топ-15)")
t = cm.nlargest(15, "likes")[["likes", "dislikes", "author", "text"]]
for _, r in t.iterrows():
    print(f"\n[+{r.likes} -{r.dislikes}] {r.author}: {str(r.text)[:300]}")

print("\n" + "=" * 130)
print("САМЫЕ СПОРНЫЕ (много дизлайков)")
t = cm.nlargest(10, "dislikes")[["likes", "dislikes", "author", "text"]]
for _, r in t.iterrows():
    print(f"\n[+{r.likes} -{r.dislikes}] {r.author}: {str(r.text)[:250]}")
