# -*- coding: utf-8 -*-
import json, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r"C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/themes/публичные_места_транспорт.json"
raw = open(p, encoding='utf-8').read().replace("NaN", "null")
arts = json.loads(raw)["статьи"]
for i, a in enumerate(arts):
    a["id"] = i + 1

groups = {
 "1 Транспорт и дорога": [4,12,17,23,25,31,32,34,40,42,45,51,54],
 "2 Магазины/покупки/услуги": [6,8,10,11,13,19,38,48,50,52],
 "3 Привычки и чувства на людях": [5,22,24,27,28,29,30,35,37,41,44,53,55],
 "  3a жвачка/кофе/дым/запах": [5,29,28,35,41],
 "  3b шум и наушники": [22,24],
 "  3c чувства: поцелуй/ссора/слёзы": [27,44,53],
 "  3d тело и съёмка": [30,37,55],
 "4 Подъезд/лифт/лестница/домофон": [16,18,26,39],
 "5 Культурные площадки": [1,7,15,43,46,47],
 "6 Улица/погода/природа/животные": [2,3,9,21,33,49],
 "7 Память и чужие культуры": [14,20,36],
}

def med(xs): return int(statistics.median(xs)) if xs else None

for name, ids in groups.items():
    sel = [arts[i-1] for i in ids if arts[i-1]["показы"] > 0]
    print(f"\n=== {name} (n={len(ids)}) ===")
    for ep in ["1_до_спада","2_склон","3_дно"]:
        g = [a for a in sel if a["эпоха"]==ep]
        if g:
            print(f"  {ep}: n={len(g)} показы={med([a['показы'] for a in g])} дочит={med([a['дочитывания'] for a in g])} CTR={round(statistics.median([a['CTR'] for a in g]),4)} комм={med([a['комментарии'] for a in g])}")
    print(f"  ИТОГО: показы={med([a['показы'] for a in sel])} дочит={med([a['дочитывания'] for a in sel])}")
    b = max(sel, key=lambda a: a["показы"]); w = min(sel, key=lambda a: a["показы"])
    print(f"  BEST : «{b['заголовок']}» {b['дата']} {b['эпоха']} {b['показы']}/{b['дочитывания']} CTR{b['CTR']} комм{b['комментарии']}")
    print(f"  WORST: «{w['заголовок']}» {w['дата']} {w['эпоха']} {w['показы']}/{w['дочитывания']} CTR{w['CTR']} комм{w['комментарии']}")
