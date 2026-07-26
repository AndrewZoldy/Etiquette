"""Своя проверка ключевых утверждений критика: серия вт/чт, обвал пола, CTR-ворота."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna()].copy()
m["half"] = m["date"].dt.year.astype(str) + "H" + ((m["date"].dt.month > 6).astype(int) + 1).astype(str)
m["dow"] = m["date"].dt.dayofweek  # 0=пн
ce = m["comments_enabled"]
print("comments_enabled:", ce.value_counts(dropna=False).to_dict())

s = m[ce == False]
print(f"\n=== СЕРИЯ (комментарии выключены): n={len(s)} ===")
print("период:", s["date"].min().date(), "—", s["date"].max().date())
print("дни недели (0=пн):", s["dow"].value_counts().sort_index().to_dict())
print(f"медиана показов {s.shows.median():,.0f}, дочитываний {s.reads.median():,.0f}, "
      f"CTR {s.ctr.median():.4f}, дочитываемость {s.read_rate.median():.3f}")
print("сцены:", s["сцена"].value_counts().head(5).to_dict())
print(f"статей >1 млн показов: {(s.shows > 1e6).sum()}, максимум {s.shows.max():,.0f}")

w = m[(ce == True) & (m["date"] >= s["date"].min()) & (m["date"] <= s["date"].max())]
print(f"\n=== КОНТРОЛЬ в том же окне (комментарии включены): n={len(w)} ===")
print("дни недели:", w["dow"].value_counts().sort_index().to_dict())
print(f"медиана показов {w.shows.median():,.0f}, дочитываний {w.reads.median():,.0f}, "
      f"CTR {w.ctr.median():.4f}, дочитываемость {w.read_rate.median():.3f}")
print(f"\nРАЗРЫВ по дочитываниям: {w.reads.median()/max(s.reads.median(),1):.0f}x")
print(f"РАЗРЫВ по показам: {w.shows.median()/max(s.shows.median(),1):.0f}x")
print(f"слов: серия {s.n_words.median():.0f}, контроль {w.n_words.median():.0f}")
print(f"картинок: серия {s.n_images.median():.0f}, контроль {w.n_images.median():.0f}")

print("\n=== ТОТ ЖЕ ЖАНР С ВКЛЮЧЁННЫМИ КОММЕНТАРИЯМИ (стол_еда|польза|бытовая) ===")
tri = (m["сцена"] == "стол_еда") & (m["функция"] == "польза") & (m["порог_входа"] == "бытовая")
a = m[tri & (ce == True) & (m["date"] >= "2025-09-16")]
b = m[tri & (ce == False)]
print(f"включены: n={len(a)} медиана дочитываний {a.reads.median():,.0f}")
print(f"выключены: n={len(b)} медиана дочитываний {b.reads.median():,.0f}")

print("\n=== ПОЛ РАСПРЕДЕЛЕНИЯ: сырьё против ce=True ===")
for label, d in (("сырьё", m), ("ce=True", m[ce == True])):
    print(f"\n{label}:")
    t = d.groupby("half").apply(lambda g: pd.Series({
        "n": len(g),
        "доля<10тыс": round((g.shows < 1e4).mean(), 3),
        "доля<3тыс": round((g.shows < 3e3).mean(), 3),
        "p10": int(g.shows.quantile(.1)),
        "p50": int(g.shows.median()),
        "p90": int(g.shows.quantile(.9)),
        "p90/p10": round(g.shows.quantile(.9) / max(g.shows.quantile(.1), 1), 1),
    }), include_groups=False)
    print(t.to_string())

print("\n=== CTR-ВОРОТА: квинтили CTR на ce=True ===")
for ep in ("1_до_спада", "3_дно"):
    for label, d in (("сырьё", m[m["эпоха"] == ep]),
                     ("ce=True", m[(m["эпоха"] == ep) & (ce == True)])):
        x = d.dropna(subset=["ctr"]).copy()
        if len(x) < 30:
            continue
        x["q"] = pd.qcut(x["ctr"], 5, labels=[1, 2, 3, 4, 5])
        g = x.groupby("q", observed=True)["shows"].median()
        rho = x[["ctr", "shows"]].corr(method="spearman").iloc[0, 1]
        print(f"{ep:12s} {label:8s} n={len(x):3d} медианы показов по квинтилям: "
              f"{[int(v) for v in g.values]} | q5/q1={g.iloc[-1]/max(g.iloc[0],1):.2f} | Спирмен={rho:+.3f}")

print("\n=== ВКЛАД СЕРИИ В КАРТИНУ ===")
bot = m[m["эпоха"] == "3_дно"]
bs = bot[bot["comments_enabled"] == False]
print(f"серия в эпохе «дно»: {len(bs)} из {len(bot)} статей = {len(bs)/len(bot):.1%}")
print(f"её доля в сумме дочитываний эпохи: {bs.reads.sum()/bot.reads.sum():.2%}")
print(f"медиана дочитываний эпохи: сырьё {bot.reads.median():.0f}, "
      f"без серии {bot[bot.comments_enabled != False].reads.median():.0f}")
pre = m[(m["эпоха"] == "1_до_спада")]
print(f"\nотношение до спада / дно по дочитываниям:")
print(f"  сырьё:      {pre.reads.median()/bot.reads.median():.2f}x")
print(f"  без серии:  {pre[pre.comments_enabled != False].reads.median()/bot[bot.comments_enabled != False].reads.median():.2f}x")
