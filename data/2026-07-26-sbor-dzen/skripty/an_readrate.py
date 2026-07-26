"""Что предсказывает ДОЧИТЫВАЕМОСТЬ (долю дошедших до конца) — целевая метрика задачи.
Считаем по всему каналу, без служебной рубрики вт/чт, и отдельно проверяем подзаголовки."""
import glob, json, os
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna() & m["read_rate"].notna()].copy()
tf = pd.read_pickle("out/text_feats.pkl")
dup = [c for c in tf.columns if c != "oid" and c in m.columns]
tf = tf.rename(columns={c: "т_" + c for c in dup})
d = m.merge(tf, on="oid", how="left")
clean = d[d["comments_enabled"] == True].copy()
print(f"всего статей {len(d)}, без служебной рубрики {len(clean)}")

print("\n" + "=" * 130)
print("1. КОРРЕЛЯЦИИ С ДОЧИТЫВАЕМОСТЬЮ (Спирмен), все статьи без служебной рубрики")
KEY = ["n_words", "n_paragraphs", "слов_в_абзаце_мед", "слов_в_предложении_мед",
       "доля_коротких_предложений", "доля_длинных_предложений", "подзаголовков",
       "вопросов", "т_обращение_вы", "обращение_вы_на100слов", "цифры", "цифры_на100слов",
       "n_images", "прямая_речь", "история_случай", "заграница", "предписание",
       "мы_совместное", "лексразнообразие", "многоточий", "тире", "восклицаний",
       "длина_первого_абзаца", "длина_последнего_абзаца", "time_to_read_s"]
rows = []
for c in KEY:
    if c not in clean.columns:
        continue
    x = clean.dropna(subset=[c, "read_rate"])
    if len(x) < 60 or x[c].nunique() < 3:
        continue
    rows.append({"признак": c, "n": len(x),
                 "дочитываемость": round(x[[c, "read_rate"]].corr(method="spearman").iloc[0, 1], 3),
                 "дочитывания": round(x[[c, "reads"]].corr(method="spearman").iloc[0, 1], 3)})
t = pd.DataFrame(rows).sort_values("дочитываемость")
print(t.to_string(index=False))

print("\n" + "=" * 130)
print("2. ПОДЗАГОЛОВКИ: проверка гипотезы на данных канала")
print("\nраспределение числа подзаголовков по всем статьям:")
print(clean["подзаголовков"].value_counts().sort_index().head(12).to_string())
c0 = (clean["подзаголовков"] == 0).sum()
print(f"\nстатей БЕЗ подзаголовков: {c0} из {len(clean)} = {c0/len(clean):.1%}")
sub = clean[clean["подзаголовков"] > 0]
print(f"статей С подзаголовками:  {len(sub)}")
if len(sub) >= 10:
    print("\nсравнение:")
    g = clean.assign(есть=np.where(clean["подзаголовков"] > 0, "есть подзаголовки", "нет")) \
             .groupby("есть").agg(n=("read_rate", "size"),
                                  дочитываемость=("read_rate", "median"),
                                  мед_дочит=("reads", "median"),
                                  мед_слов=("n_words", "median"),
                                  мед_CTR=("ctr", "median")).round(4)
    print(g.to_string())
    print("\nтолько длинные статьи (больше 900 слов):")
    L = clean[clean["n_words"] > 900]
    if len(L) >= 10:
        g2 = L.assign(есть=np.where(L["подзаголовков"] > 0, "есть", "нет")) \
              .groupby("есть").agg(n=("read_rate", "size"),
                                   дочитываемость=("read_rate", "median"),
                                   мед_слов=("n_words", "median")).round(4)
        print(g2.to_string())
    print("\nстатьи с подзаголовками — список:")
    print(sub[["date", "title_studio", "подзаголовков", "n_words", "read_rate", "reads"]]
          .sort_values("подзаголовков", ascending=False).head(15).round(3).to_string(index=False))

print("\n" + "=" * 130)
print("3. ГЛАВНЫЕ РЫЧАГИ ДОЧИТЫВАЕМОСТИ по группам")
for col, bins, labs in (
    ("слов_в_предложении_мед", [0, 10, 13, 16, 100], ["до 10", "10-13", "13-16", "больше 16"]),
    ("слов_в_абзаце_мед", [0, 25, 40, 60, 500], ["до 25", "25-40", "40-60", "больше 60"]),
    ("n_words", [0, 450, 600, 900, 1500, 9999], ["до 450", "450-600", "600-900", "900-1500", "больше 1500"]),
    ("доля_коротких_предложений", [-0.01, 0.12, 0.2, 0.3, 1.01], ["до 12%", "12-20%", "20-30%", "больше 30%"]),
    ("вопросов", [-1, 0, 2, 5, 100], ["нет", "1-2", "3-5", "6+"]),
    ("цифры_на100слов", [-0.01, 0.3, 1.0, 2.0, 100], ["почти нет", "0,3-1", "1-2", "больше 2"]),
    ("n_images", [0, 3, 5, 8, 50], ["1-3", "4-5", "6-8", "9+"]),
):
    if col not in clean.columns:
        continue
    x = clean.dropna(subset=[col]).copy()
    x["g"] = pd.cut(x[col], bins, labels=labs)
    g = x.groupby("g", observed=True).agg(n=("read_rate", "size"), знач=(col, "median"),
                                          дочитываемость=("read_rate", "median"),
                                          мед_дочит=("reads", "median")).round(4)
    print(f"\n--- {col} ---")
    print(g.to_string())

print("\n" + "=" * 130)
print("4. ГДЕ СЕЙЧАС РУБРИКА И ЧЕРНОВИК по каждому рычагу")
r = d[d["title_studio"].astype(str).str.contains("Светская жизнь Петербурга", na=False)]
draft = {"n_words": 2517, "n_paragraphs": 42, "подзаголовков": 0}
print(f"{'признак':30s} {'рубрика':>10s} {'черновик':>10s} {'лучшая группа канала':>24s}")
BEST = {"слов_в_предложении_мед": "10-13", "слов_в_абзаце_мед": "до 25", "n_words": "до 450",
        "доля_коротких_предложений": "больше 30%", "вопросов": "3-5", "цифры_на100слов": "почти нет",
        "подзаголовков": "больше 0", "n_images": "4-5"}
for k, best in BEST.items():
    rv = r[k].median() if k in r.columns else None
    dv = draft.get(k, "—")
    print(f"{k:30s} {str(round(rv,2) if rv is not None else '—'):>10s} {str(dv):>10s} {best:>24s}")
