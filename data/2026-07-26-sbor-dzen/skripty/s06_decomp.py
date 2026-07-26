# -*- coding: utf-8 -*-
"""Итоговая мультипликативная декомпозиция падения медианы дочитываний."""
import pandas as pd, numpy as np
from common import load, wmedian
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
NB,SEED=4000,20260726
m=load(); m['cell2']=m['сцена'].astype(str)+'|'+m['функция'].astype(str)

def reweight(src,tgt,cc,minn=5):
    tgt=tgt.copy(); src=src.copy()
    vc=tgt[cc].value_counts(); keep=set(vc[vc>=minn].index)
    tgt['_c']=tgt[cc].where(tgt[cc].isin(keep),'прочее'); src['_c']=src[cc].where(src[cc].isin(keep),'прочее')
    ps=src['_c'].value_counts(normalize=True); pt=tgt['_c'].value_counts(normalize=True)
    return tgt, tgt['_c'].map(lambda c:(ps.get(c,0.0)/pt[c]) if pt.get(c,0)>0 else 0.0).values

# --- фактор зрелости, идентифицированный ВНУТРИ одной эпохи на ce=True ---
ce=m[m['ceT']]
c1=ce[(ce['age_days']>=60)&(ce['age_days']<150)]   # 25.02.2026-25.05.2026
c2=ce[(ce['age_days']>=220)&(ce['age_days']<300)]  # 29.09.2025-15.12.2025
age_factor=c2['reads'].median()/c1['reads'].median()
lr=np.random.default_rng(SEED); a=c1['reads'].values.astype(float); b=c2['reads'].values.astype(float)
bs=np.array([np.median(b[lr.integers(0,len(b),len(b))])/max(np.median(a[lr.integers(0,len(a),len(a))]),1e-9) for _ in range(NB)])
print("ФАКТОР ЗРЕЛОСТИ, оценённый ВНУТРИ послеобвального периода (ce=True, обе когорты после 01.11.2025 или на границе):")
print(f"  когорта 60-150 дн  (публ. {c1['date'].min().date()}..{c1['date'].max().date()}) n={len(c1)} мед reads={c1['reads'].median():,.0f}")
print(f"  когорта 220-300 дн (публ. {c2['date'].min().date()}..{c2['date'].max().date()}) n={len(c2)} мед reads={c2['reads'].median():,.0f}")
print(f"  => фактор зрелости = {age_factor:.2f}x  CI95%=[{np.percentile(bs,2.5):.2f};{np.percentile(bs,97.5):.2f}]")
c3=ce[(ce['age_days']>=300)&(ce['age_days']<400)]
print(f"  для контраста когорта 300-400 дн (публ. {c3['date'].min().date()}..{c3['date'].max().date()}, ДО обвала) n={len(c3)} мед reads={c3['reads'].median():,.0f}")
print(f"  => скачок 220-300 -> 300-400 = {c3['reads'].median()/c2['reads'].median():.2f}x — это ГРАНИЦА ЭПОХИ, не возраст")

print("\n"+"="*118)
print("МУЛЬТИПЛИКАТИВНАЯ ДЕКОМПОЗИЦИЯ (медиана дочитываний)")
print("="*118)
for lbl,A,B in [('БАЗА = 2025H1 (пик) -> 2026H1', m[m['half']=='2025H1'], m[m['half']=='2026H1']),
                ('БАЗА = эпоха "до спада" -> эпоха "дно"', m[m['эпоха']=='1_до_спада'], m[m['эпоха']=='3_дно'])]:
    raw=A['reads'].median()/B['reads'].median()
    Ac,Bc=A[A['ceT']],B[B['ceT']]
    after_ce=Ac['reads'].median()/Bc['reads'].median()
    f_ce=raw/after_ce
    res=[]
    for cc in ['cell','cell2','сцена']:
        tgt,w=reweight(Ac,Bc,cc); f_std=after_ce/(Ac['reads'].median()/wmedian(tgt['reads'].values,w))
        tgt2,w2=reweight(Bc,Ac,cc); rev=wmedian(tgt2['reads'].values,w2)/Bc['reads'].median()
        res.append((cc,after_ce/f_std, f_std, rev))
    print(f"\n--- {lbl} ---")
    print(f"  сырое отношение                                  = {raw:6.2f}x")
    print(f"  снятие серии ce=False   (делитель {f_ce:.2f})        = {after_ce:6.2f}x")
    print(f"  снятие фактора зрелости (делитель {age_factor:.2f})        = {after_ce/age_factor:6.2f}x")
    for cc,std_val,f_std,rev in res:
        print(f"  + стандартизация состава [{cc:6s}] делитель {f_std:5.2f} => ОСТАТОК = {std_val/age_factor:6.2f}x   "
              f"(обратная сторона Оахаки: {rev/age_factor:5.2f}x)")

print("\n"+"="*118)
print("ИТОГОВАЯ ВИЛКА ОСТАТОЧНОГО КОЭФФИЦИЕНТА ЭПОХИ")
print("="*118)
vals=[]
for lbl,A,B in [('2025H1->2026H1', m[m['half']=='2025H1'], m[m['half']=='2026H1']),
                ('до спада->дно',  m[m['эпоха']=='1_до_спада'], m[m['эпоха']=='3_дно'])]:
    Ac,Bc=A[A['ceT']],B[B['ceT']]
    for cc in ['cell','cell2','сцена']:
        tgt,w=reweight(Ac,Bc,cc); f=(Ac['reads'].median()/wmedian(tgt['reads'].values,w))/age_factor
        tgt2,w2=reweight(Bc,Ac,cc); r=(wmedian(tgt2['reads'].values,w2)/Bc['reads'].median())/age_factor
        vals += [f,r]
        print(f"  {lbl:16s} ячейка={cc:6s}  прямое={f:5.2f}x  обратное={r:5.2f}x")
print(f"\n  ВИЛКА: {min(vals):.2f}x .. {max(vals):.2f}x ; медиана оценок = {np.median(vals):.2f}x")
print(f"  Цифра критика для ступени 4 (3,95x) НЕ включала фактор зрелости отдельно и опиралась на n=26.")
