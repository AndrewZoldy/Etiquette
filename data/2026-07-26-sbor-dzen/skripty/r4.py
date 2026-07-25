# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 4. Тематическое обвинение на чистой выборке + стандартизация смеси."""
import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
rng = np.random.default_rng(20260726)
m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')

def bootci(x,B=5000):
    x=np.asarray(pd.Series(x).dropna(),float)
    if len(x)<2: return (np.nan,np.nan)
    r=np.median(x[rng.integers(0,len(x),size=(B,len(x)))],axis=1)
    return float(np.percentile(r,2.5)), float(np.percentile(r,97.5))

print("="*120)
print("ТРЕБОВАНИЕ 4-A. ИНДЕКС СЦЕНЫ К МЕДИАНЕ СВОЕЙ ЭПОХИ, ТОЛЬКО ce=True, n>=10")
print("   индекс = медиана(сцена внутри эпохи) / медиана(вся эпоха, ce=True)")
print("="*120)
res={}
for ep in ['1_до_спада','3_дно']:
    E = m[(m['эпоха']==ep) & m['ce']]
    mr, ms = E['reads'].median(), E['shows'].median()
    print(f"\nЭПОХА {ep}: ce=True n={len(E)}; медиана эпохи reads={mr:,.0f}, shows={ms:,.0f}".replace(',',' '))
    print(f"  (для справки: без фильтра ce n={len(m[m['эпоха']==ep])}, медиана reads={m[m['эпоха']==ep]['reads'].median():,.0f})".replace(',',' '))
    print(f"  {'сцена':26s} {'n':>4s} {'мед.reads':>11s} {'инд.reads':>10s} {'CI95 инд.reads':>20s} {'мед.shows':>11s} {'инд.shows':>10s}")
    for sc, g in E.groupby('сцена'):
        if len(g) < 10:
            continue
        lo,hi = bootci(g['reads'])
        res[(ep,sc)] = dict(n=len(g), reads=g['reads'].median(), ir=g['reads'].median()/mr,
                            shows=g['shows'].median(), ish=g['shows'].median()/ms)
        print(f"  {sc:26s} {len(g):4d} {g['reads'].median():11,.0f} {g['reads'].median()/mr:10.2f} [{lo/mr:8.2f};{hi/mr:8.2f}] {g['shows'].median():11,.0f} {g['shows'].median()/ms:10.2f}".replace(',',' '))
    skipped = [(sc,len(g)) for sc,g in E.groupby('сцена') if len(g)<10]
    print(f"  не выводятся (n<10): {skipped}")

print("\n"+"-"*120)
print("СВЕРКА С КРИТИКОМ по стол_еда: индекс reads 1,71 (до спада, n=61) -> 2,54 (дно, n=17); индекс shows 1,66 -> 1,60")
for ep in ['1_до_спада','3_дно']:
    r = res.get((ep,'стол_еда'))
    if r: print(f"   {ep:12s} n={r['n']:3d} индекс reads={r['ir']:.2f} индекс shows={r['ish']:.2f}")

print("\n"+"="*120)
print("ТРЕБОВАНИЕ 4-Б. ВНУТРИСЦЕНОВАЯ ДИНАМИКА стол_еда ПО ПОЛУГОДИЯМ, ce=True (n>=10)")
print("="*120)
print(f"  {'полугодие':10s} {'n_все':>6s} {'n_ce':>5s} {'мед.reads ce':>13s} {'CI95':>22s} {'мед.shows ce':>13s} {'мед.reads ВСЕ':>14s}")
se_hist={}
for h in ['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']:
    a = m[(m['half']==h)&(m['сцена']=='стол_еда')]
    g = a[a['ce']]
    if len(g)<10:
        print(f"  {h:10s} {len(a):6d} {len(g):5d}  -- меньше 10 на ce=True, вывод не формулируется (мед.reads ВСЕ={a['reads'].median():,.0f})".replace(',',' '))
        continue
    lo,hi=bootci(g['reads']); se_hist[h]=g['reads'].median()
    print(f"  {h:10s} {len(a):6d} {len(g):5d} {g['reads'].median():13,.0f} [{lo:9,.0f};{hi:10,.0f}] {g['shows'].median():13,.0f} {a['reads'].median():14,.0f}".replace(',',' '))
print("\n  Отношения внутри сцены стол_еда (ce=True) и сравнение с каналом целиком (ce=True):")
ch={}
for h in ['2024H1','2024H2','2025H1','2026H1']:
    ch[h]=m[(m['half']==h)&m['ce']]['reads'].median()
for a,b in [('2025H1','2026H1'),('2024H1','2026H1'),('2024H2','2026H1')]:
    if a in se_hist and b in se_hist:
        print(f"   стол_еда {a}/{b}: x{se_hist[a]/se_hist[b]:6.2f}   |  канал целиком {a}/{b}: x{ch[a]/ch[b]:6.2f}"
              f"   -> тема падает {'МЕДЛЕННЕЕ' if se_hist[a]/se_hist[b] < ch[a]/ch[b] else 'БЫСТРЕЕ'} канала")

print("\n"+"="*120)
print("ТРЕБОВАНИЕ 4-В. СКОЛЬКО ИЗ ПРОВАЛА стол_еда СОЗДАНО ПОДПРОДУКТОМ ce=False")
print("="*120)
for h in ['2025H1','2025H2','2026H1']:
    a = m[(m['half']==h)&(m['сцена']=='стол_еда')]
    t_ = a[a['ce']]; f_ = a[~a['ce']]
    print(f"  {h}: всего n={len(a):3d} | ce=True n={len(t_):3d} мед.reads={t_['reads'].median() if len(t_) else float('nan'):>8,.0f} мед.shows={t_['shows'].median() if len(t_) else float('nan'):>9,.0f}"
          f" | ce=False n={len(f_):3d} мед.reads={f_['reads'].median() if len(f_) else float('nan'):>7,.0f} мед.shows={f_['shows'].median() if len(f_) else float('nan'):>8,.0f}".replace(',',' '))
print("\n  Медиана по СМЕСИ (как в Факте 8 досье) против медианы по ce=True:")
for h in ['2025H1','2025H2','2026H1']:
    a = m[(m['half']==h)&(m['сцена']=='стол_еда')]
    print(f"   {h}: смесь shows={a['shows'].median():>9,.0f}  ce=True shows={a[a['ce']]['shows'].median():>9,.0f}  отношение x{a[a['ce']]['shows'].median()/a['shows'].median():.2f}".replace(',',' '))

print("\n"+"="*120)
print("ТРЕБОВАНИЕ 4-Г. СТАНДАРТИЗАЦИЯ: сколько падения даёт СМЕНА СМЕСИ, сколько — СМЕНА РАЗДАЧИ")
print("   прямая стандартизация: медиана эпохи оценивается как sum_s w_s * med_s (взвешенная по сценам)")
print("="*120)
for flt, lab in [(m['ce'], 'ce=True'), (m['ce'] | ~m['ce'], 'ВСЯ ВЫБОРКА')]:
    E1 = m[(m['эпоха']=='1_до_спада') & flt]; E3 = m[(m['эпоха']=='3_дно') & flt]
    scenes = sorted(set(E1['сцена']) | set(E3['сцена']))
    w1 = E1['сцена'].value_counts(normalize=True); w3 = E3['сцена'].value_counts(normalize=True)
    med1 = E1.groupby('сцена')['reads'].median(); med3 = E3.groupby('сцена')['reads'].median()
    # используем только сцены, где n>=10 в ОБЕИХ эпохах; остальные в «прочее_объединённое»
    n1 = E1['сцена'].value_counts(); n3 = E3['сцена'].value_counts()
    ok = [s for s in scenes if n1.get(s,0)>=10 and n3.get(s,0)>=10]
    print(f"\n  --- {lab} --- сцены с n>=10 в обеих эпохах: {ok}")
    print(f"      покрытие: эпоха1 {w1[ok].sum():.1%} статей, эпоха3 {w3[ok].sum():.1%} статей")
    W1 = w1[ok]/w1[ok].sum(); W3 = w3[ok]/w3[ok].sum()
    A = float((W1*med1[ok]).sum()); B = float((W3*med3[ok]).sum())
    CF = float((W1*med3[ok]).sum())   # смесь эпохи 1, раздача эпохи 3
    CF2 = float((W3*med1[ok]).sum())  # смесь эпохи 3, раздача эпохи 1
    print(f"      {'сцена':26s} {'доля Э1':>8s} {'доля Э3':>8s} {'мед.reads Э1':>13s} {'мед.reads Э3':>13s}")
    for s in ok:
        print(f"      {s:26s} {W1[s]:8.3f} {W3[s]:8.3f} {med1[s]:13,.0f} {med3[s]:13,.0f}".replace(',',' '))
    print(f"      наблюдаемый взвеш. уровень эпохи 1 : {A:12,.0f}".replace(',',' '))
    print(f"      наблюдаемый взвеш. уровень эпохи 3 : {B:12,.0f}".replace(',',' '))
    print(f"      общее падение                      : x{A/B:.2f}")
    print(f"      контрфакт «смесь Э1 + раздача Э3»  : {CF:12,.0f}  -> вклад ТОЛЬКО раздачи: x{A/CF:.2f}".replace(',',' '))
    print(f"      контрфакт «смесь Э3 + раздача Э1»  : {CF2:12,.0f}  -> вклад ТОЛЬКО смеси : x{A/CF2:.2f}".replace(',',' '))
    print(f"      разложение: раздача x{A/CF:.2f} * смесь x{CF/B:.2f} = x{A/B:.2f}")
