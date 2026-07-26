# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1: лестница контролей на дочитываниях 2025H1 -> 2026H1 + Оахака + регрессия."""
import pandas as pd, numpy as np
from common import load, wmedian
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)

NB = 4000
SEED = 20260726
m = load()

A = m[m['half'] == '2025H1'].copy()   # база
B = m[m['half'] == '2026H1'].copy()   # дно

print("="*104)
print("ТРЕБОВАНИЕ 1. ЛЕСТНИЦА КОНТРОЛЕЙ, первичная метрика = reads (дочитывания), 2025H1 -> 2026H1")
print("="*104)
print(f"reads: min={m['reads'].min()}, нулей={int((m['reads']==0).sum())}")
print(f"n(2025H1)={len(A)}  n(2026H1)={len(B)}")

rng = np.random.default_rng(SEED)

def ci_ratio(a, b, nb=NB, seed=SEED):
    a = np.asarray(a,float); b = np.asarray(b,float)
    r0 = np.median(a)/np.median(b)
    lr = np.random.default_rng(seed)
    out = np.empty(nb)
    for i in range(nb):
        out[i] = np.median(a[lr.integers(0,len(a),len(a))]) / np.median(b[lr.integers(0,len(b),len(b))])
    return r0, np.percentile(out,2.5), np.percentile(out,97.5)

# ---------------- ступени 1-3 ----------------
steps = []
s1a, s1b = A, B
steps.append(('1. сырьё (все статьи)', s1a, s1b))
s2a, s2b = A[A['ceT']], B[B['ceT']]
steps.append(('2. + только comments_enabled==True', s2a, s2b))
s3a, s3b = s2a[s2a['age_days']>=150], s2b[s2b['age_days']>=150]
steps.append(('3. + ценз зрелости age_days>=150', s3a, s3b))

print("\n" + "-"*104)
print("СТУПЕНИ 1-3: медиана reads и отношение 2025H1/2026H1, бутстрап 4000 ресемплов, CI 95%")
print("-"*104)
rows=[]
for name, a, b in steps:
    r, lo, hi = ci_ratio(a['reads'].values, b['reads'].values)
    rows.append({'ступень':name, 'n 2025H1':len(a), 'n 2026H1':len(b),
                 'мед reads 2025H1':int(np.median(a['reads'])), 'мед reads 2026H1':int(np.median(b['reads'])),
                 'отношение':round(r,2), 'CI_low':round(lo,2), 'CI_high':round(hi,2)})
print(pd.DataFrame(rows).to_string(index=False))
print(f"\nДиапазоны дат после ценза зрелости: 2025H1 {s3a['date'].min().date()}..{s3a['date'].max().date()} | "
      f"2026H1 {s3b['date'].min().date()}..{s3b['date'].max().date()}")
print(f"Ценз age>=150 отрезал в 2026H1: {len(s2b)-len(s3b)} статей из {len(s2b)}")

# ---------------- ступень 4: прямое перевзвешивание ----------------
def reweight(src, tgt, cellcol, minn=5):
    """веса для наблюдений tgt = доля ячейки в src / доля в tgt. Ячейки с n<minn в tgt -> 'прочее'."""
    tgt = tgt.copy(); src = src.copy()
    vc = tgt[cellcol].value_counts()
    keep = set(vc[vc>=minn].index)
    tgt['_c'] = tgt[cellcol].where(tgt[cellcol].isin(keep), 'прочее')
    src['_c'] = src[cellcol].where(src[cellcol].isin(keep), 'прочее')
    ps = src['_c'].value_counts(normalize=True)
    pt = tgt['_c'].value_counts(normalize=True)
    w = tgt['_c'].map(lambda c: (ps.get(c,0.0)/pt[c]) if pt.get(c,0)>0 else 0.0)
    cov = float(sum(ps.get(c,0.0) for c in pt.index))   # какая доля состава src вообще представлена в tgt
    return tgt, w.values, keep, ps, pt, cov

def ci_wratio(a_vals, b_df, b_w, nb=NB, seed=SEED, weighted_side='b', a_df=None):
    """CI отношения median(a)/wmedian(b). Ресемплинг обеих групп; веса переносятся вместе с наблюдением."""
    lr = np.random.default_rng(seed)
    a = np.asarray(a_vals,float); bv = b_df['reads'].values.astype(float); bw = np.asarray(b_w,float)
    out=np.empty(nb)
    for i in range(nb):
        ia = lr.integers(0,len(a),len(a)); ib = lr.integers(0,len(bv),len(bv))
        out[i] = np.median(a[ia]) / max(wmedian(bv[ib], bw[ib]), 1e-9)
    out=out[np.isfinite(out)]
    return np.percentile(out,2.5), np.percentile(out,97.5)

print("\n" + "-"*104)
print("СТУПЕНЬ 4: стандартизация состава прямым перевзвешиванием 2026H1 к составу 2025H1")
print("(на выборке ступени 3: ce=True + age>=150). Ячейка = сцена|функция|порог_входа, n<5 в целевом -> 'прочее'")
print("-"*104)

for cellname, cellcol in [('сцена|функция|порог', 'cell'), ('сцена|функция', 'cell2'), ('сцена', 'сцена')]:
    for df in (m, s3a, s3b):
        pass
    A2 = s3a.copy(); B2 = s3b.copy()
    for d in (A2, B2):
        d['cell2'] = d['сцена'].astype(str)+'|'+d['функция'].astype(str)
    tgt, w, keep, ps, pt, cov = reweight(A2, B2, cellcol)
    wm = wmedian(tgt['reads'].values, w)
    r = np.median(A2['reads'])/wm if wm>0 else np.nan
    lo, hi = ci_wratio(A2['reads'].values, tgt, w)
    print(f"\n[ячейка = {cellname}]  ячеек с n>=5 в 2026H1: {len(keep)}; "
          f"доля состава 2025H1, представленная в 2026H1: {cov*100:.1f}%")
    print(f"  медиана reads 2025H1 (сырая)            = {np.median(A2['reads']):,.0f}")
    print(f"  ВЗВЕШЕННАЯ медиана reads 2026H1 (к 2025H1) = {wm:,.0f}   (сырая была {np.median(B2['reads']):,.0f})")
    print(f"  ОСТАТОЧНОЕ ОТНОШЕНИЕ ЭПОХИ = {r:.2f}x   CI95% [{lo:.2f}; {hi:.2f}]")
    tb = pd.DataFrame({'доля 2025H1,%':(ps*100).round(1),'доля 2026H1,%':(pt*100).round(1)}).fillna(0)
    tb['вес'] = (tb['доля 2025H1,%']/tb['доля 2026H1,%']).round(3)
    tb['n 2026H1'] = tgt['_c'].value_counts()
    tb['мед reads 2026H1'] = tgt.groupby('_c')['reads'].median().round(0)
    print(tb.sort_values('доля 2026H1,%',ascending=False).to_string())

# ---------------- симметричная проверка Оахаки ----------------
print("\n" + "-"*104)
print("СИММЕТРИЧНАЯ ПРОВЕРКА ОАХАКИ: 2025H1 перевзвешено к составу 2026H1")
print("-"*104)
for cellname, cellcol in [('сцена|функция|порог','cell'), ('сцена|функция','cell2'), ('сцена','сцена')]:
    A2 = s3a.copy(); B2 = s3b.copy()
    for d in (A2,B2):
        d['cell2'] = d['сцена'].astype(str)+'|'+d['функция'].astype(str)
    tgt, w, keep, ps, pt, cov = reweight(B2, A2, cellcol)   # источник состава = 2026H1, цель = 2025H1
    wm = wmedian(tgt['reads'].values, w)
    r = wm/np.median(B2['reads'])
    lo, hi = ci_wratio_rev = None, None
    lr = np.random.default_rng(SEED); out=np.empty(NB)
    av = tgt['reads'].values.astype(float); aw=np.asarray(w,float); bv=B2['reads'].values.astype(float)
    for i in range(NB):
        ia=lr.integers(0,len(av),len(av)); ib=lr.integers(0,len(bv),len(bv))
        out[i]= wmedian(av[ia],aw[ia]) / max(np.median(bv[ib]),1e-9)
    lo,hi = np.percentile(out,2.5), np.percentile(out,97.5)
    print(f"\n[ячейка = {cellname}] ячеек n>=5 в 2025H1: {len(keep)}; покрытие состава 2026H1: {cov*100:.1f}%")
    print(f"  ВЗВЕШЕННАЯ медиана reads 2025H1 (к составу 2026H1) = {wm:,.0f}  (сырая {np.median(A2['reads']):,.0f})")
    print(f"  медиана reads 2026H1 (сырая) = {np.median(B2['reads']):,.0f}")
    print(f"  ОСТАТОЧНОЕ ОТНОШЕНИЕ ЭПОХИ = {r:.2f}x   CI95% [{lo:.2f}; {hi:.2f}]")

# ---------------- вариант из задания: взвешенная медиана медиан по сценам ----------------
print("\n" + "-"*104)
print("ВАРИАНТ ЗАДАНИЯ: веса = доли сцен эпохи '1_до_спада', применены к медианам сцен эпохи '3_дно'")
print("(и наоборот). Оба варианта на ce=True; группы <10 наблюдений помечены)")
print("-"*104)
for filt, fname in [(lambda d: d, 'сырьё'), (lambda d: d[d['ceT']], 'ce=True')]:
    E1 = filt(m[m['эпоха']=='1_до_спада']); E3 = filt(m[m['эпоха']=='3_дно'])
    w1 = E1['сцена'].value_counts(normalize=True)
    med3 = E3.groupby('сцена')['reads'].median(); n3 = E3['сцена'].value_counts()
    med1 = E1.groupby('сцена')['reads'].median(); n1 = E1['сцена'].value_counts()
    w3 = E3['сцена'].value_counts(normalize=True)
    common = [s for s in w1.index if s in med3.index]
    std_3_at_1 = wmedian([med3[s] for s in common], [w1[s] for s in common])
    std_1_at_3 = wmedian([med1[s] for s in common], [w3[s] for s in common])
    print(f"\n[{fname}] n(до спада)={len(E1)} n(дно)={len(E3)}")
    print(f"  сырая медиана reads: до спада {E1['reads'].median():,.0f} -> дно {E3['reads'].median():,.0f}  = {E1['reads'].median()/max(E3['reads'].median(),1):.2f}x")
    print(f"  дно со СМЕСЬЮ до спада: {std_3_at_1:,.0f}  => остаточное отношение {E1['reads'].median()/max(std_3_at_1,1):.2f}x")
    print(f"  до спада со СМЕСЬЮ дна: {std_1_at_3:,.0f}  => остаточное отношение {std_1_at_3/max(E3['reads'].median(),1):.2f}x")
    tt = pd.DataFrame({'вес(до спада)':w1.round(3),'мед reads дно':med3.round(0),'n дно':n3,
                       'мед reads до':med1.round(0),'n до':n1,'вес(дно)':w3.round(3)}).fillna(0)
    tt['n<10 дно'] = np.where(tt['n дно']<10,'ДА','')
    print(tt.sort_values('вес(до спада)',ascending=False).to_string())
