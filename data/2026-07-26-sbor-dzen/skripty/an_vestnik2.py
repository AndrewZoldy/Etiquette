"""Своя проверка: длина против дочитываемости внутри рубрики и вокруг неё."""
import glob, json, os
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna()].copy()
tf = pd.read_pickle("out/text_feats.pkl")
dup = [c for c in tf.columns if c != "oid" and c in m.columns]
tf = tf.rename(columns={c: "т_" + c for c in dup})
m = m.merge(tf, on="oid", how="left")

# только настоящие выпуски рубрики
r = m[m["title_studio"].astype(str).str.contains("Светская жизнь Петербурга", na=False)].copy()
r = r.sort_values("date")
print(f"выпусков рубрики: {len(r)}")

print("\n" + "=" * 130)
print("1. ДЛИНА ПРОТИВ ДОЧИТЫВАЕМОСТИ ВНУТРИ РУБРИКИ")
t = r[["date", "n_words", "read_rate", "reads", "opens", "ctr", "n_paragraphs",
       "слов_в_абзаце_мед", "слов_в_предложении_мед", "time_to_read_s"]].copy()
t["дата"] = t["date"].dt.strftime("%d.%m")
print(t[["дата", "n_words", "read_rate", "reads", "opens", "ctr",
         "n_paragraphs", "слов_в_абзаце_мед", "слов_в_предложении_мед", "time_to_read_s"]]
      .round(4).to_string(index=False))

for a, b in (("n_words", "read_rate"), ("n_words", "reads"), ("n_words", "opens"),
             ("n_words", "ctr"), ("time_to_read_s", "read_rate")):
    x = r.dropna(subset=[a, b])
    if len(x) >= 8:
        rho = x[[a, b]].corr(method="spearman").iloc[0, 1]
        pr = x[[a, b]].corr().iloc[0, 1]
        print(f"  {a:18s} × {b:12s}: Спирмен {rho:+.3f}, Пирсон {pr:+.3f} (n={len(x)})")

print("\n" + "=" * 130)
print("2. КЛЮЧЕВАЯ ЛОВУШКА: длина или календарь? Порядок выпуска тоже растёт со временем")
r = r.reset_index(drop=True)
r["номер"] = range(1, len(r) + 1)
for a in ("n_words", "номер"):
    x = r.dropna(subset=[a, "read_rate"])
    rho = x[[a, "read_rate"]].corr(method="spearman").iloc[0, 1]
    print(f"  {a:10s} × дочитываемость: Спирмен {rho:+.3f}")
print(f"  n_words × номер выпуска:      Спирмен "
      f"{r[['n_words','номер']].corr(method='spearman').iloc[0,1]:+.3f}")
print("\nчастная связь (ранговая регрессия дочитываемости на длину и номер):")
try:
    from scipy import stats
    rr = r.dropna(subset=["n_words", "read_rate"]).copy()
    rw = stats.rankdata(rr["n_words"]); rn = stats.rankdata(rr["номер"]); ry = stats.rankdata(rr["read_rate"])
    X = np.column_stack([np.ones(len(rr)), rw, rn])
    beta, *_ = np.linalg.lstsq(X, ry, rcond=None)
    print(f"  коэффициент при длине {beta[1]:+.3f}, при номере {beta[2]:+.3f}")
    # частные корреляции
    def partial(x, y, z):
        rxy = np.corrcoef(x, y)[0, 1]; rxz = np.corrcoef(x, z)[0, 1]; ryz = np.corrcoef(y, z)[0, 1]
        return (rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    print(f"  частная корреляция длина×дочитываемость при фикс. номере: {partial(rw, ry, rn):+.3f}")
    print(f"  частная корреляция номер×дочитываемость при фикс. длине:  {partial(rn, ry, rw):+.3f}")
except Exception as e:
    print("  scipy недоступен:", e)

print("\n" + "=" * 130)
print("3. ЕСТЬ ЛИ В КАНАЛЕ ДЛИННЫЕ СТАТЬИ С ХОРОШИМ ДОЧИТЫВАНИЕМ")
long = m[(m["n_words"] > 1200)].sort_values("read_rate", ascending=False)
print(f"статей длиннее 1200 слов: {len(long)}")
print(long[["date", "title_studio", "n_words", "read_rate", "reads", "n_paragraphs",
            "слов_в_абзаце_мед"]].head(12).round(3).to_string(index=False))
print(f"\nиз них с дочитываемостью выше 45%: {(long['read_rate'] > 0.45).sum()}")

print("\n" + "=" * 130)
print("4. ЧТО РАЗЛИЧАЕТ РУБРИКУ И УДАЧНЫЕ СВЕТСКИЕ СТАТЬИ")
good = m[m["title_studio"].astype(str).str.contains(
    "Ошибки, которые сразу выдают|Темы для светских бесед|Дама здоровается первая|"
    "ice breakers|культурный выход", na=False, regex=True)]
COMP = ["n_words", "n_paragraphs", "слов_в_абзаце_мед", "слов_в_предложении_мед", "вопросов",
        "длина_последнего_абзаца", "n_images", "time_to_read_s", "min_per_read",
        "read_rate", "ctr", "доля_коротких_предложений", "цифры", "т_обращение_вы"]
COMP = [c for c in COMP if c in m.columns]
cmp = pd.DataFrame({
    "рубрика (10)": r[COMP].median(),
    "удачные светские (5)": good[COMP].median(),
    "канал (620)": m[COMP].median(),
}).round(3)
cmp["во_сколько_раз"] = (cmp["рубрика (10)"] / cmp["удачные светские (5)"].replace(0, np.nan)).round(2)
print(cmp.to_string())

print("\n" + "=" * 130)
print("5. ВРЕМЯ ЧТЕНИЯ: сколько Дзен требует прочитать, чтобы зачесть дочитывание")
print("Дзен считает дочитыванием прохождение до конца. Оценка нужного времени:")
r2 = r.copy()
r2["сек_на_1000_слов"] = r2["time_to_read_s"] / r2["n_words"] * 1000
print(r2[["дата", "n_words", "time_to_read_s", "сек_на_1000_слов", "min_per_read", "read_rate"]]
      .round(2).to_string(index=False))
print(f"\nмедиана времени чтения рубрики: {r['time_to_read_s'].median():.0f} сек "
      f"({r['time_to_read_s'].median()/60:.1f} мин)")
print(f"медиана по каналу:              {m['time_to_read_s'].median():.0f} сек "
      f"({m['time_to_read_s'].median()/60:.1f} мин)")

print("\n" + "=" * 130)
print("6. КОММЕНТАРИИ К РУБРИКЕ: о чём пишут")
for _, row in r.iterrows():
    p = f"out/comments/{row['oid']}.json"
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    cs = sorted(d.get("comments") or [], key=lambda c: -(c.get("likes") or 0))
    print(f"\n--- {row['date'].strftime('%d.%m')} ({int(row['reads'])} дочит., "
          f"{len(cs)} комм.) ---")
    for c in cs[:4]:
        print(f"  [+{c.get('likes')}] {(c.get('text') or '')[:170]}")
