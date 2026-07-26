"""Разборы-примеры: чем выстрелившие статьи отличаются от провалившихся, во всех измерениях."""
import glob, json
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 80)

m = pd.read_pickle("out/full.pkl")
tf = pd.read_pickle("out/text_feats.pkl")
dup = [c for c in tf.columns if c != "oid" and c in m.columns]
tf = tf.rename(columns={c: "т_" + c for c in dup})
d = m.merge(tf, on="oid", how="left")
try:
    sh = pd.read_pickle("out/sheets_joined.pkl")[["oid", "обложка_люди", "интрига_набора",
                                                  "связь_общая", "набор_источник"]]
    d = d.merge(sh, on="oid", how="left")
except Exception as e:
    print("полотна недоступны:", e)
d = d[d["shows"].notna()].copy()

bot = d[d["эпоха"] == "3_дно"].copy()
top = bot.nlargest(25, "reads")
low = bot[bot["reads"] > 0].nsmallest(25, "reads")

print("=" * 150)
print("ЭПОХА ДНО: 25 лучших против 25 худших по дочитываниям — сравнение по всем измерениям")
COMP = [("слов", "слов"), ("вопросов", "вопросов"), ("длина_последнего_абзаца", "финал, слов"),
        ("слов_в_предложении_мед", "слов в предложении"), ("подзаголовков", "подзаголовков"),
        ("заграница", "отсылок к загранице"), ("цифры", "цифр в тексте"),
        ("история_случай", "личных историй"), ("предписание", "предписаний"),
        ("мы_совместное", "«мы»"), ("n_images", "картинок"),
        ("brightness", "яркость обложки"), ("ctr", "CTR"), ("read_rate", "дочитываемость"),
        ("comments", "комментариев")]
rows = []
for col, name in COMP:
    if col not in bot.columns:
        continue
    a, b = top[col].median(), low[col].median()
    rows.append({"признак": name, "лучшие_25": round(float(a), 4) if pd.notna(a) else None,
                 "худшие_25": round(float(b), 4) if pd.notna(b) else None,
                 "во_сколько": round(float(a) / float(b), 2) if b and pd.notna(b) and b != 0 else None})
print(pd.DataFrame(rows).to_string(index=False))

for col in ("сцена", "функция", "порог_входа", "фокус", "обложка_люди", "связь_общая"):
    if col not in bot.columns:
        continue
    print(f"\n--- {col} ---")
    t = pd.DataFrame({"лучшие_25": top[col].value_counts(),
                      "худшие_25": low[col].value_counts()}).fillna(0).astype(int)
    print(t.to_string())

print("\n" + "=" * 150)
print("25 ЛУЧШИХ СТАТЕЙ ЭПОХИ ДНО")
print(top[["date", "title_studio", "сцена", "функция", "shows", "reads", "ctr", "comments"]]
      .to_string(index=False))
print("\n" + "=" * 150)
print("25 ХУДШИХ СТАТЕЙ ЭПОХИ ДНО")
print(low[["date", "title_studio", "сцена", "функция", "shows", "opens", "reads", "comments"]]
      .to_string(index=False))

print("\n" + "=" * 150)
print("ПРОВЕРКА УСТОЙЧИВОСТИ: те же признаки на эпохе «до спада» (25 лучших vs 25 худших)")
pre = d[d["эпоха"] == "1_до_спада"].copy()
t2 = pre.nlargest(25, "reads")
l2 = pre[pre["reads"] > 0].nsmallest(25, "reads")
rows = []
for col, name in COMP:
    if col not in pre.columns:
        continue
    a, b = t2[col].median(), l2[col].median()
    rows.append({"признак": name, "лучшие_25": round(float(a), 4) if pd.notna(a) else None,
                 "худшие_25": round(float(b), 4) if pd.notna(b) else None,
                 "во_сколько": round(float(a) / float(b), 2) if b and pd.notna(b) and b != 0 else None})
print(pd.DataFrame(rows).to_string(index=False))
