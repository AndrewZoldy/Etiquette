"""Разбор обложек: проверка гипотезы «Валентина с мужчинами собирает больше» и остальных признаков."""
import glob, json
import numpy as np
import pandas as pd

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 60)

rows = []
for f in sorted(glob.glob("out/marks/covers_*.jsonl")):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
c = pd.DataFrame(rows).drop_duplicates("oid")
print(f"размечено обложек: {len(c)}")

m = pd.read_pickle("out/full.pkl")
d = m.merge(c, on="oid", how="inner")
print(f"склеено с метриками: {len(d)}")
d = d[d["shows"].notna()]

for col in ("valentina", "valentina_with_man", "companions", "image_kind", "intrigue",
            "people_count", "emotion", "gaze_to_camera", "text_on_image", "royals",
            "historical", "shot", "setting", "celebrity", "quality", "dress_code"):
    if col in d.columns:
        print(f"\n--- {col} ---")
        print(d[col].value_counts(dropna=False).head(12).to_string())


def by(col, ep, minn=10):
    x = d[d["эпоха"] == ep]
    if not len(x):
        return None
    base_s, base_r, base_c = x["shows"].median(), x["reads"].median(), x["ctr"].median()
    out = []
    for v, g in x.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        out.append({"значение": str(v), "n": len(g),
                    "мед_показы": int(g["shows"].median()),
                    "инд_показы": round(g["shows"].median() / base_s, 2),
                    "мед_дочит": int(g["reads"].median()),
                    "инд_дочит": round(g["reads"].median() / base_r, 2),
                    "мед_CTR": round(g["ctr"].median(), 4),
                    "инд_CTR": round(g["ctr"].median() / base_c, 2)})
    return pd.DataFrame(out).sort_values("инд_CTR", ascending=False)


print("\n" + "=" * 150)
print("ГЛАВНАЯ ГИПОТЕЗА: «Валентина вместе с мужчинами собирает больше просмотров»")
for ep in ("1_до_спада", "3_дно"):
    x = d[d["эпоха"] == ep]
    print(f"\n### {ep} (n={len(x)})")
    for col in ("valentina", "valentina_with_man", "companions"):
        t = by(col, ep, minn=8)
        if t is not None and len(t):
            print(f"\n-- {col} --")
            print(t.to_string(index=False))

print("\n" + "=" * 150)
print("ПРОВЕРКА НА ПОДМЕНУ: не объясняется ли эффект темой статьи?")
if "valentina_with_man" in d.columns:
    vm = d[d["valentina_with_man"].astype(str).str.lower().str.startswith("да")]
    print(f"\nвсего обложек «Валентина с мужчиной»: {len(vm)}")
    print(vm["сцена"].value_counts().to_string())
    print("\nих статьи:")
    print(vm[["date", "title_studio", "сцена", "функция", "shows", "reads", "ctr"]]
          .sort_values("shows", ascending=False).head(25).to_string(index=False))

print("\n" + "=" * 150)
print("ОСТАЛЬНЫЕ ПРИЗНАКИ ОБЛОЖКИ по эпохам")
for col in ("image_kind", "intrigue", "people_count", "emotion", "gaze_to_camera",
            "text_on_image", "shot", "setting", "royals", "historical", "quality", "dress_code"):
    if col not in d.columns:
        continue
    for ep in ("1_до_спада", "3_дно"):
        t = by(col, ep)
        if t is not None and len(t) > 1:
            print(f"\n--- {col} | {ep} ---")
            print(t.to_string(index=False))

print("\n" + "=" * 150)
print("ОБЪЕКТИВНЫЕ ЦВЕТОВЫЕ МЕТРИКИ обложки vs результат (на дне)")
bot = d[d["эпоха"] == "3_дно"].dropna(subset=["brightness"])
for col in ("brightness", "saturation", "contrast", "warm"):
    if len(bot) > 30:
        b = bot.copy()
        b["q"] = pd.qcut(b[col], 3, labels=["низкая", "средняя", "высокая"], duplicates="drop")
        g = b.groupby("q", observed=True).agg(n=("shows", "size"), знач=(col, "median"),
                                              мед_показы=("shows", "median"),
                                              мед_CTR=("ctr", "median")).round(4)
        print(f"\n--- {col} ---")
        print(g.to_string())

c.to_pickle("out/covers_marked.pkl")
d.to_pickle("out/covers_joined.pkl")
print("\nсохранено out/covers_marked.pkl, out/covers_joined.pkl")
