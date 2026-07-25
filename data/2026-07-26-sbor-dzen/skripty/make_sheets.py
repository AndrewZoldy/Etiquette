"""Сводное полотно (контактный лист) по каждой статье: все её иллюстрации на одной картинке."""
import glob, json, os
from PIL import Image, ImageDraw, ImageFont

OUT = "out"
SHEETS = os.path.join(OUT, "img", "sheets")
BD = os.path.join(OUT, "batches_sheets")
os.makedirs(SHEETS, exist_ok=True)
os.makedirs(BD, exist_ok=True)

CELL = 300          # сторона ячейки
PAD = 6
COLS = 4
LABEL = 18          # полоска под номер кадра

try:
    FONT = ImageFont.truetype("arial.ttf", 14)
except Exception:
    FONT = ImageFont.load_default()


def build(oid, imgs):
    files = []
    for k, im in enumerate(imgs):
        p = f"out/img/body/{oid}_{k:02d}_{im['id']}.jpg"
        if os.path.exists(p):
            files.append((k, p))
    if not files:
        return None
    cols = min(COLS, len(files))
    rows = -(-len(files) // cols)
    W = cols * CELL + (cols + 1) * PAD
    H = rows * (CELL + LABEL) + (rows + 1) * PAD
    sheet = Image.new("RGB", (W, H), (235, 235, 238))
    dr = ImageDraw.Draw(sheet)
    for i, (k, p) in enumerate(files):
        r, c = divmod(i, cols)
        x = PAD + c * (CELL + PAD)
        y = PAD + r * (CELL + LABEL + PAD)
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        im.thumbnail((CELL, CELL), Image.LANCZOS)
        ox = x + (CELL - im.size[0]) // 2
        oy = y + (CELL - im.size[1]) // 2
        sheet.paste(im, (ox, oy))
        dr.rectangle([x, y + CELL, x + CELL, y + CELL + LABEL], fill=(28, 28, 32))
        dr.text((x + 4, y + CELL + 2), f"#{k}" + (" — обложка" if k == 0 else ""),
                fill=(245, 245, 245), font=FONT)
    return sheet


pages = sorted(glob.glob("out/pages/*.json"))
made, skipped, manifest = 0, 0, []
absd = os.path.abspath(SHEETS).replace("\\", "/")
for f in pages:
    d = json.load(open(f, encoding="utf-8"))
    oid = d["oid"]
    dst = os.path.join(SHEETS, f"{oid}.jpg")
    imgs = d.get("images") or []
    if not imgs:
        skipped += 1
        continue
    if not os.path.exists(dst):
        s = build(oid, imgs)
        if s is None:
            skipped += 1
            continue
        s.save(dst, "JPEG", quality=72, optimize=True)
        made += 1
    manifest.append({"oid": oid, "заголовок": d.get("title"),
                     "полотно": f"{absd}/{oid}.jpg", "картинок": len(imgs),
                     "слов": d.get("n_words"),
                     "подписи": [i.get("caption") for i in imgs if i.get("caption")]})

print(f"полотен сделано {made}, всего {len(manifest)}, пропущено {skipped}")
sz = sum(os.path.getsize(os.path.join(SHEETS, x)) for x in os.listdir(SHEETS)) / 1048576
print(f"объём {sz:.0f} МБ, средний файл {sz*1024/max(1,len(manifest)):.0f} КБ")

import hashlib
manifest.sort(key=lambda x: hashlib.md5(x["oid"].encode()).hexdigest())
N = 14
size = -(-len(manifest) // N)
for i in range(N):
    ch = manifest[i * size:(i + 1) * size]
    if ch:
        json.dump(ch, open(f"{BD}/sheets_{i:02d}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
print(f"партий {N} по ~{size} статей, каталог {os.path.abspath(BD)}")
