"""Вовлечённость и раздача: стало ли обсуждение двигателем? Плюс разбор рубрик и серий."""
import re
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna()].copy()

print("=" * 140)
print("1. ВОВЛЕЧЁННОСТЬ КАК ДВИГАТЕЛЬ: связь долей отклика с показами, по эпохам")
for ep in ("1_до_спада", "3_дно"):
    d = m[m["эпоха"] == ep]
    print(f"\n--- {ep} (n={len(d)}) --- Спирмен с ПОКАЗАМИ:")
    for c in ("ctr", "read_rate", "likes_per_read", "comments_per_read", "subs_per_read",
              "min_per_read"):
        x = d.dropna(subset=[c, "shows"])
        if len(x) > 30:
            print(f"   {c:20s} {x[[c,'shows']].corr(method='spearman').iloc[0,1]:+.3f}")

print("\n" + "=" * 140)
print("2. КОММЕНТАРИИ НА ДОЧИТЫВАНИЕ по квинтилям (эпоха дно) — при контроле на CTR")
bot = m[m["эпоха"] == "3_дно"].dropna(subset=["comments_per_read", "ctr"]).copy()
bot["ctr_q"] = pd.qcut(bot["ctr"], 3, labels=["низкий CTR", "средний", "высокий"])
bot["cpr_q"] = pd.qcut(bot["comments_per_read"], 3, labels=["мало обсуждают", "средне", "много"])
piv = bot.pivot_table(index="cpr_q", columns="ctr_q", values="shows", aggfunc="median", observed=True)
cnt = bot.pivot_table(index="cpr_q", columns="ctr_q", values="shows", aggfunc="size", observed=True)
print("медиана показов:")
print(piv.round(0).to_string())
print("\nчисло статей:")
print(cnt.to_string())

print("\n" + "=" * 140)
print("3. МИНУТ НА ДОЧИТЫВАНИЕ (глубина чтения) vs показы")
for ep in ("1_до_спада", "3_дно"):
    d = m[m["эпоха"] == ep].dropna(subset=["min_per_read"]).copy()
    if len(d) < 40:
        continue
    d["q"] = pd.qcut(d["min_per_read"], 4, labels=["1 быстро", "2", "3", "4 долго"], duplicates="drop")
    g = d.groupby("q", observed=True).agg(n=("shows", "size"), минут=("min_per_read", "median"),
                                          мед_показы=("shows", "median"),
                                          мед_дочит=("reads", "median")).round(3)
    print(f"\n-- {ep} --")
    print(g.to_string())

print("\n" + "=" * 140)
print("4. РУБРИКИ И СЕРИИ: статьи с повторяющимся началом заголовка")
m["префикс"] = m["title_studio"].astype(str).str.extract(r"^([А-ЯЁA-Z][^:.,?!]{3,28})")[0]
ser = m.groupby("префикс").agg(n=("shows", "size"), мед_показы=("shows", "median"),
                               мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"))
ser = ser[ser["n"] >= 4].sort_values("n", ascending=False)
print(ser.head(25).round(4).to_string())

print("\n" + "=" * 140)
print("5. РУБРИКА «Светская жизнь Петербурга»")
sv = m[m["title_studio"].astype(str).str.contains("Светская жизнь", na=False)]
print(f"статей: {len(sv)}, период {sv.date.min().date()} — {sv.date.max().date()}")
print(f"медиана показов {sv.shows.median():,.0f}, дочитываний {sv.reads.median():,.0f}, "
      f"CTR {sv.ctr.median():.4f}")
print(f"суммарно дочитываний: {sv.reads.sum():,.0f} "
      f"({sv.reads.sum()/m.reads.sum()*100:.2f}% всех дочитываний канала при "
      f"{len(sv)/len(m)*100:.1f}% статей)")
print("\nпоследние 10:")
print(sv.nlargest(10, "date")[["date", "title_studio", "shows", "opens", "reads", "ctr"]].to_string(index=False))

print("\n" + "=" * 140)
print("6. СКОЛЬКО ВНИМАНИЯ УХОДИТ В НИКУДА (эпоха дно)")
b = m[m["эпоха"] == "3_дно"]
dead = b[b["shows"] < 10000]
print(f"статей с показами меньше 10 тыс.: {len(dead)} из {len(b)} ({len(dead)/len(b)*100:.0f}%)")
print(f"их суммарные дочитывания: {dead.reads.sum():,.0f} из {b.reads.sum():,.0f} "
      f"({dead.reads.sum()/b.reads.sum()*100:.1f}%)")
print("\nсостав по сценам:")
print(dead["сцена"].value_counts().to_string())
print("\nсостав по функции:")
print(dead["функция"].value_counts().to_string())
