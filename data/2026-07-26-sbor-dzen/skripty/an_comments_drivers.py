"""Что заставляет комментировать: сравнение при фиксированном числе дочитываний
(чтобы не делить на общий знаменатель)."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna() & (m["reads"] > 0)].copy()

# полосы по дочитываниям — внутри полосы сравниваем АБСОЛЮТНОЕ число комментариев
m["полоса"] = pd.qcut(m["reads"], 5, labels=["1 мало", "2", "3", "4", "5 много"])
print("=" * 140)
print("КОНТРОЛЬ ЗНАМЕНАТЕЛЯ: полосы по дочитываниям")
print(m.groupby("полоса", observed=True).agg(n=("reads", "size"), дочит=("reads", "median"),
                                             комм=("comments", "median"),
                                             лайки=("likes", "median")).round(0).to_string())


def within(col, minn=12):
    """Медиана комментариев по значению признака ВНУТРИ каждой полосы дочитываний."""
    out = []
    for v, g in m.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        row = {"значение": str(v)[:30], "n": len(g)}
        for b, gb in g.groupby("полоса", observed=True):
            if len(gb) >= 5:
                base = m[(m["полоса"] == b)]["comments"].median()
                row[str(b)] = round(gb["comments"].median() / max(base, 1), 2)
        out.append(row)
    return pd.DataFrame(out)


print("\n" + "=" * 140)
print("ИНДЕКС ЧИСЛА КОММЕНТАРИЕВ (к медиане своей полосы дочитываний)")
print("значение > 1 = обсуждают активнее, чем типичная статья с таким же числом читателей\n")
for col in ("сцена", "функция", "фокус", "объект_осуждения", "спорность", "порог_входа"):
    if col not in m.columns:
        continue
    t = within(col)
    if len(t) > 1:
        print(f"--- {col} ---")
        print(t.to_string(index=False))
        print()

# то же по разметке текстов, где она есть
try:
    tx = pd.read_pickle("out/texts_joined.pkl")
    tx = tx[tx["reads"] > 0].copy()
    tx["полоса"] = pd.qcut(tx["reads"], 4, labels=["1", "2", "3", "4"])
    print("=" * 140)
    print("ТО ЖЕ ПО ЭКСПЕРТНОЙ РАЗМЕТКЕ ТЕКСТОВ (где размечено)")
    for col in ("потенциал_спора", "узнаваемость", "норма_спорная", "объект_осуждения_t",
                "тон", "позиция_автора", "категоричность", "призыв_к_комментарию", "личный_опыт"):
        if col not in tx.columns:
            continue
        out = []
        for v, g in tx.groupby(col, dropna=False, observed=True):
            if len(g) < 12:
                continue
            row = {"значение": str(v)[:28], "n": len(g)}
            for b, gb in g.groupby("полоса", observed=True):
                if len(gb) >= 4:
                    base = tx[tx["полоса"] == b]["comments"].median()
                    row[str(b)] = round(gb["comments"].median() / max(base, 1), 2)
            out.append(row)
        o = pd.DataFrame(out)
        if len(o) > 1:
            print(f"--- {col} ---")
            print(o.to_string(index=False))
            print()
except Exception as e:
    print("разметка текстов недоступна:", e)

print("=" * 140)
print("САМЫЕ ОБСУЖДАЕМЫЕ СТАТЬИ ОТНОСИТЕЛЬНО ЧИСЛА ЧИТАТЕЛЕЙ (эпоха дно, дочитываний > 500)")
b = m[(m["эпоха"] == "3_дно") & (m["reads"] > 500)].copy()
b["комм_на_1000_дочит"] = (b["comments"] / b["reads"] * 1000).round(1)
print(b.nlargest(15, "комм_на_1000_дочит")[
    ["date", "title_studio", "сцена", "функция", "reads", "comments", "комм_на_1000_дочит"]
].to_string(index=False))
print("\nсамые НЕобсуждаемые:")
print(b.nsmallest(10, "комм_на_1000_дочит")[
    ["date", "title_studio", "сцена", "функция", "reads", "comments", "комм_на_1000_дочит"]
].to_string(index=False))
