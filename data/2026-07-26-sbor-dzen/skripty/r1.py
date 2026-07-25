# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1. Верхняя граница возрастного недосчёта дочитываний."""
import pandas as pd, numpy as np, json, os
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
rng = np.random.default_rng(20260726)

m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
CUT = pd.Timestamp('2026-07-25')

def boot_med_ci(x, B=5000):
    x = np.asarray(pd.Series(x).dropna(), float)
    if len(x) == 0: return (np.nan, np.nan, np.nan)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    meds = np.median(x[idx], axis=1)
    return (float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))

print("="*100)
print("ТРЕБОВАНИЕ 1. ВОЗРАСТНОЙ НЕДОСЧЁТ ДОЧИТЫВАНИЙ (эпоха 3_дно, ce=True)")
print("="*100)

# --- насыщенный уровень: эпоха 1, age_days > 550
sat = m[(m['эпоха'] == '1_до_спада') & (m['age_days'] > 550) & m['ce']]
sat_all = m[(m['эпоха'] == '1_до_спада') & (m['age_days'] > 550)]
print(f"\nНАСЫЩЕННЫЙ ЭТАЛОН: эпоха 1, age_days>550, ce=True: n={len(sat)}")
print(f"  даты публикации: {sat['date'].min():%d.%m.%Y} .. {sat['date'].max():%d.%m.%Y}")
cpr_sat = sat['comments_per_read'].median(); lpr_sat = sat['likes_per_read'].median()
spr_sat = sat['subs_per_read'].median()
c1,c2,c3 = boot_med_ci(sat['comments_per_read']); l1,l2,l3 = boot_med_ci(sat['likes_per_read'])
print(f"  медиана comments_per_read = {cpr_sat:.5f}  CI95 [{c2:.5f}; {c3:.5f}]")
print(f"  медиана likes_per_read    = {lpr_sat:.5f}  CI95 [{l2:.5f}; {l3:.5f}]")
print(f"  медиана subs_per_read     = {spr_sat:.5f}")
print(f"  (без фильтра ce: n={len(sat_all)}, cpr={sat_all['comments_per_read'].median():.5f}, lpr={sat_all['likes_per_read'].median():.5f})")

# --- окна возраста внутри эпохи 3
wins = [(0,45),(45,75),(75,110),(110,150),(150,200),(200,270)]
d3 = m[(m['эпоха'] == '3_дно') & m['ce']].copy()
print(f"\nЭпоха 3_дно, ce=True: n={len(d3)}, age_days {d3['age_days'].min()}..{d3['age_days'].max()}")
rows = []
for a,b in wins:
    s = d3[(d3['age_days'] >= a) & (d3['age_days'] < b)]
    if len(s) == 0: continue
    cpr = s['comments_per_read'].median(); lpr = s['likes_per_read'].median()
    spr = s['subs_per_read'].median()
    _,cl,ch = boot_med_ci(s['comments_per_read']); _,ll,lh = boot_med_ci(s['likes_per_read'])
    rows.append(dict(окно=f"{a}-{b}", n=len(s),
        дата_от=f"{s['date'].min():%d.%m.%y}", дата_до=f"{s['date'].max():%d.%m.%y}",
        cpr=cpr, cpr_lo=cl, cpr_hi=ch, mult_cpr=cpr/cpr_sat,
        lpr=lpr, lpr_lo=ll, lpr_hi=lh, mult_lpr=lpr/lpr_sat,
        spr=spr, mult_spr=spr/spr_sat if spr_sat else np.nan,
        med_reads=s['reads'].median(), med_shows=s['shows'].median(),
        med_ctr=s['ctr'].median(), med_rr=s['read_rate'].median()))
t = pd.DataFrame(rows)
print("\nТаблица 1.1. Медианы по окнам возраста (эпоха 3_дно, ce=True)")
print(t[['окно','n','дата_от','дата_до','cpr','cpr_lo','cpr_hi','mult_cpr','lpr','lpr_lo','lpr_hi','mult_lpr']].to_string(
    index=False, float_format=lambda v: f"{v:.4f}"))
print("\nТаблица 1.2. Те же окна: сопутствующие показатели")
print(t[['окно','n','med_shows','med_reads','med_ctr','med_rr','spr','mult_spr']].to_string(
    index=False, float_format=lambda v: f"{v:.4f}"))

print("\nСверка с цифрами критика (cpr): его 0.0683/0.0474/0.0347/0.0183/0.0231/0.0139, эталон 0.0094")
crit = [0.0683,0.0474,0.0347,0.0183,0.0231,0.0139]
for i,r in t.iterrows():
    print(f"  {r['окно']:8s} мой {r['cpr']:.4f}  критик {crit[i]:.4f}  разница {r['cpr']-crit[i]:+.5f}")
print(f"  эталон  мой {cpr_sat:.4f}  критик 0.0094  разница {cpr_sat-0.0094:+.5f}")

# --- ДИАГНОСТИКА А: расходятся ли множители cpr и lpr?
print("\n"+"-"*100)
print("ДИАГНОСТИКА А. Если недосчёт чисто в ЗНАМЕНАТЕЛЕ (reads), множители cpr и lpr обязаны совпасть.")
print("-"*100)
print(t[['окно','n','mult_cpr','mult_lpr','mult_spr']].assign(
    отношение=lambda d: d['mult_cpr']/d['mult_lpr']).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

# --- ДИАГНОСТИКА Б: cpr по возрасту ВНУТРИ эпохи 1 (всё зрелое) => насыщается ли вообще?
print("\n"+"-"*100)
print("ДИАГНОСТИКА Б. cpr/lpr по возрасту ВНУТРИ эпохи 1 (все статьи зрелые, age>360). Если ряд не плоский —")
print("               «насыщенный уровень» не существует, это календарный тренд вовлечённости.")
print("-"*100)
e1 = m[(m['эпоха']=='1_до_спада') & m['ce']]
for a,b in [(270,400),(400,550),(550,700),(700,900),(900,1250)]:
    s = e1[(e1['age_days']>=a)&(e1['age_days']<b)]
    if len(s) < 10:
        print(f"  {a}-{b}: n={len(s)} — меньше 10, вывод не формулируется"); continue
    print(f"  age {a:4d}-{b:4d}: n={len(s):3d}  {s['date'].min():%m.%y}-{s['date'].max():%m.%y}  "
          f"cpr={s['comments_per_read'].median():.5f}  lpr={s['likes_per_read'].median():.5f}  "
          f"reads_med={s['reads'].median():.0f}")

# --- ДИАГНОСТИКА В: скорость набора комментариев по таймстемпам
print("\n"+"-"*100)
print("ДИАГНОСТИКА В. Скорость набора КОММЕНТАРИЕВ по таймстемпам (comments_all.pkl).")
print("               Модель критика требует, чтобы числитель насыщался быстро.")
print("-"*100)
c = pd.read_pickle('out/comments_all.pkl')
c['ts_dt'] = pd.to_datetime(c['ts'], unit='ms')
pub = m.set_index('oid')['date']
c['pub'] = c['oid'].map(pub)
c = c[c['pub'].notna()].copy()
c['age_at_comment'] = (c['ts_dt'] - c['pub']).dt.total_seconds()/86400.0
c = c[c['age_at_comment'] >= -0.5]
# берём только зрелые статьи (age_days>200), чтобы окно наблюдения не резало хвост
mature_oids = set(m[m['age_days']>200]['oid'])
cm = c[c['oid'].isin(mature_oids)]
print(f"  комментариев всего {len(c)}, у зрелых статей (age>200д) {len(cm)} по {cm['oid'].nunique()} статьям")
for d in [1,3,7,14,30,45,60,90,150,200]:
    print(f"   доля комментариев, поступивших за первые {d:3d} дней: {(cm['age_at_comment']<=d).mean():.4f}")
# по статье: медианная доля за 45 дней
g = cm.groupby('oid')['age_at_comment'].agg(lambda s: (s<=45).mean())
print(f"  медианная ПО СТАТЬЯМ доля комментариев за 45 дней: {g.median():.4f} (n статей {len(g)})")
g2 = cm.groupby('oid')['age_at_comment'].agg(lambda s: (s<=110).mean())
print(f"  медианная ПО СТАТЬЯМ доля комментариев за 110 дней: {g2.median():.4f}")

# --- ДИАГНОСТИКА Г: что даёт ценз зрелости age>=110 для дна
print("\n"+"-"*100)
print("ДИАГНОСТИКА Г. Влияние ценза зрелости age_days>=110 на окно «дна» (ce=True)")
print("-"*100)
d3c = d3[d3['age_days']>=110]
print(f"  дно ce=True без ценза: n={len(d3)}, медиана reads={d3['reads'].median():.0f}, shows={d3['shows'].median():.0f}")
print(f"  дно ce=True с цензом  : n={len(d3c)}, медиана reads={d3c['reads'].median():.0f}, shows={d3c['shows'].median():.0f}")
print(f"  ценз отсекает публикации с {d3[d3['age_days']<110]['date'].min():%d.%m.%Y} по {d3[d3['age_days']<110]['date'].max():%d.%m.%Y}")
t.to_pickle('r1_table.pkl')
json.dump({'cpr_sat':cpr_sat,'lpr_sat':lpr_sat}, open('r1_sat.json','w'))
