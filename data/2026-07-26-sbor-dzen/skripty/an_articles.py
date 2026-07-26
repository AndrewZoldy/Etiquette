"""Свести поштучный разбор статей и проверить каждый признак с контролем на тему."""
import glob, json, os, re
from collections import Counter
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

rows = []
for f in glob.glob("out/marks_article/*.json"):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(d, list):
        rows.extend(x for x in d if isinstance(x, dict))
    elif isinstance(d, dict):
        if "oid" not in d:
            d["oid"] = os.path.basename(f)[:-5]
        rows.append(d)
a = pd.DataFrame(rows).drop_duplicates("oid")
print("разобрано статей поштучно:", len(a))
print("полей:", len(a.columns))
print("\nзаполненность ключевых полей:")
KEY = ["subject", "norm_disputable", "opening_type", "hook_strength", "structure",
       "ending_type", "ending_words", "tone", "author_stance", "recognisability",
       "dispute_potential", "novelty", "hate_risk", "cover_people", "cover_interaction",
       "cover_link_to_title", "cover_curiosity_gap", "frames_on_point", "frames_off",
       "shows_mistake", "reaction_mix", "hate_themes", "top_comment_type",
       "own_stories", "strength_score", "cost_to_follow", "situation_frequency"]
for c in KEY:
    if c in a.columns:
        print(f"   {c:24s} {a[c].notna().sum():4d} / {len(a)}")
    else:
        print(f"   {c:24s} НЕТ ПОЛЯ")

m = pd.read_pickle("out/full.pkl")
d = m.merge(a, on="oid", how="inner", suffixes=("", "_a"))
d = d[d["shows"].notna()].copy()
print(f"\nсклеено с метриками: {len(d)}; по эпохам: {d.groupby('эпоха').size().to_dict()}")

# часть полей агенты возвращают списками — приводим к строке, иначе группировка падает
for c in d.columns:
    if d[c].apply(lambda v: isinstance(v, (list, dict))).any():
        d[c] = d[c].apply(lambda v: ", ".join(map(str, v)) if isinstance(v, list)
                          else (json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v))

NUMS = ["hook_strength", "recognisability", "dispute_potential", "novelty", "hate_risk",
        "strength_score", "cover_interaction", "cover_curiosity_gap", "ending_words",
        "frames_on_point", "frames_off", "concrete_examples", "categoricalness", "set_score"]
for c in NUMS:
    if c in d.columns:
        d[c] = pd.to_numeric(d[c], errors="coerce")


def tab(col, ep, minn=10):
    x = d[d["эпоха"] == ep]
    if not len(x):
        return None
    br, bc = x["reads"].median(), x["ctr"].median()
    out = []
    for v, g in x.groupby(col, dropna=False, observed=True):
        if len(g) < minn:
            continue
        out.append({"значение": str(v)[:34], "n": len(g),
                    "мед_дочит": int(g["reads"].median()),
                    "инд_дочит": round(g["reads"].median() / max(br, 1), 2),
                    "мед_CTR": round(g["ctr"].median(), 4),
                    "инд_CTR": round(g["ctr"].median() / bc, 2),
                    "дочитыв": round(g["read_rate"].median(), 3),
                    "комм": int(g["comments"].median())})
    df = pd.DataFrame(out)
    return df.sort_values("инд_дочит", ascending=False) if len(df) else df


CATS = ["norm_disputable", "norm_clear", "opening_type", "structure", "ending_type", "tone",
        "author_stance", "situation_frequency", "cost_to_follow", "cover_people",
        "cover_link_to_title", "shows_mistake", "own_stories", "top_comment_type",
        "personal_experience", "call_to_comment", "title_promise_kept", "judged_party",
        "self_repeat", "audience", "norm_source"]
print("\n" + "=" * 145)
print("КАТЕГОРИАЛЬНЫЕ ПРИЗНАКИ (поштучный разбор)")
for col in CATS:
    if col not in d.columns:
        continue
    for ep in ("1_до_спада", "3_дно"):
        t = tab(col, ep)
        if t is not None and len(t) > 1:
            print(f"\n--- {col} | {ep} ---")
            print(t.to_string(index=False))

print("\n" + "=" * 145)
print("ЧИСЛОВЫЕ ОЦЕНКИ, эпоха дно (Спирмен с дочитываниями)")
bot = d[d["эпоха"] == "3_дно"]
for c in NUMS:
    if c not in bot.columns:
        continue
    x = bot.dropna(subset=[c])
    if len(x) < 25 or x[c].nunique() < 3:
        continue
    rho = x[[c, "reads"]].corr(method="spearman").iloc[0, 1]
    rho2 = x[[c, "ctr"]].corr(method="spearman").iloc[0, 1]
    rho3 = x[[c, "comments"]].corr(method="spearman").iloc[0, 1]
    print(f"  {c:22s} дочит {rho:+.3f}  CTR {rho2:+.3f}  комментарии {rho3:+.3f}  (n={len(x)})")

print("\n" + "=" * 145)
print("ТЕМЫ ПРЕТЕНЗИЙ ХЕЙТЕРОВ по всему разобранному корпусу")
cnt = Counter()
for v in d.get("hate_themes", pd.Series(dtype=object)).dropna():
    items = v if isinstance(v, list) else re.split(r"[,;]", str(v))
    for x in items:
        x = str(x).strip().lower()
        if x and x not in ("нет", "не определить", "[]"):
            cnt[x] += 1
for k, v in cnt.most_common(20):
    print(f"   {v:4d}  {k}")

print("\n" + "=" * 145)
print("ПЕРЕПИСАННЫЕ ЗАГОЛОВКИ: примеры от агентов (самые слабые статьи)")
if "rewrite_headline" in d.columns:
    w = d[d["эпоха"] == "3_дно"].nsmallest(15, "reads")[
        ["title_studio", "reads", "rewrite_headline"]]
    for _, r in w.iterrows():
        print(f"\n  было: {r.title_studio}  ({int(r.reads)} дочит.)")
        print(f"  стало: {r.rewrite_headline}")

a.to_pickle("out/articles_marked.pkl")
d.to_pickle("out/articles_joined.pkl")
print("\nсохранено out/articles_marked.pkl, out/articles_joined.pkl")
