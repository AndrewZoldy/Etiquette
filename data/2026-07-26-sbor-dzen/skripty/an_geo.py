"""Комментарии к рубрике: география читателей и что они вообще говорят."""
import glob, json, os, re
from collections import Counter
import pandas as pd

m = pd.read_pickle("out/full.pkl")
v = m[m["title_studio"].astype(str).str.contains("Светская жизнь Петербурга", na=False)].sort_values("date")

allc = []
for _, row in v.iterrows():
    p = f"out/comments/{row['oid']}.json"
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    for c in d.get("comments") or []:
        allc.append({"дата": row["date"].strftime("%d.%m"), "дочит": int(row["reads"]),
                     "автор": c.get("author_name"), "лайки": c.get("likes") or 0,
                     "дизлайки": c.get("dislikes") or 0, "текст": c.get("text") or ""})
cm = pd.DataFrame(allc)
print(f"комментариев к рубрике всего: {len(cm)} по {cm['дата'].nunique()} выпускам")

GEO = {
    "не в Петербурге": r"(не в питер|не в петербург|я из|живу в|у нас в|приеду|приезжа|"
                       r"далеко|москв|регион|провинц|жаль что не|мне бы|была бы в)",
    "хочу пойти / пойду": r"(пойд|схожу|обязательно буд|запиш|беру билет|спасибо за подборк|"
                          r"сохран|в закладк)",
    "благодарность": r"(спасибо|благодар|как всегда интересн|люблю ваш)",
    "про формат": r"(длинн|много текст|не дочит|устал|перечисл|список|структур|"
                  r"тяжело чита|разбит)",
    "про Петербург вообще": r"(петербург|питер|спб|нев|эрмитаж|мариин)",
}
print("\nМАРКЕРЫ В КОММЕНТАРИЯХ:")
for k, rx in GEO.items():
    mask = cm["текст"].str.contains(rx, case=False, na=False, regex=True)
    print(f"  {k:26s} {mask.sum():4d} из {len(cm)} = {mask.mean():.1%}, "
          f"медиана лайков {cm[mask]['лайки'].median() if mask.sum() else 0:.0f}")

print("\n" + "=" * 120)
print("ВСЕ КОММЕНТАРИИ К РУБРИКЕ, отсортированы по лайкам (топ-30)")
for _, r in cm.nlargest(30, "лайки").iterrows():
    print(f"[{r['дата']} +{r['лайки']}/-{r['дизлайки']}] {r['автор']}: {r['текст'][:220]}")

print("\n" + "=" * 120)
print("КТО КОММЕНТИРУЕТ РУБРИКУ (топ-12 авторов)")
print(cm["автор"].value_counts().head(12).to_string())
print("\nсколько из них комментируют канал в целом (для сравнения ядра):")
core = cm["автор"].value_counts()
print(f"уникальных авторов в рубрике: {cm['автор'].nunique()}, "
      f"комментариев в среднем на автора: {len(cm)/max(cm['автор'].nunique(),1):.1f}")
