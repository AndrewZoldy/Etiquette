# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 2. Локализация события во времени по двум независимым шкалам."""
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
rng = np.random.default_rng(20260726)

m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['ymS'] = m['ym'].astype(str)

def boot_med_ci(x, B=5000):
    x = np.asarray(pd.Series(x).dropna(), float)
    if len(x) < 2: return (float(np.median(x)) if len(x) else np.nan, np.nan, np.nan)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    meds = np.median(x[idx], axis=1)
    return (float(np.median(x)), float(np.percentile(meds,2.5)), float(np.percentile(meds,97.5)))

months = [f"{y}-{mm:02d}" for y in (2025,2026) for mm in range(1,13)]
months = [x for x in months if '2025-05' <= x <= '2026-07']

# кривая набора комментариев эпохи 3_дно (из r1b) -> доля набранного к возрасту N
curve = {0:0.0, 7:0.620, 14:0.717, 30:0.800, 45:0.822, 75:0.875, 110:0.923, 150:0.957, 200:0.994, 400:1.0}
ck, cv = np.array(sorted(curve)), np.array([curve[k] for k in sorted(curve)])
def share(age): return float(np.interp(min(age,400), ck, cv))

print("="*118)
print("ТРЕБОВАНИЕ 2 (а). МЕСЯЧНЫЕ МЕДИАНЫ shows и reads, ТОЛЬКО ce=True, бутстрап-CI 95%")
print("="*118)
ce = m[m['ce']]
rows=[]
for mo in months:
    s = ce[ce['ymS']==mo]
    sa = m[m['ymS']==mo]
    if len(s)==0: continue
    sh,shl,shh = boot_med_ci(s['shows']); rd,rdl,rdh = boot_med_ci(s['reads'])
    age = s['age_days'].median()
    rows.append(dict(месяц=mo, n_ce=len(s), n_все=len(sa), shows=sh, sh_lo=shl, sh_hi=shh,
                     reads=rd, rd_lo=rdl, rd_hi=rdh, возраст=age, доля=share(age),
                     reads_adj=rd/share(age)))
t = pd.DataFrame(rows)
print(t[['месяц','n_ce','n_все','shows','sh_lo','sh_hi','reads','rd_lo','rd_hi']].to_string(
    index=False, float_format=lambda v: f"{v:,.0f}".replace(',',' ')))
print("\nСверка reads с цифрами критика (авг25..апр26): 16837/14269/4119/5055/2874/5313/5982/4764/3222")
crit = {'2025-08':16837,'2025-09':14269,'2025-10':4119,'2025-11':5055,'2025-12':2874,
        '2026-01':5313,'2026-02':5982,'2026-03':4764,'2026-04':3222}
for k,v in crit.items():
    mine = float(t.loc[t['месяц']==k,'reads'].iloc[0])
    print(f"   {k}: мой {mine:8.0f}  критик {v:8.0f}  {'СОВПАЛО' if abs(mine-v)<1 else 'РАСХОЖДЕНИЕ'}")

print("\nТаблица 2.1б. Те же месяцы с поправкой на незрелость (делим медиану reads на долю набранного")
print("              к медианному возрасту месяца; кривая набора измерена по таймстемпам комментариев эпохи 3):")
print(t[['месяц','n_ce','возраст','доля','reads','reads_adj']].to_string(
    index=False, float_format=lambda v: f"{v:,.3f}".replace(',',' ')))

print("\n"+"="*118)
print("ТРЕБОВАНИЕ 2 (б). МЕСЯЧНЫЕ СУММЫ ДОЧИТЫВАНИЙ по ВСЕМ статьям месяца публикации")
print("="*118)
rows=[]
for mo in months:
    sa = m[m['ymS']==mo]; sc = ce[ce['ymS']==mo]
    if len(sa)==0: continue
    rows.append(dict(месяц=mo, n_все=len(sa), сумма_reads_все=sa['reads'].sum(),
                     n_ce=len(sc), сумма_reads_ce=sc['reads'].sum(),
                     сумма_shows_все=sa['shows'].sum()))
t2 = pd.DataFrame(rows)
t2['млн_все'] = t2['сумма_reads_все']/1e6
t2['млн_ce']  = t2['сумма_reads_ce']/1e6
print(t2[['месяц','n_все','сумма_reads_все','млн_все','n_ce','млн_ce','сумма_shows_все']].to_string(
    index=False, float_format=lambda v: f"{v:,.3f}".replace(',',' ')))
print("\nСверка сумм с критиком: авг25 1.696 млн, дек 0.295, фев26 0.323, апр 0.314, июн 0.340")
for k,v in [('2025-08',1.696),('2025-12',0.295),('2026-02',0.323),('2026-04',0.314),('2026-06',0.340)]:
    mine = float(t2.loc[t2['месяц']==k,'млн_все'].iloc[0])
    print(f"   {k}: мой {mine:.3f} млн  критик {v:.3f} млн  разница {mine-v:+.3f}")

print("\n"+"="*118)
print("ПРОВЕРКА ПРАВИЛА РЕШЕНИЯ: одна ступень? где? какая амплитуда? плато после?")
print("="*118)
print("\nА. Помесячные отношения «предыдущий месяц / текущий» по медиане reads (ce=True):")
prev=None
for _,r in t.iterrows():
    if prev is not None:
        print(f"   {prev['месяц']} -> {r['месяц']}: {prev['reads']:>9,.0f} -> {r['reads']:>9,.0f}   x{prev['reads']/r['reads']:5.2f}".replace(',',' '))
    prev = r
print("\nБ. Уровневые блоки (ce=True), медиана по объединённому пулу месяцев:")
blocks = [('май-июл 2025', ['2025-05','2025-06','2025-07']),
          ('авг-сен 2025', ['2025-08','2025-09']),
          ('окт-дек 2025', ['2025-10','2025-11','2025-12']),
          ('янв-мар 2026', ['2026-01','2026-02','2026-03']),
          ('апр-июл 2026', ['2026-04','2026-05','2026-06','2026-07'])]
res={}
for name, mos in blocks:
    s = ce[ce['ymS'].isin(mos)]
    sh,shl,shh = boot_med_ci(s['shows']); rd,rdl,rdh = boot_med_ci(s['reads'])
    res[name]=(rd,sh)
    print(f"   {name:14s} n={len(s):3d}  shows {sh:>9,.0f} [{shl:>9,.0f};{shh:>10,.0f}]   reads {rd:>8,.0f} [{rdl:>7,.0f};{rdh:>8,.0f}]".replace(',',' '))
print("\nВ. Амплитуда ступени (ce=True):")
print(f"   май-июл2025 -> окт-дек2025: reads x{res['май-июл 2025'][0]/res['окт-дек 2025'][0]:.2f}, shows x{res['май-июл 2025'][1]/res['окт-дек 2025'][1]:.2f}")
print(f"   авг-сен2025 -> окт-дек2025: reads x{res['авг-сен 2025'][0]/res['окт-дек 2025'][0]:.2f}, shows x{res['авг-сен 2025'][1]/res['окт-дек 2025'][1]:.2f}")
print(f"   окт-дек2025 -> янв-мар2026: reads x{res['окт-дек 2025'][0]/res['янв-мар 2026'][0]:.2f}  (>1 = продолжает падать, <1 = восстановление)")
print(f"   янв-мар2026 -> апр-июл2026: reads x{res['янв-мар 2026'][0]/res['апр-июл 2026'][0]:.2f}  (эти месяцы незрелые)")

print("\nГ. Бутстрап-CI отношения блоков по reads (ce=True), 5000 повторов:")
def boot_ratio(a,b,B=5000):
    a=np.asarray(a,float); b=np.asarray(b,float)
    ra=np.median(a[rng.integers(0,len(a),size=(B,len(a)))],axis=1)
    rb=np.median(b[rng.integers(0,len(b),size=(B,len(b)))],axis=1)
    r=ra/rb
    return np.median(a)/np.median(b), np.percentile(r,2.5), np.percentile(r,97.5)
pairs=[('май-июл 2025','окт-дек 2025'),('окт-дек 2025','янв-мар 2026'),('янв-мар 2026','апр-июл 2026')]
for A,B_ in pairs:
    a=ce[ce['ymS'].isin(dict(blocks)[A])]['reads']; b=ce[ce['ymS'].isin(dict(blocks)[B_])]['reads']
    p,lo,hi = boot_ratio(a,b)
    print(f"   {A} / {B_}: {p:.2f}  CI95 [{lo:.2f}; {hi:.2f}]")
    a=ce[ce['ymS'].isin(dict(blocks)[A])]['shows']; b=ce[ce['ymS'].isin(dict(blocks)[B_])]['shows']
    p,lo,hi = boot_ratio(a,b)
    print(f"   {'':{len(A)}s}   shows: {p:.2f}  CI95 [{lo:.2f}; {hi:.2f}]")

print("\nД. ПРОДОЛЖАЕТСЯ ЛИ УБЫВАНИЕ ПОСЛЕ МАРТА 2026 при цензе зрелости (age>=110)?")
cz = ce[ce['age_days']>=110]
for name, mos in blocks:
    s = cz[cz['ymS'].isin(mos)]
    if len(s)<10: print(f"   {name:14s} n={len(s):3d} — меньше 10 после ценза, вывод не формулируется"); continue
    print(f"   {name:14s} n={len(s):3d}  reads {s['reads'].median():>8,.0f}  shows {s['shows'].median():>9,.0f}".replace(',',' '))
print("   (ценз убирает апрель-июль 2026 целиком, поэтому «после марта 2026» на цензурованных данных не проверяемо)")
print("\n   Поэтому проверяю с поправкой на незрелость (reads_adj):")
for name, mos in blocks:
    sub = t[t['месяц'].isin(mos)]
    print(f"   {name:14s} медиана помесячных reads_adj = {sub['reads_adj'].median():>9,.0f}".replace(',',' '))
t.to_pickle('r2_month.pkl')
