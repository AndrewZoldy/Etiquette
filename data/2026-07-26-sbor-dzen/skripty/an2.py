import json, sys, io, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/themes/стол_еда.json'
s = open(p, encoding='utf-8').read().replace(': NaN', ': null')
arts = json.loads(s)['статьи']

groups = {
 'A1 Как есть: основные блюда': [11,36,13,14,38,51,52,31,57,110,113,114,119,97,35,108,111],
 'A2 Как есть: десерты/фрукты/яйца': [6,55,56,132,122,50,53,58,120,99,100],
 'B1 Чай и кофе': [2,9,12,26,49,60,94,106,107,125,135],
 'B2 Алкоголь, вино, тосты, бокалы': [25,33,64,69,72,76,77,79,83,84,85,86,87,90,95,116,118,123],
 'C1 Диковинные приборы': [15,16,19,20,21,28,37,39,41,45],
 'C2 Правила обращения с приборами': [43,48,73,75,96,103,117,124,127,128],
 'D Сервировка и посуда': [0,1,17,29,46,82,88,91,93,102,121,126],
 'E Ресторан и общепит': [8,24,40,47,59,61,62,63,78,109,115,133,134],
 'F Поведение и манеры за столом': [22,23,30,42,44,66,67,70,80,98,112,129,130],
 'G Праздничный и домашний стол': [4,32,34,68,74,81,89,92,101,104],
 'H Своды правил и смысл этикета': [5,27,65,71,131],
 'I Гастрокультура и история': [3,7,10,18,54,105],
}

allidx = []
for v in groups.values(): allidx += v
assert len(allidx) == 136, len(allidx)
assert len(set(allidx)) == 136, sorted([x for x in set(allidx) if allidx.count(x)>1])

def med(xs): return int(statistics.median(xs)) if xs else None

for g, idxs in groups.items():
    rows = [arts[i] for i in idxs]
    print('='*90)
    print(f'{g}  — всего {len(rows)}')
    for ep in ['1_до_спада','2_склон','3_дно']:
        sub = [r for r in rows if r['эпоха']==ep]
        if not sub: continue
        print(f'   {ep}: n={len(sub)} медиана показы={med([r["показы"] for r in sub])} '
              f'дочит={med([r["дочитывания"] for r in sub])} '
              f'мед.комм={med([r["комментарии"] for r in sub])}')
    print(f'   ВСЕГО: медиана показы={med([r["показы"] for r in rows])} дочит={med([r["дочитывания"] for r in rows])}')
    srt = sorted(rows, key=lambda r: -r['показы'])
    print(f'   ЛУЧШАЯ: {srt[0]["заголовок"]} ({srt[0]["дата"]}, {srt[0]["эпоха"]}) — {srt[0]["показы"]} показов, {srt[0]["дочитывания"]} дочит')
    print(f'   ХУДШАЯ: {srt[-1]["заголовок"]} ({srt[-1]["дата"]}, {srt[-1]["эпоха"]}) — {srt[-1]["показы"]} показов, {srt[-1]["дочитывания"]} дочит')
    # лучшая на дне
    dno = [r for r in rows if r['эпоха']=='3_дно']
    if dno:
        d = sorted(dno, key=lambda r: -r['показы'])[0]
        print(f'   ЛУЧШАЯ НА ДНЕ: {d["заголовок"]} — {d["показы"]} / {d["дочитывания"]}')
    for r in sorted(rows, key=lambda r: r['дата']):
        print(f'      {r["дата"]} {r["эпоха"][:1]} {r["показы"]:>9} {r["дочитывания"]:>7} {r["функция"][:12]:<12} {r["заголовок"]}')

print('#'*90)
# сцена целиком по эпохам
for ep in ['1_до_спада','2_склон','3_дно']:
    sub=[r for r in arts if r['эпоха']==ep]
    print(ep, 'n=',len(sub),'мед.показы=',med([r['показы'] for r in sub]),'мед.дочит=',med([r['дочитывания'] for r in sub]))
# функции на дне
print('--- по функциям на дне ---')
for f in set(r['функция'] for r in arts):
    sub=[r for r in arts if r['эпоха']=='3_дно' and r['функция']==f]
    if sub: print(f, 'n=',len(sub),'мед.показы=',med([r['показы'] for r in sub]),'мед.дочит=',med([r['дочитывания'] for r in sub]))
print('--- порог на дне ---')
for f in set(r['порог'] for r in arts):
    sub=[r for r in arts if r['эпоха']=='3_дно' and r['порог']==f]
    if sub: print(f, 'n=',len(sub),'мед.показы=',med([r['показы'] for r in sub]))
print('--- дно: топ-12 ---')
for r in sorted([r for r in arts if r['эпоха']=='3_дно'], key=lambda r:-r['показы'])[:14]:
    print(f'  {r["показы"]:>9} {r["дочитывания"]:>7} {r["функция"][:12]:<12} {r["заголовок"]}')
