"""Подготовка иллюстраций к разбору зрением: лёгкие копии 512px, эталоны Валентины, партии для субагентов."""
import glob, io, json, os, shutil
import numpy as np
from PIL import Image
from dzenlib import Dzen, jsonl_read

OUT = "out"
SMALL = os.path.join(OUT, "img", "covers_512")
REF = os.path.join(OUT, "img", "ref")
BATCH = os.path.join(OUT, "batches")
for p in (SMALL, REF, BATCH):
    os.makedirs(p, exist_ok=True)

# ---------- 1. эталонные фото Валентины ----------
d = Dzen()
refs = {
    "avatar": "https://avatars.dzeninfra.ru/get-zen-logos/271828/pub_63dd27aac30ab522dcce48b3_68074a9727a18649081d45e0/orig",
    "og": "https://avatars.dzeninfra.ru/get-zen-pub-og/271828/pub_63dd27aac30ab522dcce48b3_69d66c123ace5e7372591915/orig",
}
for name, url in refs.items():
    p = os.path.join(REF, name + ".jpg")
    if os.path.exists(p):
        continue
    try:
        raw = d.get(url, binary=True, timeout=60)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((640, 640), Image.LANCZOS)
        im.save(p, "JPEG", quality=85)
        print("эталон", name, im.size)
    except Exception as e:
        print("эталон FAIL", name, e)

# ---------- 2. лёгкие копии обложек ----------
made = 0
stats = {}
for f in sorted(glob.glob(os.path.join(OUT, "img", "covers", "*.jpg"))):
    oid = os.path.basename(f)[:-4]
    dst = os.path.join(SMALL, oid + ".jpg")
    im = Image.open(f).convert("RGB")
    w, h = im.size
    # объективные метрики цвета — считаем на маленькой копии
    a = np.asarray(im.resize((64, 64))).astype(float) / 255
    mx, mn = a.max(axis=2), a.min(axis=2)
    stats[oid] = {
        "w": w, "h": h, "aspect": round(w / h, 3),
        "brightness": round(float(a.mean()), 3),
        "saturation": round(float((mx - mn).mean()), 3),
        "contrast": round(float(a.std()), 3),
        "warm": round(float(a[:, :, 0].mean() - a[:, :, 2].mean()), 3),
    }
    if not os.path.exists(dst):
        im2 = im.copy()
        im2.thumbnail((512, 512), Image.LANCZOS)
        im2.save(dst, "JPEG", quality=78, optimize=True)
        made += 1
print(f"лёгких копий сделано {made}, всего {len(os.listdir(SMALL))}")
json.dump(stats, open(os.path.join(OUT, "cover_stats.json"), "w"), ensure_ascii=False)

# ---------- 3. партии для субагентов (вслепую: без метрик!) ----------
pubs = {p["oid"]: p for p in jsonl_read(os.path.join(OUT, "publications.jsonl"))}
files = sorted(os.listdir(SMALL))
# перемешиваем детерминированно, чтобы партии не были по датам
import hashlib
files.sort(key=lambda f: hashlib.md5(f.encode()).hexdigest())

N_BATCH = 14
size = -(-len(files) // N_BATCH)
absdir = os.path.abspath(SMALL).replace("\\", "/")
for i in range(N_BATCH):
    chunk = files[i * size:(i + 1) * size]
    if not chunk:
        continue
    rows = [{"oid": f[:-4], "file": f"{absdir}/{f}",
             "title": (pubs.get(f[:-4]) or {}).get("title", "")} for f in chunk]
    json.dump(rows, open(os.path.join(BATCH, f"covers_{i:02d}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
print(f"партий {N_BATCH}, по {size} обложек, каталог {os.path.abspath(BATCH)}")
sz = sum(os.path.getsize(os.path.join(SMALL, f)) for f in os.listdir(SMALL)) / 1048576
print(f"объём лёгкого набора {sz:.0f} МБ (средний файл {sz*1024/len(files):.0f} КБ)")
