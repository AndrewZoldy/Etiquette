"""Разбор экспертной разметки всех 620 текстов: приёмы, структура, тон, риски."""
import glob, json, re
from collections import Counter
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

rows = []
for f in sorted(glob.glob("out/marks_text/*.jsonl")):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
t = pd.DataFrame(rows).drop_duplicates("oid")
print("размечено текстов:", len(t))
print("поля:", list(t.columns))

m = pd.read_pickle("out/full.pkl")
d = m.merge(t, on="oid", how="inner", suffixes=("", "_t"))
d = d[d["shows"].notna()].copy()
print("склеено:", len(d), "| по эпохам:", d.groupby("эпоха").size().to_dict())

for c in ("крючок_силы", "категоричность", "узнаваемость", "потенциал_спора", "новизна",
          "риск_хейта", "оценка_1_5", "конкретных_примеров"):
    if c in d.columns:
        d[c] = pd.to_numeric(d[c], errors="coerce")


def tab(col, ep, minn=12):
    x = d[d["эпоха"] == ep]
    bs, br, bc = x["shows"].median(), x["reads"].median(), x["ctr"].median()
    out = []
    for v, g in x.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        out.append({"значение": str(v)[:32], "n": len(g),
                    "мед_показы": int(g["shows"].median()), "инд_показы": round(g["shows"].median()/bs, 2),
                    "мед_дочит": int(g["reads"].median()), "инд_дочит": round(g["reads"].median()/br, 2),
                    "мед_CTR": round(g["ctr"].median(), 4), "инд_CTR": round(g["ctr"].median()/bc, 2),
                    "дочитыв": round(g["read_rate"].median(), 3)})
    return pd.DataFrame(out).sort_values("инд_дочит", ascending=False)


CATS = ["тип_зачина", "структура", "финал_тип", "тон", "позиция_автора", "адресат",
        "норма_ясная", "норма_спорная", "есть_запрет", "ситуация_бытовая",
        "призыв_к_комментарию", "личный_опыт", "заголовок_выполнен", "объект_осуждения",
        "самоповтор", "цифры_в_тексте", "внутренняя_ссылка"]
print("\n" + "=" * 145)
print("КАТЕГОРИАЛЬНЫЕ ПРИЗНАКИ ТЕКСТА vs РЕЗУЛЬТАТ")
for col in CATS:
    if col not in d.columns:
        continue
    for ep in ("1_до_спада", "3_дно"):
        tt = tab(col, ep)
        if len(tt) > 1:
            print(f"\n--- {col} | {ep} ---")
            print(tt.to_string(index=False))

print("\n" + "=" * 145)
print("ЧИСЛОВЫЕ ОЦЕНКИ (эпоха дно)")
bot = d[d["эпоха"] == "3_дно"]
for c in ("крючок_силы", "узнаваемость", "потенциал_спора", "новизна", "категоричность",
          "риск_хейта", "оценка_1_5", "конкретных_примеров"):
    if c not in bot.columns:
        continue
    x = bot.dropna(subset=[c])
    if len(x) < 40:
        continue
    g = x.groupby(c).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                         мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                         дочитыв=("read_rate", "median")).round(4)
    rho = x[[c, "reads"]].corr(method="spearman").iloc[0, 1]
    print(f"\n--- {c} (Спирмен с дочитываниями {rho:+.3f}) ---")
    print(g.to_string())

print("\n" + "=" * 145)
print("КОНТРОЛЬ НА ТЕМУ: ключевые признаки внутри «стол_еда», эпоха дно")
sf = bot[bot["сцена"] == "стол_еда"]
print(f"n={len(sf)}")
for c in ("норма_спорная", "тип_зачина", "финал_тип", "личный_опыт", "потенциал_спора",
          "узнаваемость"):
    if c not in sf.columns:
        continue
    g = sf.groupby(c, observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                         мед_дочит=("reads", "median"),
                                         мед_CTR=("ctr", "median")).round(4)
    g = g[g["n"] >= 5]
    if len(g) > 1:
        print(f"\n--- {c} ---")
        print(g.to_string())

print("\n" + "=" * 145)
print("НАРРАТИВНЫЕ ПРИЁМЫ: частота и связь с результатом (эпоха дно)")
def split_list(v):
    if not isinstance(v, str):
        return []
    return [x.strip().lower() for x in re.split(r"[,;]", v) if x.strip() and x.strip().lower() != "нет"]

allp = Counter()
for v in d.get("нарративные_приёмы", pd.Series(dtype=str)).dropna():
    allp.update(split_list(v))
print("\nчастота по всем 620 статьям:")
for k, v in allp.most_common(25):
    print(f"  {v:4d}  {k}")

print("\nсвязь с результатом (эпоха дно, приёмы встречающиеся >=12 раз):")
res = []
bb = bot.copy()
bb["_p"] = bb.get("нарративные_приёмы", pd.Series(dtype=str)).map(split_list)
base_r = bb["reads"].median()
base_c = bb["ctr"].median()
for p, cnt in allp.most_common(40):
    has = bb[bb["_p"].map(lambda L: p in L)]
    if len(has) < 12:
        continue
    res.append({"приём": p, "n": len(has),
                "мед_дочит": int(has["reads"].median()),
                "инд_дочит": round(has["reads"].median()/base_r, 2),
                "мед_CTR": round(has["ctr"].median(), 4),
                "инд_CTR": round(has["ctr"].median()/base_c, 2)})
print(pd.DataFrame(res).sort_values("инд_дочит", ascending=False).to_string(index=False))

print("\n" + "=" * 145)
print("РЕЧЕВЫЕ ОБОРОТЫ: самые частые (по всем статьям)")
ph = Counter()
for v in d.get("речевые_обороты", pd.Series(dtype=object)).dropna():
    if isinstance(v, list):
        items = v
    else:
        items = re.split(r"[;|]", str(v))
    for x in items:
        x = str(x).strip().strip('"«»').lower()
        if 8 < len(x) < 90:
            ph[x] += 1
for k, v in ph.most_common(30):
    print(f"  {v:3d}  {k}")

d.to_pickle("out/texts_joined.pkl")
