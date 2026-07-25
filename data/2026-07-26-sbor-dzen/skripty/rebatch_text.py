"""Пересобрать партии текстов из тех статей, которые ещё не размечены."""
import glob, hashlib, json, os

done = set()
for f in glob.glob("out/marks_text/*.jsonl"):
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                done.add(json.loads(line)["oid"])
            except Exception:
                pass
print("уже размечено:", len(done))

allrec = []
for f in sorted(glob.glob("out/batches_text/text_*.json")):
    if "_r" in os.path.basename(f):
        continue
    allrec.extend(json.load(open(f, encoding="utf-8")))
# уникализируем
seen, uniq = set(), []
for r in allrec:
    if r["oid"] not in seen:
        seen.add(r["oid"])
        uniq.append(r)
todo = [r for r in uniq if r["oid"] not in done]
print("всего статей:", len(uniq), "| осталось разметить:", len(todo))

todo.sort(key=lambda x: hashlib.md5(x["oid"].encode()).hexdigest())
SIZE = 20
N = -(-len(todo) // SIZE)
for i in range(N):
    ch = todo[i * SIZE:(i + 1) * SIZE]
    p = f"out/batches_text/text_r{i:02d}.json"
    json.dump(ch, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    last = os.path.getsize(p) / 1024
print(f"новых партий {N} по {SIZE} статей (~{last:.0f} КБ каждая)")
