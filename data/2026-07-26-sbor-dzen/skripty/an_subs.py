"""Оптимум плотности подзаголовков и главные рычаги дочитываемости, с бутстрапом."""
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


def boot_med_diff(a, b, n=5000):
    a, b = np.asarray(a.dropna()), np.asarray(b.dropna())
    if len(a) < 5 or len(b) < 5:
        return None
    diffs = [np.median(rng.choice(a, len(a), True)) - np.median(rng.choice(b, len(b), True))
             for _ in range(n)]
    return np.median(diffs), np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)


print("=" * 120)
print("1. ПОДЗАГОЛОВКИ: разница дочитываемости с бутстрап-интервалом")
has = c[c["подзаголовков"] > 0]["read_rate"]
no = c[c["подзаголовков"] == 0]["read_rate"]
r = boot_med_diff(has, no)
print(f"есть подзаголовки: n={len(has)} медиана {has.median():.3f}")
print(f"нет:               n={len(no)} медиана {no.median():.3f}")
print(f"разница медиан: {r[0]:+.3f} п.п.*100 = {r[0]*100:+.1f} п.п., "
      f"интервал 95% [{r[1]*100:+.1f}; {r[2]*100:+.1f}]")
print("вывод:", "интервал НЕ содержит нуля — эффект есть" if r[1] > 0 or r[2] < 0
      else "интервал СОДЕРЖИТ ноль — эффект не доказан")

print("\n" + "=" * 120)
print("2. ПЛОТНОСТЬ ПОДЗАГОЛОВКОВ: слов на один подзаголовок")
s = c[c["подзаголовков"] > 0].copy()
s["слов_на_подзаголовок"] = s["n_words"] / s["подзаголовков"]
s["g"] = pd.cut(s["слов_на_подзаголовок"], [0, 50, 80, 120, 200, 9999],
                labels=["до 50", "50-80", "80-120", "120-200", "больше 200"])
print(s.groupby("g", observed=True).agg(n=("read_rate", "size"),
                                        слов_на_подзаг=("слов_на_подзаголовок", "median"),
                                        подзаголовков=("подзаголовков", "median"),
                                        слов=("n_words", "median"),
                                        дочитываемость=("read_rate", "median")).round(3).to_string())
print("\nвсе статьи с подзаголовками, отсортированы по плотности:")
print(s[["title_studio", "подзаголовков", "n_words", "слов_на_подзаголовок", "read_rate"]]
      .sort_values("слов_на_подзаголовок").round(2).to_string(index=False))

print("\n" + "=" * 120)
print("3. ГЛАВНЫЕ РЫЧАГИ ДОЧИТЫВАЕМОСТИ с бутстрапом: крайние группы")
TESTS = [
    ("время чтения по Дзену", "time_to_read_s", 300, 600),
    ("объём статьи, слов", "n_words", 600, 1200),
    ("слов в абзаце", "слов_в_абзаце_мед", 30, 45),
    ("слов в предложении", "слов_в_предложении_мед", 13, 16),
    ("обращений на «вы»", "т_обращение_вы", 8, 2),
    ("доля коротких предложений", "доля_коротких_предложений", 0.25, 0.12),
    ("прямая речь, вхождений", "прямая_речь", 1, 5),
]
for name, col, lo, hi in TESTS:
    if col not in c.columns:
        continue
    a = c[c[col] <= lo]["read_rate"]
    b = c[c[col] >= hi]["read_rate"]
    if len(a) < 10 or len(b) < 10:
        print(f"{name:32s} мало данных (n={len(a)}/{len(b)})")
        continue
    r = boot_med_diff(a, b)
    sign = "✓" if (r[1] > 0 or r[2] < 0) else "—"
    print(f"{name:32s} {col} ≤{lo}: n={len(a):3d} {a.median():.3f}  |  "
          f"≥{hi}: n={len(b):3d} {b.median():.3f}  |  разница {r[0]*100:+5.1f} п.п. "
          f"[{r[1]*100:+5.1f}; {r[2]*100:+5.1f}] {sign}")

print("\n" + "=" * 120)
print("4. ГДЕ СЕЙЧАС РУБРИКА И ЧЕРНОВИК")
v = d[d["title_studio"].astype(str).str.contains("Светская жизнь Петербурга", na=False)]
print(f"{'признак':30s} {'рубрика':>9s} {'канал':>9s} {'лучшая зона':>16s}")
ZONES = [("time_to_read_s", "не больше 300 с"), ("n_words", "не больше 600"),
         ("слов_в_абзаце_мед", "не больше 30"), ("слов_в_предложении_мед", "10-13"),
         ("т_обращение_вы", "8 и больше"), ("доля_коротких_предложений", "0,25 и выше"),
         ("подзаголовков", "8-10 при 500-900 слов")]
for col, zone in ZONES:
    if col in v.columns:
        print(f"{col:30s} {v[col].median():>9.2f} {c[col].median():>9.2f} {zone:>16s}")
print("\nчерновик: 2517 слов, 42 абзаца, 0 подзаголовков, 41 событие")
print(f"оценка времени чтения черновика: около "
      f"{2517 / (v['n_words'].median() / v['time_to_read_s'].median()):.0f} секунд "
      f"= {2517 / (v['n_words'].median() / v['time_to_read_s'].median()) / 60:.1f} минут")
