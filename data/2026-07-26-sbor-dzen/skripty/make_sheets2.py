"""Пересобрать партии полотен: к каждой картинке приложить текст, рядом с которым она стоит."""
import glob, hashlib, json, os

OUT = "out"
SHEETS = os.path.abspath(os.path.join(OUT, "img", "sheets")).replace("\\", "/")
BD = os.path.join(OUT, "batches_sheets")
os.makedirs(BD, exist_ok=True)


def context(seq, images):
    """Для каждой картинки — абзац до и абзац после (по фактической позиции в статье)."""
    # позиции картинок в последовательности
    out = []
    img_idx = 0
    for i, el in enumerate(seq):
        if el.get("k") != "image":
            continue
        before = ""
        for j in range(i - 1, -1, -1):
            if seq[j].get("k") in ("p", "header", "li", "quote"):
                before = seq[j].get("t") or ""
                break
        after = ""
        for j in range(i + 1, len(seq)):
            if seq[j].get("k") in ("p", "header", "li", "quote"):
                after = seq[j].get("t") or ""
                break
        cap = None
        if img_idx < len(images):
            cap = images[img_idx].get("caption")
        out.append({
            "n": img_idx,
            "текст_перед": before[:400],
            "текст_после": after[:400],
            "подпись": cap,
        })
        img_idx += 1
    return out


manifest = []
for fn in sorted(glob.glob("out/pages/*.json")):
    d = json.load(open(fn, encoding="utf-8"))
    oid = d["oid"]
    imgs = d.get("images") or []
    if not imgs or not os.path.exists(os.path.join(OUT, "img", "sheets", oid + ".jpg")):
        continue
    seq = d.get("sequence") or []
    ctx = context(seq, imgs)
    manifest.append({
        "oid": oid,
        "заголовок": d.get("title"),
        "полотно": f"{SHEETS}/{oid}.jpg",
        "картинок": len(imgs),
        "слов": d.get("n_words"),
        "первый_абзац": (d.get("paragraphs") or [""])[0][:500],
        "последний_абзац": (d.get("paragraphs") or [""])[-1][:400],
        "подзаголовки": d.get("headers") or [],
        "кадры_в_контексте": ctx,
    })

print("статей с полотном и контекстом:", len(manifest))
nctx = sum(len(x["кадры_в_контексте"]) for x in manifest)
print("кадров с текстовым окружением:", nctx)

manifest.sort(key=lambda x: hashlib.md5(x["oid"].encode()).hexdigest())
N = 14
size = -(-len(manifest) // N)
for i in range(N):
    ch = manifest[i * size:(i + 1) * size]
    if ch:
        p = f"{BD}/sheets_{i:02d}.json"
        json.dump(ch, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        last = os.path.getsize(p) / 1024
print(f"партий {N} по ~{size} статей (~{last:.0f} КБ), каталог {os.path.abspath(BD)}")

# пример
ex = manifest[0]
print("\nпример статьи:", ex["заголовок"])
for c in ex["кадры_в_контексте"][:3]:
    print(f"  #{c['n']}: перед = {c['текст_перед'][:110]!r}")
