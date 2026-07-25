"""Обогащённая таблица: Студия + карточки + тексты + разметка заголовков + метрики обложек."""
import glob, json, os, re, unicodedata
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 60)
DATA = r"d:\Work\Etiquette\Etiquette\data"


def nt(s):
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKC", s).lower().replace("ё", "е")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


m = pd.read_pickle("out/master_raw.pkl")
m = m[m["oid"].notna()].copy()
m["date"] = pd.to_datetime(m["date"])
m["ym"] = m["date"].dt.to_period("M")
m["key"] = m["date"].dt.strftime("%Y-%m-%d") + "|" + m["title_studio"].map(nt)

# ---------- разметка заголовков от прошлого агента ----------
mk = pd.concat([pd.read_excel(f) for f in
                sorted(glob.glob(os.path.join(DATA, "drive-download-*", "*статьи с разметкой*.xlsx")))],
               ignore_index=True)
mk["дата"] = pd.to_datetime(mk["дата"])
mk["key"] = mk["дата"].dt.strftime("%Y-%m-%d") + "|" + mk["заголовок"].map(nt)
MKCOLS = ["сцена", "функция", "порог_входа", "фокус", "объект_осуждения", "цифра_в_заголовке",
          "негативная_рамка", "вопрос", "обращение_вы", "конкретный_якорь", "спорность",
          "серийная_рубрика", "уверенность_разметки"]
mk2 = mk[["key", "id"] + MKCOLS].drop_duplicates("key")
before = len(m)
m = m.merge(mk2, on="key", how="left")
print(f"разметка подключена к {m['сцена'].notna().sum()} из {before} статей")

# ---------- метрики обложек ----------
cs = json.load(open("out/cover_stats.json", encoding="utf-8"))
cst = pd.DataFrame.from_dict(cs, orient="index").rename_axis("oid").reset_index()
m = m.merge(cst, on="oid", how="left")

# ---------- эпохи ----------
def epoch(ym):
    if ym <= pd.Period("2025-07"):
        return "1_до_спада"
    if ym <= pd.Period("2025-10"):
        return "2_склон"
    return "3_дно"


m["эпоха"] = m["ym"].map(epoch)
m["age_days"] = (pd.Timestamp("2026-07-25") - m["date"]).dt.days
print(m.groupby("эпоха").agg(n=("oid", "size"), мед_показы=("shows", "median"),
                             мед_дочит=("reads", "median")).round(0).to_string())

m.to_pickle("out/full.pkl")
print("\nсохранено out/full.pkl:", m.shape)

# ---------- что работает: по эпохам ----------
def tab(col, minn=10):
    rows = []
    for ep in ("1_до_спада", "3_дно"):
        d = m[m["эпоха"] == ep]
        base_sh, base_rd = d["shows"].median(), d["reads"].median()
        for v, g in d.groupby(col, observed=True):
            if len(g) < minn:
                continue
            rows.append({
                "эпоха": ep, "значение": v, "n": len(g),
                "мед_показы": int(g["shows"].median()),
                "инд_показы": round(g["shows"].median() / base_sh, 2),
                "мед_дочит": int(g["reads"].median()),
                "инд_дочит": round(g["reads"].median() / base_rd, 2),
                "CTR": round(g["ctr"].median(), 4),
                "дочитываемость": round(g["read_rate"].median(), 3),
                "комм_на_дочит": round(g["comments_per_read"].median(), 4),
            })
    return pd.DataFrame(rows)


for col in ("сцена", "функция", "порог_входа", "фокус", "спорность", "негативная_рамка",
            "вопрос", "цифра_в_заголовке", "конкретный_якорь", "обращение_вы"):
    t = tab(col)
    if len(t):
        print("\n" + "=" * 150)
        print(f"ПРИЗНАК: {col}")
        print(t.sort_values(["эпоха", "инд_дочит"], ascending=[True, False]).to_string(index=False))
