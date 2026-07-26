"""Полный разбор корпуса комментариев: присутствие автора, хейт, что лайкают."""
import glob, json, re
from collections import Counter
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 100)

AUTHOR = "Валентина Хлистун | Этикет"

rows = []
per = []
for f in glob.glob("out/comments/*.json"):
    d = json.load(open(f, encoding="utf-8"))
    cs = d.get("comments") or []
    if not cs:
        continue
    oid = d["oid"]
    a_cnt = sum(1 for c in cs if (c.get("author_name") or "") == AUTHOR)
    liked = sum(1 for c in cs if (c.get("owner_reaction") or "none") != "none")
    per.append({"oid": oid, "всего": len(cs),
                "ответов_автора": a_cnt, "лайков_автора": liked,
                "корневых": sum(1 for c in cs if c["level"] == "root")})
    for c in cs:
        rows.append({"oid": oid, "author": c.get("author_name") or "",
                     "text": c.get("text") or "", "likes": c.get("likes") or 0,
                     "dislikes": c.get("dislikes") or 0,
                     "children": c.get("children") or 0, "level": c["level"]})

cm = pd.DataFrame(rows)
pa = pd.DataFrame(per)
print(f"комментариев {len(cm):,}, статей {len(pa)}")

print("\n" + "=" * 130)
print("1. ПРИСУТСТВИЕ АВТОРА В ОБСУЖДЕНИЯХ")
print(f"ответов от канала всего: {pa['ответов_автора'].sum()}")
print(f"статей, где автор ответил хотя бы раз: {(pa['ответов_автора'] > 0).sum()} из {len(pa)}"
      f" ({(pa['ответов_автора'] > 0).mean():.1%})")
print(f"лайков автора комментариям всего: {pa['лайков_автора'].sum()}")
print(f"статей, где автор лайкнул хотя бы один комментарий: {(pa['лайков_автора'] > 0).sum()}")
print(f"доля ответов автора в общем объёме: {pa['ответов_автора'].sum()/len(cm):.4%}")
au = cm[cm["author"] == AUTHOR]
if len(au):
    print("\nчто именно пишет автор (до 8 примеров):")
    for _, r in au.nlargest(8, "likes").iterrows():
        print(f"  [+{r.likes}] {r.text[:200]}")

print("\n" + "=" * 130)
print("2. ЧТО ЛАЙКАЮТ ЧИТАТЕЛИ: типы самых залайканных комментариев")
top = cm.nlargest(300, "likes").copy()
PAT = {
    "своя история": r"(у меня|мой муж|моя мама|моя свекров|у нас|когда я|однажды|помню|"
                    r"мы всегда|в моей|моя подруга|мой сын|моя дочь)",
    "возражение автору": r"(не согласн|бред|чушь|ерунда|неправда|это не так|автор|вы пишете|"
                        r"кто вы|не учите|надуманн|глупост)",
    "шутка/цитата": r"(\(с\)|анекдот|ха-ха|😂|🤣|как говорил|классик)",
    "поддержка": r"(спасибо|благодар|согласна|верно|прекрасн|полезн|люблю ваш)",
    "дополнение правила": r"(я бы добавила|ещё стоит|также важно|не забудьте|добавлю)",
}
cnt = Counter()
for _, r in top.iterrows():
    low = r.text.lower()
    hit = [k for k, p in PAT.items() if re.search(p, low)]
    cnt[hit[0] if hit else "прочее"] += 1
print("среди 300 самых залайканных:")
for k, v in cnt.most_common():
    print(f"   {v:4d}  {k}")

print("\n" + "=" * 130)
print("3. ХЕЙТ: таксономия претензий по всему корпусу")
HATE = {
    "оторванность от жизни": r"(в реальной жизни|где вы такое|кто так дела|в жизни так не|"
                             r"не встречал|не бывает|выдумк|фантаз)",
    "нет личного опыта": r"(у которого нет|не был[аи]? (в браке|замужем)|у вас нет|"
                        r"судя по всему,? вы|видно.{0,15}не )",
    "нейросеть / ИИ": r"(нейросет|искусственн(ый|ым) интеллект|\bии\b|chatgpt|gpt|"
                      r"написан[оа] (ботом|машиной)|сгенерир)",
    "вода, нет смысла": r"(вод[аыу] лить|воды налил|ни о чём|пустая статья|слов много|"
                        r"в одно предложение|очевидн|банальн|и так все знают)",
    "устарело": r"(устарел|прошл(ый|ого) век|при царе|позапрошл|девятнадцат|"
                r"дореволюц|уже не актуальн)",
    "снобизм, поучение": r"(не учите|кто вы такая|высокомерн|снобизм|поучает|учить жить|"
                         r"возомнил|напыщен|манернич|зазнал)",
    "не по деньгам": r"(не для наших|на такие зарплат|у кого есть деньги|нищ|пенси|"
                     r"не по карману|барск|роскош|богатеньк)",
    "навязывание": r"(кому надо|каждый сам|не ваше дело|зачем это|кому это нужно|"
                   r"почему я должен|никто не обязан)",
    "агрессия": r"(дур[аон]\b|идиот|тупост|мерзк|отвратит|ненавиж|заткн|позор)",
}
HC = {k: re.compile(v, re.I) for k, v in HATE.items()}
res = []
for k, rx in HC.items():
    m = cm[cm["text"].str.contains(rx, na=False)]
    res.append({"претензия": k, "комментариев": len(m),
                "доля_корпуса": round(len(m) / len(cm) * 100, 2),
                "медиана_лайков": float(m["likes"].median()) if len(m) else 0,
                "сумма_лайков": int(m["likes"].sum())})
h = pd.DataFrame(res).sort_values("комментариев", ascending=False)
print(h.to_string(index=False))
print(f"\nдля сравнения: медиана лайков по всему корпусу {cm['likes'].median():.0f}, "
      f"среднее {cm['likes'].mean():.1f}")

print("\n" + "=" * 130)
print("4. САМЫЕ ЗАЛАЙКАННЫЕ ПРЕТЕНЗИИ (топ-12)")
mask = cm["text"].str.contains("|".join(HATE.values()), case=False, na=False, regex=True)
for _, r in cm[mask].nlargest(12, "likes").iterrows():
    print(f"\n[+{r.likes} -{r.dislikes}] {r.author}: {r.text[:280]}")

pa.to_pickle("out/comm_author.pkl")
cm.to_pickle("out/comments_full.pkl")
