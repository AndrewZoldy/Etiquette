"""Плоский экспорт текстов статей: одна таблица TSV + читаемый markdown-сборник."""
import csv, glob, json, os
import pandas as pd

DST = r"d:\Work\Etiquette\Etiquette\data\2026-07-26-sbor-dzen"
os.makedirs(DST, exist_ok=True)

m = pd.read_pickle("out/full.pkl")
meta = m.set_index("oid")[["date", "title_studio", "share_link", "сцена", "функция",
                           "shows", "opens", "reads", "ctr", "comments", "likes",
                           "comments_enabled", "эпоха"]].to_dict("index")

rows = []
for f in sorted(glob.glob("out/pages/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    oid = d["oid"]
    mm = meta.get(oid, {})
    rows.append({
        "oid": oid,
        "дата": str(mm.get("date", ""))[:10],
        "заголовок": d.get("title") or mm.get("title_studio") or "",
        "ссылка": d.get("share_link") or mm.get("share_link") or "",
        "сцена": mm.get("сцена", ""),
        "функция": mm.get("функция", ""),
        "эпоха": mm.get("эпоха", ""),
        "комментарии_включены": mm.get("comments_enabled", ""),
        "показы": mm.get("shows", ""),
        "открытия": mm.get("opens", ""),
        "дочитывания": mm.get("reads", ""),
        "CTR": mm.get("ctr", ""),
        "комментариев": mm.get("comments", ""),
        "лайков": mm.get("likes", ""),
        "слов": d.get("n_words"),
        "абзацев": d.get("n_paragraphs"),
        "картинок": d.get("n_images"),
        "подзаголовки": " | ".join(d.get("headers") or []),
        "текст": (d.get("text") or "").replace("\t", " ").replace("\r", " "),
    })

df = pd.DataFrame(rows).sort_values("дата")
p = os.path.join(DST, "teksty-620-statey.tsv")
df.to_csv(p, sep="\t", index=False, encoding="utf-8-sig",
          quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
print(f"TSV: {p} ({os.path.getsize(p)/1048576:.1f} МБ, {len(df)} статей)")

# читаемый сборник, разбитый по годам, чтобы файлы не были огромными
df["год"] = df["дата"].str[:4]
for year, g in df.groupby("год"):
    out = [f"# Статьи канала «Валентина Хлистун | Этикет» — {year}\n",
           f"Статей: {len(g)}. Собрано с Дзена 26.07.2026.\n"]
    for _, r in g.iterrows():
        out.append(f"\n---\n\n## {r['заголовок']}\n")
        out.append(f"**Дата:** {r['дата']} · **Ссылка:** {r['ссылка']} · "
                   f"**Сцена:** {r['сцена']} · **Функция:** {r['функция']}\n")
        out.append(f"**Показы:** {r['показы']} · **Дочитывания:** {r['дочитывания']} · "
                   f"**CTR:** {r['CTR']} · **Комментариев:** {r['комментариев']} · "
                   f"**Комментарии включены:** {r['комментарии_включены']}\n")
        if r["подзаголовки"]:
            out.append(f"**Подзаголовки:** {r['подзаголовки']}\n")
        out.append(f"\n{r['текст']}\n")
    fn = os.path.join(DST, f"teksty-{year}.md")
    open(fn, "w", encoding="utf-8").write("\n".join(out))
    print(f"MD:  {fn} ({os.path.getsize(fn)/1048576:.1f} МБ, {len(g)} статей)")
