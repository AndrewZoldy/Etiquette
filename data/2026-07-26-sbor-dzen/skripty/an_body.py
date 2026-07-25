"""Разбор внутренних иллюстраций: связь оформления с результатом."""
import glob, json
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 60)

rows = []
for f in sorted(glob.glob("out/marks_body/*.jsonl")):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
b = pd.DataFrame(rows).drop_duplicates("oid")
print("разобрано статей:", len(b))
print("колонки:", list(b.columns))

m = pd.read_pickle("out/full.pkl")
d = m.merge(b, on="oid", how="inner")
d = d[d["shows"].notna()].copy()
print("склеено с метриками:", len(d))

for c in ("оценка_1_5", "доля_с_валентиной", "доля_с_людьми"):
    if c in d.columns:
        d[c] = pd.to_numeric(d[c], errors="coerce")

for col in ("единство_стиля", "источник_набора", "связь_с_текстом", "повторяемость",
            "показывает_ошибку", "эмоции_в_кадре", "разнообразие_сюжетов", "качество"):
    if col in d.columns:
        print(f"\n--- {col} ---")
        print(d[col].value_counts(dropna=False).head(10).to_string())


def tab(col, ep, minn=8):
    x = d[d["эпоха"] == ep]
    if not len(x):
        return None
    bs, br, bc = x["shows"].median(), x["reads"].median(), x["ctr"].median()
    out = []
    for v, g in x.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        out.append({"значение": str(v)[:28], "n": len(g),
                    "мед_показы": int(g["shows"].median()), "инд_показы": round(g["shows"].median()/bs, 2),
                    "мед_дочит": int(g["reads"].median()), "инд_дочит": round(g["reads"].median()/br, 2),
                    "мед_CTR": round(g["ctr"].median(), 4), "инд_CTR": round(g["ctr"].median()/bc, 2),
                    "дочитываемость": round(g["read_rate"].median(), 3)})
    return pd.DataFrame(out).sort_values("инд_дочит", ascending=False)


print("\n" + "=" * 130)
print("ПРИЗНАКИ ОФОРМЛЕНИЯ vs РЕЗУЛЬТАТ")
for col in ("связь_с_текстом", "источник_набора", "единство_стиля", "показывает_ошибку",
            "эмоции_в_кадре", "разнообразие_сюжетов", "качество", "повторяемость"):
    if col not in d.columns:
        continue
    for ep in ("1_до_спада", "3_дно"):
        t = tab(col, ep)
        if t is not None and len(t) > 1:
            print(f"\n--- {col} | {ep} ---")
            print(t.to_string(index=False))

print("\n" + "=" * 130)
print("ОЦЕНКА НАБОРА (1-5) vs результат")
for ep in ("1_до_спада", "3_дно"):
    x = d[d["эпоха"] == ep].dropna(subset=["оценка_1_5"])
    if len(x) < 20:
        continue
    g = x.groupby("оценка_1_5").agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                    мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                                    дочитываемость=("read_rate", "median")).round(4)
    print(f"\n-- {ep} --")
    print(g.to_string())
    rho = x[["оценка_1_5", "reads"]].corr(method="spearman").iloc[0, 1]
    rho2 = x[["оценка_1_5", "read_rate"]].corr(method="spearman").iloc[0, 1]
    print(f"Спирмен оценка×дочитывания = {rho:+.3f}; оценка×дочитываемость = {rho2:+.3f}")

print("\n" + "=" * 130)
print("ЧАСТЫЕ ПРОБЛЕМЫ (по всем разобранным)")
from collections import Counter
cnt = Counter()
for v in d.get("проблемы", pd.Series(dtype=str)).dropna():
    for p in str(v).split(","):
        p = p.strip().lower()
        if p and p != "нет":
            cnt[p] += 1
for k, v in cnt.most_common(20):
    print(f"  {v:4d}  {k}")

print("\n" + "=" * 130)
print("ТИПИЧНЫЕ СЮЖЕТЫ")
cnt2 = Counter()
for v in d.get("типичные_сюжеты", pd.Series(dtype=str)).dropna():
    for p in str(v).split(","):
        p = p.strip().lower()
        if p:
            cnt2[p] += 1
for k, v in cnt2.most_common(25):
    print(f"  {v:4d}  {k}")

d.to_pickle("out/body_joined.pkl")
