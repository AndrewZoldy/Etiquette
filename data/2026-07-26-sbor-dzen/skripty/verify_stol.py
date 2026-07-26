"""Своя проверка: доля и индекс темы «стол и еда» и функций, с контролем на серию."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 220)
m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna()]
clean = m[m["comments_enabled"] == True]

print("=== ДОЛЯ ТЕМЫ «стол_еда» ===")
for lbl, d in (("сырьё", m), ("без серии", clean)):
    a = d[d["эпоха"] == "1_до_спада"]
    b = d[d["эпоха"] == "3_дно"]
    pa = (a["сцена"] == "стол_еда").mean()
    pb = (b["сцена"] == "стол_еда").mean()
    print(f"{lbl:10s} до спада {pa:.1%} (n={len(a)}) -> дно {pb:.1%} (n={len(b)})")

print("\n=== ИНДЕКС «стол_еда» к медиане своей эпохи, по дочитываниям ===")
for lbl, d in (("сырьё", m), ("без серии", clean)):
    for ep in ("1_до_спада", "3_дно"):
        x = d[d["эпоха"] == ep]
        s = x[x["сцена"] == "стол_еда"]
        if len(s) >= 10:
            print(f"{lbl:10s} {ep:12s} n={len(s):3d} индекс={s['reads'].median()/x['reads'].median():.2f}"
                  f"  (медиана темы {s['reads'].median():.0f}, эпохи {x['reads'].median():.0f})")

print("\n=== ВНУТРИТЕМНОЕ ПАДЕНИЕ vs КАНАЛЬНОЕ (без серии) ===")
a = clean[clean["эпоха"] == "1_до_спада"]
b = clean[clean["эпоха"] == "3_дно"]
sa, sb = a[a["сцена"] == "стол_еда"], b[b["сцена"] == "стол_еда"]
print(f"канал:    {a['reads'].median():.0f} -> {b['reads'].median():.0f} = {a['reads'].median()/b['reads'].median():.2f}x")
print(f"стол_еда: {sa['reads'].median():.0f} -> {sb['reads'].median():.0f} = {sa['reads'].median()/sb['reads'].median():.2f}x  (n={len(sa)} -> {len(sb)})")

print("\n=== ФУНКЦИИ: доли и индексы без серии ===")
for ep in ("1_до_спада", "3_дно"):
    x = clean[clean["эпоха"] == ep]
    print(f"\n-- {ep} (n={len(x)}), медиана эпохи {x['reads'].median():.0f}")
    for f, g in x.groupby("функция"):
        if len(g) >= 10:
            print(f"   {f:26s} доля {len(g)/len(x):6.1%} n={len(g):3d} "
                  f"индекс={g['reads'].median()/x['reads'].median():.2f}")

print("\n=== СЦЕНЫ: доли до и после, без серии ===")
a2 = clean[clean["эпоха"] == "1_до_спада"]["сцена"].value_counts(normalize=True)
b2 = clean[clean["эпоха"] == "3_дно"]["сцена"].value_counts(normalize=True)
t = pd.DataFrame({"до_спада": (a2 * 100).round(1), "дно": (b2 * 100).round(1)}).fillna(0)
t["изменение_пп"] = (t["дно"] - t["до_спада"]).round(1)
print(t.sort_values("изменение_пп", ascending=False).to_string())
