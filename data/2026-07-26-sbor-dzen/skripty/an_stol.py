"""Что случилось с категорией «стол_еда» и почему она провалилась сильнее канала."""
import json, glob
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 70)

m = pd.read_pickle("out/full.pkl")
bot = m[m["эпоха"] == "3_дно"]

print("=" * 150)
print("ДИНАМИКА СЦЕН ПО ПОЛУГОДИЯМ (медиана показов / число статей)")
m["half"] = m["date"].dt.year.astype(str) + "H" + ((m["date"].dt.month > 6).astype(int) + 1).astype(str)
p = m.pivot_table(index="сцена", columns="half", values="shows", aggfunc="median")
n = m.pivot_table(index="сцена", columns="half", values="shows", aggfunc="size")
print("\nмедиана показов:")
print(p.round(0).to_string())
print("\nчисло статей:")
print(n.fillna(0).astype(int).to_string())

print("\n" + "=" * 150)
print("«СТОЛ_ЕДА» НА ДНЕ: 60 статей — что это такое")
s = bot[bot["сцена"] == "стол_еда"].sort_values("date")
print(s[["date", "title_studio", "n_words", "n_images", "shows", "opens", "reads",
         "ctr", "read_rate", "comments", "likes"]].to_string(index=False))

print("\n" + "=" * 150)
print("СРАВНЕНИЕ: стол_еда до спада vs на дне — характеристики самих статей")
for ep in ("1_до_спада", "3_дно"):
    d = m[(m["эпоха"] == ep) & (m["сцена"] == "стол_еда")]
    print(f"\n{ep}: n={len(d)}")
    print(f"  слов: медиана {d.n_words.median():.0f} (было бы видно, если тексты стали короче)")
    print(f"  картинок: медиана {d.n_images.median():.0f}")
    print(f"  подзаголовков: медиана {d.n_headers.median():.0f}")
    print(f"  время на чтение (сек): медиана {d.time_to_read_s.median():.0f}")
    print(f"  дочитываемость: {d.read_rate.median():.3f}   CTR: {d.ctr.median():.4f}")
    print(f"  доля с нулевыми комментариями: {(d.comments == 0).mean():.2f}")
    print(f"  доля 'узкая' тема: {(d.порог_входа == 'узкая').mean():.2f}")
    print(f"  доля 'познавательное': {(d.функция == 'познавательное').mean():.2f}")

print("\n" + "=" * 150)
print("ОБЩЕЕ: как менялись сами статьи (длина, картинки) по полугодиям")
q = m.groupby("half").agg(n=("oid", "size"), слов=("n_words", "median"),
                          картинок=("n_images", "median"), подзаг=("n_headers", "median"),
                          сек_чтения=("time_to_read_s", "median"),
                          доля_узких=("порог_входа", lambda s: round((s == "узкая").mean(), 2)),
                          доля_познават=("функция", lambda s: round((s == "познавательное").mean(), 2)),
                          доля_польза=("функция", lambda s: round((s == "польза").mean(), 2)),
                          доля_спорных=("спорность", lambda s: round(pd.to_numeric(s, errors="coerce").mean(), 2)),
                          )
print(q.to_string())

print("\n" + "=" * 150)
print("ТОП-15 статей эпохи «дно» по дочитываниям — что ещё работает")
t = bot.nlargest(15, "reads")[["date", "title_studio", "сцена", "функция", "shows", "reads",
                               "ctr", "comments", "n_words"]]
print(t.to_string(index=False))

print("\n" + "=" * 150)
print("ХУДШИЕ 15 статей эпохи «дно»")
w = bot.nsmallest(15, "shows")[["date", "title_studio", "сцена", "функция", "shows", "opens",
                                "reads", "n_words"]]
print(w.to_string(index=False))
