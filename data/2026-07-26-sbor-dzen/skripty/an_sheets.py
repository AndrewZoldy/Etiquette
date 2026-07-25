"""Полный (нестратифицированный) разбор иллюстративных наборов по 612 статьям."""
import glob, json
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

rows = []
for f in sorted(glob.glob("out/marks_sheets/*.jsonl")):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
s = pd.DataFrame(rows).drop_duplicates("oid")
print("разобрано наборов:", len(s))

m = pd.read_pickle("out/full.pkl")
d = m.merge(s, on="oid", how="inner")
d = d[d["shows"].notna()].copy()
print("склеено с метриками:", len(d))
print(d.groupby("эпоха").size().to_string())

for c in ("оценка_1_5", "кадров_по_месту", "кадров_мимо", "кадров_с_валентиной",
          "кадров_с_людьми", "кадров_предметных", "интрига_набора", "картинок"):
    if c in d.columns:
        d[c] = pd.to_numeric(d[c], errors="coerce")
d["доля_мимо"] = d["кадров_мимо"] / d["картинок"].replace(0, np.nan)

print("\n--- распределения ---")
for c in ("связь_общая", "набор_источник", "набор_единый", "обложка_люди",
          "обложка_связь_с_заголовком", "показана_ошибка", "эмоции", "разнообразие", "качество"):
    if c in d.columns:
        print(f"\n{c}:")
        print(d[c].value_counts(dropna=False).head(9).to_string())
print("\nдоля кадров «мимо»: медиана %.2f, среднее %.2f" %
      (d["доля_мимо"].median(), d["доля_мимо"].mean()))
print("оценка набора: медиана %.1f, среднее %.2f" % (d["оценка_1_5"].median(), d["оценка_1_5"].mean()))


def tab(col, ep, minn=10):
    x = d[d["эпоха"] == ep]
    bs, br, bc = x["shows"].median(), x["reads"].median(), x["ctr"].median()
    out = []
    for v, g in x.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        out.append({"значение": str(v)[:30], "n": len(g),
                    "мед_показы": int(g["shows"].median()), "инд_показы": round(g["shows"].median()/bs, 2),
                    "мед_дочит": int(g["reads"].median()), "инд_дочит": round(g["reads"].median()/br, 2),
                    "мед_CTR": round(g["ctr"].median(), 4), "инд_CTR": round(g["ctr"].median()/bc, 2),
                    "дочитыв": round(g["read_rate"].median(), 3)})
    return pd.DataFrame(out).sort_values("инд_дочит", ascending=False)


print("\n" + "=" * 140)
print("ПРИЗНАКИ НАБОРА vs РЕЗУЛЬТАТ (полная выборка)")
for col in ("обложка_люди", "обложка_связь_с_заголовком", "связь_общая", "набор_источник",
            "набор_единый", "показана_ошибка", "эмоции", "разнообразие", "качество"):
    if col not in d.columns:
        continue
    for ep in ("1_до_спада", "3_дно"):
        t = tab(col, ep)
        if len(t) > 1:
            print(f"\n--- {col} | {ep} ---")
            print(t.to_string(index=False))

print("\n" + "=" * 140)
print("ЧИСЛОВЫЕ: доля «мимо», оценка набора, интрига — по группам (эпоха дно)")
bot = d[d["эпоха"] == "3_дно"].copy()
for c, bins, labs in (("доля_мимо", [-0.01, 0.001, 0.25, 0.5, 1.01],
                       ["нет промахов", "до 25%", "25-50%", "больше 50%"]),
                      ("оценка_1_5", [0, 2.5, 3.5, 5], ["1-2", "3", "4-5"]),
                      ("интрига_набора", [-1, 0, 1, 3], ["0", "1", "2-3"]),
                      ("картинок", [0, 3, 5, 20], ["1-3", "4-5", "6+"])):
    x = bot.dropna(subset=[c]).copy()
    x["g"] = pd.cut(x[c], bins, labels=labs)
    g = x.groupby("g", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                          мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                                          дочитыв=("read_rate", "median")).round(4)
    print(f"\n--- {c} ---")
    print(g.to_string())

print("\n" + "=" * 140)
print("КОНТРОЛЬ НА ТЕМУ: внутри «стол_еда», эпоха дно")
sf = bot[bot["сцена"] == "стол_еда"]
for c in ("связь_общая", "показана_ошибка", "обложка_люди"):
    if c in sf.columns:
        g = sf.groupby(c, observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                             мед_дочит=("reads", "median"),
                                             мед_CTR=("ctr", "median")).round(4)
        print(f"\n--- {c} ---")
        print(g[g["n"] >= 5].to_string())

print("\n" + "=" * 140)
print("ЧАСТЫЕ ПРОБЛЕМЫ")
from collections import Counter
cnt = Counter()
for v in d.get("проблемы", pd.Series(dtype=str)).dropna():
    for p in str(v).split(","):
        p = p.strip().lower()
        if p and p not in ("нет", "не определить"):
            cnt[p] += 1
for k, v in cnt.most_common(22):
    print(f"  {v:4d}  {k}")

d.to_pickle("out/sheets_joined.pkl")
