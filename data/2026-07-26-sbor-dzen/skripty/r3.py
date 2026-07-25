# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 3. Тест на аномальность базы сравнения."""
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
rng = np.random.default_rng(20260726)

m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['ymS'] = m['ym'].astype(str)

def boot_ratio_stat(a, b, stat, B=5000):
    a = np.asarray(pd.Series(a).dropna(), float); b = np.asarray(pd.Series(b).dropna(), float)
    if len(a) < 2 or len(b) < 2: return (np.nan,)*3
    ra = stat(a[rng.integers(0,len(a),size=(B,len(a)))], axis=1)
    rb = stat(b[rng.integers(0,len(b),size=(B,len(b)))], axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        r = ra/rb
    r = r[np.isfinite(r)]
    return (stat(a)/stat(b), float(np.percentile(r,2.5)), float(np.percentile(r,97.5)))

med = lambda x, axis=None: np.median(x, axis=axis)

print("="*118)
print("ТРЕБОВАНИЕ 3. 2026H1 (ce=True) ПРОТИВ ТРЁХ НЕЗАВИСИМЫХ ДОСПАДОВЫХ ОКОН")
print("="*118)

base = m[m['ce']]
W = {}
for h in ['2023H2','2024H1','2024H2','2025H1','2026H1']:
    W[h] = base[base['half']==h]
# две версии целевого окна
tgt_raw  = base[base['half']=='2026H1']
tgt_cens = base[(base['half']=='2026H1') & (base['age_days']>=110)]
print(f"\n2026H1 ce=True без ценза : n={len(tgt_raw)},  публикации {tgt_raw['date'].min():%d.%m.%Y}-{tgt_raw['date'].max():%d.%m.%Y}")
print(f"2026H1 ce=True ценз>=110д: n={len(tgt_cens)}, публикации {tgt_cens['date'].min():%d.%m.%Y}-{tgt_cens['date'].max():%d.%m.%Y}")
for h in ['2023H2','2024H1','2024H2','2025H1']:
    print(f"{h} ce=True: n={len(W[h])}, все зрелые (мин. возраст {W[h]['age_days'].min()} дн.)")

metrics = [('shows','медиана показов'),('opens','медиана открытий'),('reads','медиана дочитываний'),
           ('ctr','медиана CTR'),('read_rate','медиана дочитываемости')]

for tname, tgt in [('2026H1 ce=True БЕЗ ценза', tgt_raw), ('2026H1 ce=True ЦЕНЗ age>=110', tgt_cens)]:
    print("\n" + "="*118)
    print(f"ЦЕЛЕВОЕ ОКНО: {tname} (n={len(tgt)})")
    print("="*118)
    print(f"{'окно':8s} {'n':>4s} | " + " | ".join(f"{lbl:>34s}" for _,lbl in metrics[:3]))
    for h in ['2023H2','2024H1','2024H2','2025H1']:
        w = W[h]; cells=[]
        for col,_ in metrics[:3]:
            p,lo,hi = boot_ratio_stat(w[col], tgt[col], med)
            cells.append(f"{w[col].median():>9,.0f}/{tgt[col].median():>7,.0f} x{p:5.2f}[{lo:4.2f};{hi:5.2f}]".replace(',',' '))
        print(f"{h:8s} {len(w):4d} | " + " | ".join(cells))
    print()
    print(f"{'окно':8s} {'n':>4s} | " + " | ".join(f"{lbl:>32s}" for _,lbl in metrics[3:]) + " |  доля shows>320k")
    for h in ['2023H2','2024H1','2024H2','2025H1']:
        w = W[h]; cells=[]
        for col,_ in metrics[3:]:
            p,lo,hi = boot_ratio_stat(w[col], tgt[col], med)
            cells.append(f"{w[col].median():>7.4f}/{tgt[col].median():.4f} x{p:5.2f}[{lo:4.2f};{hi:5.2f}]")
        sa = (w['shows']>320000).mean(); sb = (tgt['shows']>320000).mean()
        # бутстрап CI для отношения долей
        A=(w['shows']>320000).values.astype(float); Bv=(tgt['shows']>320000).values.astype(float)
        ra=A[rng.integers(0,len(A),size=(5000,len(A)))].mean(axis=1); rb=Bv[rng.integers(0,len(Bv),size=(5000,len(Bv)))].mean(axis=1)
        rr=(ra/rb); rr=rr[np.isfinite(rr)]
        cells.append(f"{sa:.3f}/{sb:.3f} x{sa/sb:5.2f}[{np.percentile(rr,2.5):4.2f};{np.percentile(rr,97.5):5.2f}]")
        print(f"{h:8s} {len(w):4d} | " + " | ".join(cells))

print("\n" + "="*118)
print("ПРОВЕРКА ПРАВИЛА РЕШЕНИЯ: содержит ли CI отношения единицу (по shows / opens / reads)")
print("="*118)
for tname, tgt in [('без ценза', tgt_raw), ('ценз age>=110', tgt_cens)]:
    print(f"\n  целевое окно 2026H1 ce=True, {tname}:")
    for h in ['2023H2','2024H1','2024H2','2025H1']:
        w = W[h]; flags=[]
        for col in ['shows','opens','reads']:
            p,lo,hi = boot_ratio_stat(w[col], tgt[col], med)
            flags.append(f"{col}: x{p:.2f} CI[{lo:.2f};{hi:.2f}] {'СОДЕРЖИТ 1' if lo<=1<=hi else ('>1' if lo>1 else '<1')}")
        n1 = sum('СОДЕРЖИТ 1' in f for f in flags)
        print(f"    {h}: " + " | ".join(flags) + f"   -> единицу содержат {n1} метрики из 3")

print("\n" + "="*118)
print("СКОС mean/median по reads (проверка утверждения критика 23,96 против 7,74)")
print("="*118)
for h in ['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']:
    w = W[h]
    if len(w)<10: continue
    print(f"  {h} ce=True n={len(w):3d}: mean={w['reads'].mean():>10,.0f} median={w['reads'].median():>8,.0f} skew_ratio={w['reads'].mean()/w['reads'].median():6.2f}".replace(',',' '))
w = tgt_cens
print(f"  2026H1 ce=True ЦЕНЗ n={len(w):3d}: mean={w['reads'].mean():>10,.0f} median={w['reads'].median():>8,.0f} skew_ratio={w['reads'].mean()/w['reads'].median():6.2f}".replace(',',' '))

print("\n" + "="*118)
print("ДОП. МЕСЯЧНЫЕ СУММЫ ДОЧИТЫВАНИЙ ЗА ВСЮ ИСТОРИЮ (шкала «б» из требования 2, вся выборка)")
print("="*118)
g = m.groupby('ymS').agg(n=('reads','size'), sum_reads=('reads','sum'), sum_shows=('shows','sum'))
g['млн_reads'] = g['sum_reads']/1e6
print(g[['n','млн_reads','sum_shows']].to_string(float_format=lambda v: f"{v:,.3f}".replace(',',' ')))
print("\n  Медианы месячных СУММ дочитываний по блокам:")
def blk(a,b,label):
    s = g.loc[(g.index>=a)&(g.index<=b),'млн_reads']
    print(f"   {label:22s} ({a}..{b}) мес={len(s):2d}  медиана={s.median():.3f} млн  мин={s.min():.3f} макс={s.max():.3f}")
    return s.median()
b1=blk('2023-07','2023-12','2023H2')
b2=blk('2024-01','2024-06','2024H1')
b3=blk('2024-07','2024-12','2024H2')
b4=blk('2025-01','2025-07','пик 2025 янв-июл')
b5=blk('2025-12','2026-06','плато дек25-июн26')
print(f"\n   отношение пик/плато по СУММАМ: x{b4/b5:.2f}")
print(f"   отношение 2024H1/плато    : x{b2/b5:.2f}")
print(f"   отношение 2023H2/плато    : x{b1/b5:.2f}")
print(f"   отношение 2024H2/плато    : x{b3/b5:.2f}")
