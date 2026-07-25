"""Механизм: изменилось ли ПРАВИЛО раздачи? Гипотеза — алгоритм стал давать пробную партию показов
и продолжать только при хорошем отклике. Тогда связь CTR×показы на дне должна быть много сильнее."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 60)

m = pd.read_pickle("out/full.pkl")
m["half"] = m["date"].dt.year.astype(str) + "H" + ((m["date"].dt.month > 6).astype(int) + 1).astype(str)

# ---------- 1. Потолок цел, пол обрушился ----------
print("=" * 150)
print("1. ФОРМА РАСПРЕДЕЛЕНИЯ ПОКАЗОВ по полугодиям (потолок vs пол)")
q = m.groupby("half")["shows"].describe(percentiles=[.1, .25, .5, .75, .9])
q["max"] = m.groupby("half")["shows"].max()
print(q[["count", "10%", "25%", "50%", "75%", "90%", "max"]].round(0).to_string())
print("\nотношение 90-й перцентиль / 10-й перцентиль (разброс):")
r = m.groupby("half")["shows"].agg(lambda s: round(s.quantile(.9) / max(s.quantile(.1), 1), 1))
print(r.to_string())

# ---------- 2. Связь CTR и показов по эпохам ----------
print("\n" + "=" * 150)
print("2. СВЯЗЬ CTR × ПОКАЗЫ — стал ли CTR решающим?")
for ep in ("1_до_спада", "2_склон", "3_дно"):
    d = m[(m["эпоха"] == ep)].dropna(subset=["ctr", "shows"])
    rho = d[["ctr", "shows"]].corr(method="spearman").iloc[0, 1]
    print(f"\n{ep} (n={len(d)}): Спирмен CTR×показы = {rho:+.3f}")
    d = d.copy()
    d["ctr_q"] = pd.qcut(d["ctr"], 5, labels=["1 худш", "2", "3", "4", "5 лучш"])
    g = d.groupby("ctr_q", observed=True).agg(n=("shows", "size"), CTR=("ctr", "median"),
                                              мед_показы=("shows", "median"),
                                              мед_дочит=("reads", "median")).round(4)
    g["во_сколько_раз_к_1"] = (g["мед_показы"] / g["мед_показы"].iloc[0]).round(1)
    print(g.to_string())

# ---------- 3. Кто прошёл «пробную партию» ----------
print("\n" + "=" * 150)
print("3. ПРОБНАЯ ПАРТИЯ. Доля статей, застрявших на малых показах")
for ep in ("1_до_спада", "3_дно"):
    d = m[m["эпоха"] == ep]
    print(f"\n{ep} (n={len(d)}):")
    for thr in (3000, 10000, 50000, 200000, 1000000):
        print(f"  показов < {thr:>9,}: {(d.shows < thr).mean():>5.1%}")
    print(f"  показов > 1 млн: {(d.shows > 1e6).mean():.1%}, "
          f"максимум {d.shows.max():,.0f}")

# ---------- 4. Что отличает выживших от застрявших на дне ----------
print("\n" + "=" * 150)
print("4. НА ДНЕ: выжившие (>500 тыс. показов) vs застрявшие (<10 тыс.)")
bot = m[m["эпоха"] == "3_дно"].copy()
bot["группа"] = np.where(bot.shows > 5e5, "выжившие", np.where(bot.shows < 1e4, "застрявшие", "середина"))
print(bot["группа"].value_counts().to_string())
for col in ("сцена", "функция", "порог_входа", "фокус"):
    t = pd.crosstab(bot[col], bot["группа"], normalize="columns").round(3) * 100
    t["разница_пп"] = (t.get("выжившие", 0) - t.get("застрявшие", 0)).round(1)
    print(f"\n--- {col} (% внутри группы) ---")
    print(t.sort_values("разница_пп", ascending=False).to_string())

num = ["n_words", "n_images", "n_headers", "time_to_read_s", "ctr", "read_rate",
       "brightness", "saturation", "contrast", "warm", "спорность"]
print("\n--- числовые признаки (медианы) ---")
bot2 = bot.copy()
bot2["спорность"] = pd.to_numeric(bot2["спорность"], errors="coerce")
print(bot2.groupby("группа")[num].median().round(3).to_string())

# ---------- 5. Инвестиция объёма vs отдача ----------
print("\n" + "=" * 150)
print("5. КУДА ИДЁТ ОБЪЁМ И ЧТО ОН ПРИНОСИТ (эпоха дно, 2025-11..2026-07)")
inv = bot.groupby("сцена").agg(статей=("oid", "size"), мед_показы=("shows", "median"),
                               мед_дочит=("reads", "median"), сумма_дочит=("reads", "sum"),
                               мед_CTR=("ctr", "median")).round(4)
inv["доля_статей_%"] = (inv["статей"] / inv["статей"].sum() * 100).round(1)
inv["доля_дочитываний_%"] = (inv["сумма_дочит"] / inv["сумма_дочит"].sum() * 100).round(1)
inv["перекос"] = (inv["доля_дочитываний_%"] / inv["доля_статей_%"]).round(2)
print(inv.sort_values("перекос", ascending=False).to_string())
