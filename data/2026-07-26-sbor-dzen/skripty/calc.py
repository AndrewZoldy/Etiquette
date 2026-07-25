# -*- coding: utf-8 -*-
import json, statistics, io, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r"C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/themes/публичные_места_транспорт.json"
raw = open(p, encoding='utf-8').read().replace("NaN", "null")
d = json.loads(raw)
arts = d["статьи"]
for i, a in enumerate(arts):
    a["id"] = i + 1

groups = {
 "S1 Транспорт и дорога": [4,12,17,23,25,31,32,34,40,42,45,51,54],
 "  S1a поезд+самолёт": [4,12,23,34],
 "  S1b метро": [17,31,51],
 "  S1c автобус": [54],
 "  S1d за рулём": [25,32,40,42],
 "  S1e пешеход": [45],
 "S2 Магазины и услуги": [6,8,10,11,13,19,38,48,50,52],
 "  S2a одежда/косметика": [8,11,38,52],
 "  S2b продукты": [13,50],
 "  S2c распродажи/ярмарки": [6,48],
 "  S2d сервис": [10,19],
 "S3 Культурные площадки": [1,7,15,43,46,47],
 "S4 Подъезд/лифт/лестница": [16,18,26,39],
 "S5 Шум/запах/привычки": [5,22,24,28,29,35,41],
 "S6 Чувства и тело на публике": [27,30,37,44,53,55],
 "S7 Улица/погода/природа/животные": [2,3,9,21,33,49],
 "S8 Память и чужие культуры": [14,20,36],
}

def med(xs):
    return int(statistics.median(xs)) if xs else None

def show(name, ids, drop_zero=True):
    sel = [arts[i-1] for i in ids]
    if drop_zero:
        sel = [a for a in sel if a["показы"] > 0]
    print(f"\n=== {name} (n={len(ids)}, с данными={len(sel)}) ===")
    for ep in ["1_до_спада", "2_склон", "3_дно"]:
        g = [a for a in sel if a["эпоха"] == ep]
        if g:
            print(f"  {ep}: n={len(g)} мед.показы={med([a['показы'] for a in g])} мед.дочит={med([a['дочитывания'] for a in g])} мед.CTR={round(statistics.median([a['CTR'] for a in g]),4)}")
    print(f"  ВСЕГО: мед.показы={med([a['показы'] for a in sel])} мед.дочит={med([a['дочитывания'] for a in sel])}")
    best = max(sel, key=lambda a: a["показы"])
    worst = min(sel, key=lambda a: a["показы"])
    print(f"  BEST: {best['заголовок']} | {best['дата']} | {best['эпоха']} | {best['показы']} / {best['дочитывания']} / CTR {best['CTR']} / комм {best['комментарии']}")
    print(f"  WORST: {worst['заголовок']} | {worst['дата']} | {worst['эпоха']} | {worst['показы']} / {worst['дочитывания']} / CTR {worst['CTR']} / комм {worst['комментарии']}")
    for a in sorted(sel, key=lambda x: -x["показы"]):
        print(f"    - {a['показы']:>8} / {a['дочитывания']:>7} | {a['эпоха']} | {a['дата']} | {a['функция']:<25} | {a['заголовок']}")

for k, v in groups.items():
    show(k, v)

print("\n\n===== ПО СЦЕНЕ ЦЕЛИКОМ =====")
sel = [a for a in arts if a["показы"] > 0]
for ep in ["1_до_спада", "2_склон", "3_дно"]:
    g = [a for a in sel if a["эпоха"] == ep]
    print(f"{ep}: n={len(g)} мед.показы={med([a['показы'] for a in g])} мед.дочит={med([a['дочитывания'] for a in g])} мед.CTR={round(statistics.median([a['CTR'] for a in g]),4)} мед.комм={med([a['комментарии'] for a in g])}")

print("\n===== ПО ФУНКЦИИ =====")
from collections import defaultdict
f = defaultdict(list)
for a in sel:
    f[(a["функция"], a["эпоха"])].append(a)
for k in sorted(f):
    g = f[k]
    print(f"{k}: n={len(g)} мед.показы={med([a['показы'] for a in g])} мед.дочит={med([a['дочитывания'] for a in g])}")
