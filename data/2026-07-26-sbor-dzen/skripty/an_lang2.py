"""Контроль языковых признаков на подмену темой и функцией статьи."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

d = pd.read_pickle("out/lang_joined.pkl")
bot = d[d["эпоха"] == "3_дно"].copy()
pre = d[d["эпоха"] == "1_до_спада"].copy()

KEY = ["вопросов", "длина_последнего_абзаца", "заграница_на100слов",
       "доля_коротких_предложений", "слов_в_предложении_мед", "мы_совместное_на100слов",
       "предписание_на100слов", "подзаголовков", "цифры_на100слов", "история_случай_на100слов"]

print("=" * 150)
print("1. ЧАСТНАЯ КОРРЕЛЯЦИЯ: связь признака с дочитываниями ВНУТРИ каждой функции (эпоха дно)")
rows = []
for c in KEY:
    r = {"признак": c, "общая": round(bot[[c, "reads"]].corr(method="spearman").iloc[0, 1], 3)}
    for f, g in bot.groupby("функция"):
        if len(g) >= 25 and g[c].nunique() > 3:
            r[str(f)[:22]] = round(g[[c, "reads"]].corr(method="spearman").iloc[0, 1], 3)
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

print("\n" + "=" * 150)
print("2. ТО ЖЕ ВНУТРИ КРУПНЫХ СЦЕН (эпоха дно)")
rows = []
for c in KEY:
    r = {"признак": c}
    for s, g in bot.groupby("сцена"):
        if len(g) >= 25 and g[c].nunique() > 3:
            r[str(s)[:20]] = round(g[[c, "reads"]].corr(method="spearman").iloc[0, 1], 3)
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False))

print("\n" + "=" * 150)
print("3. ФИНАЛЬНЫЙ АБЗАЦ: короткий финал против длинного (эпоха дно)")
b = bot.dropna(subset=["длина_последнего_абзаца"]).copy()
b["финал"] = pd.cut(b["длина_последнего_абзаца"], [-1, 15, 30, 60, 10000],
                    labels=["до 15 слов", "16-30", "31-60", "больше 60"])
g = b.groupby("финал", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                          мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                                          дочитываемость=("read_rate", "median")).round(4)
print(g.to_string())
print("\nвнутри темы «стол и еда»:")
s = b[b["сцена"] == "стол_еда"]
print(s.groupby("финал", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                            мед_дочит=("reads", "median"),
                                            мед_CTR=("ctr", "median")).round(4).to_string())
print("\nвнутри функции «польза»:")
s = b[b["функция"] == "польза"]
print(s.groupby("финал", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                            мед_дочит=("reads", "median"),
                                            мед_CTR=("ctr", "median")).round(4).to_string())

print("\n" + "=" * 150)
print("4. ВОПРОСЫ В ТЕКСТЕ (эпоха дно)")
b = bot.copy()
b["вопр"] = pd.cut(b["вопросов"], [-1, 0, 2, 5, 100], labels=["нет", "1-2", "3-5", "6+"])
print(b.groupby("вопр", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                           мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                                           дочитываемость=("read_rate", "median")).round(4).to_string())
print("\nвнутри функции «польза» (n=114):")
s = b[b["функция"] == "польза"]
print(s.groupby("вопр", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                           мед_дочит=("reads", "median"),
                                           мед_CTR=("ctr", "median")).round(4).to_string())

print("\n" + "=" * 150)
print("5. ЗАГРАНИЦА (в Японии, во Франции...) — эпоха дно")
b = bot.copy()
b["згр"] = np.where(b["заграница"] > 0, "есть отсылка к загранице", "нет")
print(b.groupby("згр").agg(n=("shows", "size"), мед_показы=("shows", "median"),
                           мед_дочит=("reads", "median"), мед_CTR=("ctr", "median")).round(4).to_string())
print("\nраспределение по сценам:")
print(pd.crosstab(b["згр"], b["сцена"]).to_string())

print("\n" + "=" * 150)
print("6. ДЛИНА ПРЕДЛОЖЕНИЯ (эпоха дно)")
b = bot.copy()
b["дл"] = pd.cut(b["слов_в_предложении_мед"], [0, 10, 13, 16, 100],
                 labels=["до 10 слов", "10-13", "13-16", "больше 16"])
print(b.groupby("дл", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                         мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                                         дочитываемость=("read_rate", "median")).round(4).to_string())
