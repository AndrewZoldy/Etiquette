"""Машинные языковые признаки текстов и заголовков против результата, по эпохам."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

m = pd.read_pickle("out/full.pkl")
t = pd.read_pickle("out/text_feats.pkl")
# развести одноимённые колонки: у разметки заголовков и у машинных признаков есть совпадения
dup = [c for c in t.columns if c != "oid" and c in m.columns]
t = t.rename(columns={c: "т_" + c for c in dup})
d = m.merge(t, on="oid", how="inner")
d = d[d["shows"].notna()].copy()
print("статей с текстом и метриками:", len(d))
print(d.groupby("эпоха").size().to_string())

TARGETS = ["reads", "ctr", "read_rate"]
NUM = [c for c in t.columns if c != "oid" and pd.api.types.is_numeric_dtype(t[c])]

print("\n" + "=" * 150)
print("КОРРЕЛЯЦИИ (Спирмен) языковых признаков с результатом, отдельно по эпохам")
rows = []
for c in NUM:
    r = {"признак": c}
    for ep in ("1_до_спада", "3_дно"):
        x = d[d["эпоха"] == ep].dropna(subset=[c])
        if len(x) < 40 or x[c].nunique() < 3:
            r[f"{ep}_дочит"] = np.nan
            r[f"{ep}_CTR"] = np.nan
            continue
        r[f"{ep}_дочит"] = round(x[[c, "reads"]].corr(method="spearman").iloc[0, 1], 3)
        r[f"{ep}_CTR"] = round(x[[c, "ctr"]].corr(method="spearman").iloc[0, 1], 3)
    rows.append(r)
cor = pd.DataFrame(rows).dropna(subset=["3_дно_дочит"])
print("\n--- ТОП-20 положительных на дне (по дочитываниям) ---")
print(cor.nlargest(20, "3_дно_дочит").to_string(index=False))
print("\n--- ТОП-20 отрицательных на дне ---")
print(cor.nsmallest(20, "3_дно_дочит").to_string(index=False))
print("\n--- ТОП-15 по CTR на дне ---")
print(cor.nlargest(15, "3_дно_CTR").to_string(index=False))

print("\n" + "=" * 150)
print("БИНАРНЫЕ ПРИЗНАКИ ЗАГОЛОВКА: медианы по группам")
BIN = ["загл_вопрос", "загл_цифра", "загл_двоеточие", "загл_кавычки", "загл_можно_ли",
       "загл_как", "загл_почему", "загл_что", "загл_когда", "загл_отрицание",
       "финал_вопрос", "старт_вопрос"]
for ep in ("1_до_спада", "3_дно"):
    x = d[d["эпоха"] == ep]
    base_r, base_c = x["reads"].median(), x["ctr"].median()
    out = []
    for c in BIN:
        for v in (1, 0):
            g = x[x[c] == v]
            if len(g) < 10:
                continue
            out.append({"признак": c, "значение": v, "n": len(g),
                        "мед_дочит": int(g["reads"].median()),
                        "инд_дочит": round(g["reads"].median() / base_r, 2),
                        "мед_CTR": round(g["ctr"].median(), 4),
                        "инд_CTR": round(g["ctr"].median() / base_c, 2)})
    o = pd.DataFrame(out)
    piv = o[o["значение"] == 1].merge(o[o["значение"] == 0], on="признак",
                                      suffixes=("_есть", "_нет"))
    piv["во_сколько_раз"] = (piv["мед_дочит_есть"] / piv["мед_дочит_нет"].replace(0, np.nan)).round(2)
    print(f"\n--- {ep} ---")
    print(piv[["признак", "n_есть", "мед_дочит_есть", "инд_дочит_есть", "инд_CTR_есть",
               "n_нет", "мед_дочит_нет", "инд_дочит_нет", "во_сколько_раз"]]
          .sort_values("во_сколько_раз", ascending=False).to_string(index=False))

print("\n" + "=" * 150)
print("ДЛИНА ЗАГОЛОВКА и ДЛИНА ТЕКСТА — по квартилям, эпоха «дно»")
bot = d[d["эпоха"] == "3_дно"]
for c in ("загл_слов", "слов", "абзацев", "слов_в_предложении_мед", "длина_первого_абзаца",
          "доля_коротких_предложений", "лексразнообразие", "подзаголовков"):
    x = bot.dropna(subset=[c])
    if x[c].nunique() < 4:
        continue
    x = x.copy()
    try:
        x["q"] = pd.qcut(x[c], 4, labels=["1 мало", "2", "3", "4 много"], duplicates="drop")
    except Exception:
        continue
    g = x.groupby("q", observed=True).agg(n=("shows", "size"), знач=(c, "median"),
                                          мед_дочит=("reads", "median"),
                                          мед_CTR=("ctr", "median"),
                                          дочитываемость=("read_rate", "median")).round(4)
    print(f"\n--- {c} ---")
    print(g.to_string())

d.to_pickle("out/lang_joined.pkl")
