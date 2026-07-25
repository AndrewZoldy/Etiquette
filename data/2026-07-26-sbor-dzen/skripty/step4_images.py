"""Шаг 4: скачать обложки и все внутренние иллюстрации, привести к компактному виду для разбора зрением."""
import glob, io, json, os, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from dzenlib import Dzen, jsonl_read

OUT = "out"
IMGDIR = os.path.join(OUT, "img")
COVDIR = os.path.join(IMGDIR, "covers")
BODYDIR = os.path.join(IMGDIR, "body")
for p in (COVDIR, BODYDIR):
    os.makedirs(p, exist_ok=True)

MAXSIDE = 900
QUALITY = 80
tl = threading.local()


def sess():
    if not hasattr(tl, "d"):
        tl.d = Dzen()
    return tl.d


def save_small(raw, path):
    im = Image.open(io.BytesIO(raw))
    im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > MAXSIDE:
        k = MAXSIDE / max(w, h)
        im = im.resize((int(w * k), int(h * k)), Image.LANCZOS)
    im.save(path, "JPEG", quality=QUALITY, optimize=True)
    return im.size


def build_tasks():
    pubs = {p["oid"]: p for p in jsonl_read(os.path.join(OUT, "publications.jsonl"))}
    tasks = []
    for f in glob.glob(os.path.join(OUT, "pages", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        oid = d["oid"]
        imgs = d.get("images") or []
        cover_id = imgs[0]["id"] if imgs else None
        p = pubs.get(oid) or {}
        cov_url = p.get("cover_url")
        # обложка
        if cov_url:
            tasks.append(("cover", oid, cover_id or "cover", cov_url,
                          os.path.join(COVDIR, f"{oid}.jpg")))
        # внутренние (все, включая первую — она же обложка, но нужна в контексте статьи)
        for k, im in enumerate(imgs):
            tasks.append(("body", oid, im["id"], im["url"],
                          os.path.join(BODYDIR, f"{oid}_{k:02d}_{im['id']}.jpg")))
    return tasks


def main():
    tasks = build_tasks()
    todo = [t for t in tasks if not os.path.exists(t[4])]
    print(f"всего файлов {len(tasks)}, качать {len(todo)}", flush=True)
    lock = threading.Lock()
    st = {"ok": 0, "fail": 0, "bytes": 0}

    def worker(t):
        kind, oid, iid, url, path = t
        try:
            raw = sess().get(url, timeout=60, binary=True, tries=3)
            save_small(raw, path)
            with lock:
                st["ok"] += 1
                st["bytes"] += os.path.getsize(path)
                if st["ok"] % 200 == 0:
                    print(f"  {st['ok']}/{len(todo)} ok, fail={st['fail']}, "
                          f"{st['bytes']/1048576:.0f} МБ", flush=True)
        except Exception as e:
            with lock:
                st["fail"] += 1
                if st["fail"] <= 12:
                    print(f"  FAIL {kind} {oid} {iid} {type(e).__name__}", flush=True)
        time.sleep(0.05 + random.random() * 0.1)

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(worker, todo))

    print(f"ГОТОВО ok={st['ok']} fail={st['fail']} "
          f"covers={len(os.listdir(COVDIR))} body={len(os.listdir(BODYDIR))} "
          f"{st['bytes']/1048576:.0f} МБ", flush=True)


if __name__ == "__main__":
    main()
