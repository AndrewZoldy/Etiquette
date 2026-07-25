"""Выгрузить статьи по сценам для построения майндмапа тем субагентами."""
import glob, json, os
import pandas as pd

OUT = "out/themes"
os.makedirs(OUT, exist_ok=True)
m = pd.read_pickle("out/full.pkl")

# текст-затравка: первые 200 знаков каждой статьи, чтобы агент понимал о чём она
lead = {}
for f in glob.glob("out/pages/*.json"):
    d = json.load(open(f, encoding="utf-8"))
    t = (d.get("text") or "").replace("\n", " ")
    lead[d["oid"]] = t[:220]
m["lead"] = m["oid"].map(lead)

m = m.sort_values("date")
scenes = m["сцена"].dropna().unique().tolist()
summary = []
for s in scenes:
    d = m[m["сцена"] == s]
    rows = []
    for _, r in d.iterrows():
        rows.append({
            "заголовок": r["title_studio"],
            "дата": r["date"].strftime("%Y-%m-%d"),
            "эпоха": r["эпоха"],
            "показы": None if pd.isna(r["shows"]) else int(r["shows"]),
            "дочитывания": None if pd.isna(r["reads"]) else int(r["reads"]),
            "CTR": None if pd.isna(r["ctr"]) else round(float(r["ctr"]), 4),
            "комментарии": None if pd.isna(r["comments"]) else int(r["comments"]),
            "функция": r["функция"],
            "порог": r["порог_входа"],
            "начало_текста": r["lead"],
        })
    fn = f"{OUT}/{s}.json"
    json.dump({"сцена": s, "статей": len(rows), "статьи": rows},
              open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    summary.append({"сцена": s, "статей": len(rows), "файл": os.path.abspath(fn).replace("\\", "/"),
                    "мед_показы_до_спада": int(d[d.эпоха == "1_до_спада"]["shows"].median() or 0)
                    if len(d[d.эпоха == "1_до_спада"]) else None,
                    "мед_показы_дно": int(d[d.эпоха == "3_дно"]["shows"].median() or 0)
                    if len(d[d.эпоха == "3_дно"]) else None})
json.dump(summary, open(f"{OUT}/_index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for s in summary:
    print(s["сцена"], s["статей"], "| до спада", s["мед_показы_до_спада"], "| дно", s["мед_показы_дно"])
print("\nкаталог:", os.path.abspath(OUT))
