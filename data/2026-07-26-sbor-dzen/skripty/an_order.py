"""Проверка гипотезы про порядок и «дойти, чтобы увидеть все варианты».
Измеримый на данных механизм: обещанное число пунктов в заголовке = счётчик прогресса."""
import re
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
rng = np.random.default_rng(20260726)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna() & m["read_rate"].notna()].copy()
tf = pd.read_pickle("out/text_feats.pkl")
dup = [c for c in tf.columns if c != "oid" and c in m.columns]
tf = tf.rename(columns={c: "т_" + c for c in dup})
d = m.merge(tf, on="oid", how="left")
c = d[d["comments_enabled"] == True].copy()
c["t"] = c["title_studio"].astype(str)


def boot(a, b, n=5000):
    a, b = np.asarray(a.dropna()), np.asarray(b.dropna())
    if len(a) < 8 or len(b) < 8:
        return None
    dd = [np.median(rng.choice(a, len(a), True)) - np.median(rng.choice(b, len(b), True))
          for _ in range(n)]
    return np.median(dd) * 100, np.percentile(dd, 2.5) * 100, np.percentile(dd, 97.5) * 100


print("=" * 125)
print("1. ОБЕЩАННОЕ ЧИСЛО ПУНКТОВ В ЗАГОЛОВКЕ = счётчик прогресса для читателя")
# «10 жестов», «Топ-5», «Три ошибки», «5 фраз»
NUM = r"(^|\s)(топ[- ]?\d+|\d+\s+[а-яё]|(две|три|четыре|пять|шесть|семь|восемь|девять|десять)\s+[а-яё])"
c["счётчик"] = np.where(c["t"].str.contains(NUM, case=False, regex=True), "есть счётчик", "нет")
g = c.groupby("счётчик").agg(n=("read_rate", "size"), дочитываемость=("read_rate", "median"),
                             мед_дочит=("reads", "median"), мед_слов=("n_words", "median"),
                             мед_CTR=("ctr", "median")).round(4)
print(g.to_string())
r = boot(c[c["счётчик"] == "есть счётчик"]["read_rate"], c[c["счётчик"] == "нет"]["read_rate"])
if r:
    print(f"разница дочитываемости: {r[0]:+.1f} п.п., интервал [{r[1]:+.1f}; {r[2]:+.1f}] "
          f"{'✓ значимо' if (r[1] > 0 or r[2] < 0) else '— не значимо'}")

print("\nпримеры статей со счётчиком, лучшие по дочитываемости:")
print(c[c["счётчик"] == "есть счётчик"].nlargest(12, "read_rate")
      [["t", "n_words", "read_rate", "reads"]].round(3).to_string(index=False))

print("\n" + "=" * 125)
print("2. КОНТРОЛЬ НА ДЛИНУ: счётчик внутри узких полос объёма")
c["полоса"] = pd.cut(c["n_words"], [0, 500, 650, 850, 9999],
                     labels=["до 500", "500-650", "650-850", "больше 850"])
t = c.pivot_table(index="полоса", columns="счётчик", values="read_rate",
                  aggfunc="median", observed=True).round(3)
n = c.pivot_table(index="полоса", columns="счётчик", values="read_rate",
                  aggfunc="size", observed=True)
print("дочитываемость:")
print(t.to_string())
print("\nчисло статей:")
print(n.to_string())

print("\n" + "=" * 125)
print("3. СКОЛЬКО ПУНКТОВ ОБЕЩАТЬ: разбор по числу в заголовке")
def num_in_title(s):
    mm = re.search(r"топ[- ]?(\d+)|(\d+)\s+[а-яё]", s.lower())
    if mm:
        v = mm.group(1) or mm.group(2)
        try:
            return int(v)
        except Exception:
            return None
    for w, v in (("две", 2), ("три", 3), ("четыре", 4), ("пять", 5), ("шесть", 6),
                 ("семь", 7), ("восемь", 8), ("девять", 9), ("десять", 10)):
        if re.search(rf"(^|\s){w}\s+[а-яё]", s.lower()):
            return v
    return None


c["обещано"] = c["t"].map(num_in_title)
s = c[c["обещано"].notna() & (c["обещано"] <= 20)].copy()
s["гр"] = pd.cut(s["обещано"], [0, 3, 5, 7, 20], labels=["2-3", "4-5", "6-7", "8+"])
print(s.groupby("гр", observed=True).agg(n=("read_rate", "size"), обещано=("обещано", "median"),
                                         дочитываемость=("read_rate", "median"),
                                         мед_слов=("n_words", "median"),
                                         мед_дочит=("reads", "median")).round(3).to_string())

print("\n" + "=" * 125)
print("4. ПОРЯДОК В САМОЙ РУБРИКЕ: проверяю, действительно ли он хронологический")
import glob, json, os
v = d[d["title_studio"].astype(str).str.contains("Светская жизнь Петербурга", na=False)].sort_values("date")
DATE = re.compile(r"\b(\d{1,2})\s+(янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)")
for _, row in v.iterrows():
    p = f"out/pages/{row['oid']}.json"
    if not os.path.exists(p):
        continue
    pg = json.load(open(p, encoding="utf-8"))
    seq = []
    for i, par in enumerate(pg.get("paragraphs") or []):
        mm = DATE.search(par[:60])
        if mm:
            seq.append((i, int(mm.group(1))))
    days = [x[1] for x in seq]
    mono = all(days[i] <= days[i + 1] for i in range(len(days) - 1)) if len(days) > 1 else None
    print(f"  {row['date'].strftime('%d.%m')}: дат в началах абзацев {len(days)}, "
          f"порядок {'строго по возрастанию' if mono else 'не монотонный' if mono is False else 'мало дат'}, "
          f"дни: {days[:12]}")

print("\n" + "=" * 125)
print("5. ЧТО СТОИТ ПЕРВЫМ И ПОСЛЕДНИМ в выпусках рубрики")
for _, row in v.iterrows():
    p = f"out/pages/{row['oid']}.json"
    if not os.path.exists(p):
        continue
    pg = json.load(open(p, encoding="utf-8"))
    ps = pg.get("paragraphs") or []
    if len(ps) < 3:
        continue
    print(f"\n--- {row['date'].strftime('%d.%m')} (дочитываемость {row['read_rate']:.1%}) ---")
    print(f"  ПЕРВЫЙ  : {ps[0][:150]}")
    print(f"  ВТОРОЙ  : {ps[1][:150]}")
    print(f"  ПОСЛЕДНИЙ: {ps[-1][:150]}")
