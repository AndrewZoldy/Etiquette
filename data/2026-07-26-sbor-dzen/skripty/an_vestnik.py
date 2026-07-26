"""Целевой разбор рубрики «Светская жизнь Петербурга» / «Культурный вѣстникъ»."""
import glob, json, os, re
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 60)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna()].copy()
tf = pd.read_pickle("out/text_feats.pkl")
dup = [c for c in tf.columns if c != "oid" and c in m.columns]
tf = tf.rename(columns={c: "т_" + c for c in dup})
m = m.merge(tf, on="oid", how="left")

PAT = r"(Светск|вестник|вёстник|Культурн)"
v = m[m["title_studio"].astype(str).str.contains(PAT, case=False, na=False)].copy()
print(f"найдено статей рубрики: {len(v)}")
print(v[["date", "title_studio", "shows", "opens", "reads", "ctr", "read_rate",
         "comments", "likes", "subs", "n_words", "n_images", "comments_enabled"]]
      .sort_values("date").to_string(index=False))

print("\n" + "=" * 140)
print("СВОДКА РУБРИКИ против канала")
rest = m[~m.index.isin(v.index)]
rows = []
for lbl, d in (("рубрика", v), ("канал без рубрики", rest),
               ("канал, эпоха дно", rest[rest["эпоха"] == "3_дно"])):
    rows.append({
        "группа": lbl, "n": len(d),
        "мед_показы": int(d["shows"].median()),
        "мед_открытия": int(d["opens"].median()),
        "мед_дочит": int(d["reads"].median()),
        "мед_CTR": round(d["ctr"].median(), 4),
        "мед_дочитываемость": round(d["read_rate"].median(), 3),
        "мед_комм": int(d["comments"].median()),
        "мед_лайки": int(d["likes"].median()),
        "мед_подписки": int(d["subs"].median()),
        "мед_слов": int(d["n_words"].median()) if d["n_words"].notna().any() else None,
        "мед_картинок": int(d["n_images"].median()) if d["n_images"].notna().any() else None,
        "мед_мин_на_дочит": round(d["min_per_read"].median(), 2),
    })
print(pd.DataFrame(rows).to_string(index=False))

print("\n" + "=" * 140)
print("ГЛАВНЫЙ ВОПРОС: где именно теряются люди — на клике или в чтении?")
print("Воронка рубрики (медианы):")
print(f"  показы      {v.shows.median():>10,.0f}")
print(f"  открытия    {v.opens.median():>10,.0f}   = CTR {v.ctr.median():.2%}")
print(f"  дочитывания {v.reads.median():>10,.0f}   = дочитываемость {v.read_rate.median():.1%}")
print("\nВоронка канала на дне (медианы):")
b = rest[rest["эпоха"] == "3_дно"]
print(f"  показы      {b.shows.median():>10,.0f}")
print(f"  открытия    {b.opens.median():>10,.0f}   = CTR {b.ctr.median():.2%}")
print(f"  дочитывания {b.reads.median():>10,.0f}   = дочитываемость {b.read_rate.median():.1%}")

print("\n" + "=" * 140)
print("СРАВНЕНИЕ ПО ДЛИНЕ: рубрика против статей канала")
print(f"рубрика: медиана слов {v.n_words.median():.0f}, "
      f"диапазон {v.n_words.min():.0f}–{v.n_words.max():.0f}")
print(f"канал:   медиана слов {rest.n_words.median():.0f}")
print(f"\nвремя чтения по Дзену (сек): рубрика {v.time_to_read_s.median():.0f}, "
      f"канал {rest.time_to_read_s.median():.0f}")
print(f"минут на дочитывание: рубрика {v.min_per_read.median():.2f}, "
      f"канал {rest.min_per_read.median():.2f}")

print("\n" + "=" * 140)
print("ДОЧИТЫВАЕМОСТЬ ПРОТИВ ДЛИНЫ ТЕКСТА по всему каналу (эпоха дно, без серии вт/чт)")
d = rest[(rest["эпоха"] == "3_дно") & (rest["comments_enabled"] == True)].dropna(subset=["n_words"]).copy()
d["дл"] = pd.cut(d["n_words"], [0, 450, 600, 800, 1200, 9999],
                 labels=["до 450", "450-600", "600-800", "800-1200", "больше 1200"])
print(d.groupby("дл", observed=True).agg(n=("shows", "size"), слов=("n_words", "median"),
                                         дочитываемость=("read_rate", "median"),
                                         мед_дочит=("reads", "median"),
                                         мин_на_дочит=("min_per_read", "median")).round(3).to_string())

print("\n" + "=" * 140)
print("СТРУКТУРА ТЕКСТОВ РУБРИКИ: подзаголовки, вопросы, абзацы")
cols = ["title_studio", "n_words", "n_paragraphs", "n_headers", "вопросов",
         "длина_последнего_абзаца", "слов_в_абзаце_мед", "n_images", "read_rate", "reads"]
cols = [c for c in cols if c in v.columns]
print(v[cols].sort_values("reads", ascending=False).to_string(index=False))

print("\n" + "=" * 140)
print("КОММЕНТАРИИ К РУБРИКЕ: что пишут читатели")
for _, r in v.sort_values("comments", ascending=False).head(6).iterrows():
    p = f"out/comments/{r['oid']}.json"
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    cs = sorted(d.get("comments") or [], key=lambda c: -(c.get("likes") or 0))
    print(f"\n--- {r['title_studio']} ({r['comments']:.0f} комм., {r['reads']:.0f} дочит.) ---")
    for c in cs[:5]:
        print(f"  [+{c.get('likes')}/-{c.get('dislikes')}] {c.get('author_name')}: "
              f"{(c.get('text') or '')[:200]}")

v.to_pickle("out/vestnik.pkl")
print("\nсохранено out/vestnik.pkl")
