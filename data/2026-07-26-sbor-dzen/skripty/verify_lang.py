"""Проверка языковых находок с контролем на серию вт/чт без комментариев."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)

d = pd.read_pickle("out/lang_joined.pkl")
d = d[d["shows"].notna()].copy()
d["серия"] = np.where(d["comments_enabled"] == False, "серия вт/чт", "обычные")
bot = d[d["эпоха"] == "3_дно"]

print("=" * 140)
print("СОСТАВ: попадают ли слабые языковые признаки в серию?")
print(bot.groupby("серия").agg(
    n=("shows", "size"),
    финал_слов=("длина_последнего_абзаца", "median"),
    вопросов=("вопросов", "median"),
    слов_в_предл=("слов_в_предложении_мед", "median"),
    заграница=("заграница", "median"),
    мед_дочит=("reads", "median"),
    мед_CTR=("ctr", "median")).round(3).to_string())

print("\n" + "=" * 140)
print("ПРИЗНАК 1. ФИНАЛЬНЫЙ АБЗАЦ — отдельно в серии и вне серии (эпоха дно)")
b = bot.dropna(subset=["длина_последнего_абзаца"]).copy()
b["финал"] = pd.cut(b["длина_последнего_абзаца"], [-1, 15, 30, 60, 10000],
                    labels=["до 15", "16-30", "31-60", "больше 60"])
for grp, x in b.groupby("серия"):
    g = x.groupby("финал", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                              мед_дочит=("reads", "median"),
                                              мед_CTR=("ctr", "median")).round(4)
    print(f"\n--- {grp} (n={len(x)}) ---")
    print(g.to_string())
    xx = x.dropna(subset=["длина_последнего_абзаца", "reads"])
    if len(xx) > 25:
        print(f"Спирмен финал×дочитывания = "
              f"{xx[['длина_последнего_абзаца','reads']].corr(method='spearman').iloc[0,1]:+.3f}")

print("\n" + "=" * 140)
print("ПРИЗНАК 2. ВОПРОСЫ В ТЕКСТЕ — отдельно в серии и вне серии")
b = bot.copy()
b["вопр"] = pd.cut(b["вопросов"], [-1, 0, 2, 5, 100], labels=["нет", "1-2", "3-5", "6+"])
for grp, x in b.groupby("серия"):
    g = x.groupby("вопр", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                             мед_дочит=("reads", "median"),
                                             мед_CTR=("ctr", "median")).round(4)
    print(f"\n--- {grp} (n={len(x)}) ---")
    print(g.to_string())
    xx = x.dropna(subset=["вопросов", "reads"])
    if len(xx) > 25:
        print(f"Спирмен вопросы×дочитывания = "
              f"{xx[['вопросов','reads']].corr(method='spearman').iloc[0,1]:+.3f}")

print("\n" + "=" * 140)
print("ПРИЗНАК 3. ДЛИНА ПРЕДЛОЖЕНИЯ — вне серии")
x = bot[bot["серия"] == "обычные"].copy()
x["дл"] = pd.cut(x["слов_в_предложении_мед"], [0, 10, 13, 16, 100],
                 labels=["до 10", "10-13", "13-16", "больше 16"])
print(x.groupby("дл", observed=True).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                         мед_дочит=("reads", "median"), мед_CTR=("ctr", "median"),
                                         дочитываемость=("read_rate", "median")).round(4).to_string())

print("\n" + "=" * 140)
print("ПРИЗНАК 4. ЗАГРАНИЦА — вне серии")
x = bot[bot["серия"] == "обычные"].copy()
x["згр"] = np.where(x["заграница"] > 0, "есть", "нет")
print(x.groupby("згр").agg(n=("shows", "size"), мед_показы=("shows", "median"),
                           мед_дочит=("reads", "median"), мед_CTR=("ctr", "median")).round(4).to_string())

print("\n" + "=" * 140)
print("ВСЕ КОРРЕЛЯЦИИ ЗАНОВО, ТОЛЬКО ВНЕ СЕРИИ (эпоха дно)")
x = bot[bot["серия"] == "обычные"]
KEY = ["вопросов", "длина_последнего_абзаца", "заграница_на100слов", "доля_коротких_предложений",
       "слов_в_предложении_мед", "мы_совместное_на100слов", "предписание_на100слов",
       "подзаголовков", "цифры_на100слов", "история_случай_на100слов", "слов",
       "т_обращение_вы", "этикет_слово_на100слов"]
rows = []
for c in KEY:
    if c not in x.columns:
        continue
    xx = x.dropna(subset=[c, "reads"])
    if len(xx) < 40:
        continue
    rows.append({"признак": c, "n": len(xx),
                 "дочит_вне_серии": round(xx[[c, "reads"]].corr(method="spearman").iloc[0, 1], 3),
                 "CTR_вне_серии": round(xx[[c, "ctr"]].corr(method="spearman").iloc[0, 1], 3),
                 "дочит_сырьё": round(bot.dropna(subset=[c, "reads"])[[c, "reads"]]
                                     .corr(method="spearman").iloc[0, 1], 3)})
print(pd.DataFrame(rows).to_string(index=False))
