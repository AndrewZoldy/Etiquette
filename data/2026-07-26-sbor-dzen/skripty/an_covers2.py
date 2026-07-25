"""Чистый разбор обложек: приведение типов, взаимодействие в кадре, контроль на тему."""
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 60)

d = pd.read_pickle("out/covers_joined.pkl")
d = d[d["shows"].notna()].copy()
for c in ("intrigue", "people_count", "оценка_1_5"):
    if c in d.columns:
        d[c] = pd.to_numeric(d[c], errors="coerce")
d["есть_люди"] = np.where(d["people_count"].fillna(0) > 0, "есть люди", "нет людей")
d["взаимодействие"] = np.where(d["intrigue"].fillna(0) >= 2, "2-3 взаимодействие",
                        np.where(d["intrigue"].fillna(0) == 1, "1 рядом", "0 нет"))


def tab(col, ep, minn=10):
    x = d[d["эпоха"] == ep]
    bs, br, bc = x["shows"].median(), x["reads"].median(), x["ctr"].median()
    out = []
    for v, g in x.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        out.append({"значение": str(v), "n": len(g),
                    "мед_показы": int(g["shows"].median()), "инд_показы": round(g["shows"].median()/bs, 2),
                    "мед_дочит": int(g["reads"].median()), "инд_дочит": round(g["reads"].median()/br, 2),
                    "мед_CTR": round(g["ctr"].median(), 4), "инд_CTR": round(g["ctr"].median()/bc, 2)})
    return pd.DataFrame(out).sort_values("инд_дочит", ascending=False)


for col in ("есть_люди", "взаимодействие", "companions", "image_kind", "emotion",
            "gaze_to_camera", "text_on_image", "shot", "setting", "royals", "historical",
            "quality", "dress_code", "main_subject_gender"):
    if col not in d.columns:
        continue
    print("\n" + "=" * 120)
    print(f"ПРИЗНАК: {col}")
    for ep in ("1_до_спада", "3_дно"):
        t = tab(col, ep)
        if len(t) > 1:
            print(f"\n-- {ep} --")
            print(t.to_string(index=False))

print("\n" + "=" * 120)
print("КОНТРОЛЬ НА ТЕМУ: взаимодействие в кадре внутри работающих сцен, эпоха «дно»")
bot = d[d["эпоха"] == "3_дно"]
good = bot[bot["сцена"].isin(["отношения_общение", "дом_семья", "гости_праздники", "стол_еда"])]
g = good.groupby("взаимодействие", observed=True).agg(
    n=("shows", "size"), мед_показы=("shows", "median"), мед_дочит=("reads", "median"),
    мед_CTR=("ctr", "median")).round(4)
print(g.to_string())

print("\n" + "=" * 120)
print("ОБЛОЖКИ «Валентина с мужчиной» — все 11 штук")
vm = d[d["valentina_with_man"].astype(str).str.strip().str.lower() == "да"]
print(vm[["date", "title_studio", "сцена", "shows", "reads", "ctr", "intrigue", "notes"]]
      .sort_values("shows", ascending=False).to_string(index=False))

print("\n" + "=" * 120)
print("СКОЛЬКО ОБЛОЖЕК ВООБЩЕ БЕЗ ЛЮДЕЙ и как это связано с результатом")
print(d.groupby(["эпоха", "есть_люди"]).agg(n=("shows", "size"), мед_показы=("shows", "median"),
                                            мед_дочит=("reads", "median"),
                                            мед_CTR=("ctr", "median")).round(4).to_string())

print("\n" + "=" * 120)
print("ЯРКОСТЬ ОБЛОЖКИ (объективно) vs результат, эпоха «дно»")
b = d[(d["эпоха"] == "3_дно")].dropna(subset=["brightness"]).copy()
b["q"] = pd.qcut(b["brightness"], 4, labels=["тёмные", "скорее тёмные", "скорее светлые", "светлые"])
print(b.groupby("q", observed=True).agg(n=("shows", "size"), яркость=("brightness", "median"),
                                        мед_показы=("shows", "median"), мед_дочит=("reads", "median"),
                                        мед_CTR=("ctr", "median")).round(4).to_string())
