"""Стратифицированная выборка статей для разбора ВНУТРЕННИХ иллюстраций + лёгкие копии 512px."""
import glob, json, os
import numpy as np
import pandas as pd
from PIL import Image

OUT = "out"
SMALL = os.path.join(OUT, "img", "body_512")
BDIR = os.path.join(OUT, "batches_body")
os.makedirs(SMALL, exist_ok=True)
os.makedirs(BDIR, exist_ok=True)

m = pd.read_pickle("out/full.pkl")
m = m[m["shows"].notna() & m["oid"].notna()]

# ---------- выборка: полюса каждой эпохи ----------
def pick(ep, k):
    d = m[m["эпоха"] == ep].sort_values("shows", ascending=False)
    return pd.concat([d.head(k), d.tail(k)])


sample = pd.concat([pick("1_до_спада", 30), pick("3_дно", 40)]).drop_duplicates("oid")
# плюс случайная середина, чтобы выборка не была только из полюсов
rest = m[~m["oid"].isin(sample["oid"])]
mid = rest.sample(n=min(30, len(rest)), random_state=7)
sample = pd.concat([sample, mid]).drop_duplicates("oid")
print(f"в выборке статей: {len(sample)}")
print(sample.groupby("эпоха").size().to_string())

# ---------- лёгкие копии картинок этих статей ----------
pages = {}
for oid in sample["oid"]:
    p = f"out/pages/{oid}.json"
    if os.path.exists(p):
        pages[oid] = json.load(open(p, encoding="utf-8"))

made, total = 0, 0
manifest = []
absd = os.path.abspath(SMALL).replace("\\", "/")
for oid, d in pages.items():
    imgs = d.get("images") or []
    files = []
    for k, im in enumerate(imgs):
        src = f"out/img/body/{oid}_{k:02d}_{im['id']}.jpg"
        if not os.path.exists(src):
            continue
        dst = os.path.join(SMALL, f"{oid}_{k:02d}.jpg")
        total += 1
        if not os.path.exists(dst):
            try:
                x = Image.open(src).convert("RGB")
                x.thumbnail((512, 512), Image.LANCZOS)
                x.save(dst, "JPEG", quality=75, optimize=True)
                made += 1
            except Exception:
                continue
        files.append({"n": k, "file": f"{absd}/{oid}_{k:02d}.jpg",
                      "подпись": im.get("caption")})
    manifest.append({
        "oid": oid, "заголовок": d.get("title"),
        "картинок": len(files), "картинки": files,
        "подзаголовки": d.get("headers") or [],
        "абзацев": d.get("n_paragraphs"), "слов": d.get("n_words"),
    })
print(f"лёгких копий: сделано {made}, всего файлов {total}")

# ---------- партии ----------
manifest = [x for x in manifest if x["картинок"] > 0]
import hashlib
manifest.sort(key=lambda x: hashlib.md5(x["oid"].encode()).hexdigest())
N = 12
size = -(-len(manifest) // N)
for i in range(N):
    ch = manifest[i * size:(i + 1) * size]
    if ch:
        json.dump(ch, open(f"{BDIR}/body_{i:02d}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
print(f"партий: {min(N, -(-len(manifest)//size))}, статей в партии ~{size}, "
      f"каталог {os.path.abspath(BDIR)}")
sample[["oid", "title_studio", "date", "эпоха", "shows", "reads", "ctr"]].to_pickle("out/body_sample.pkl")
print("выборка сохранена out/body_sample.pkl")
