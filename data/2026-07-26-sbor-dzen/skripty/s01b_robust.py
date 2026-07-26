# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1, часть Б: устойчивость ступени 4 на выборках с достаточным n + регрессии."""
import pandas as pd, numpy as np
from common import load, wmedian
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
NB, SEED = 4000, 20260726
m = load()

def ci_ratio(a,b,nb=NB,seed=SEED):
    a=np.asarray(a,float); b=np.asarray(b,float); lr=np.random.default_rng(seed); out=np.empty(nb)
    for i in range(nb): out[i]=np.median(a[lr.integers(0,len(a),len(a))])/max(np.median(b[lr.integers(0,len(b),len(b))]),1e-9)
    return np.median(a)/max(np.median(b),1e-9), np.percentile(out,2.5), np.percentile(out,97.5)

def reweight(src,tgt,cellcol,minn=5):
    tgt=tgt.copy(); src=src.copy()
    vc=tgt[cellcol].value_counts(); keep=set(vc[vc>=minn].index)
    tgt['_c']=tgt[cellcol].where(tgt[cellcol].isin(keep),'прочее')
    src['_c']=src[cellcol].where(src[cellcol].isin(keep),'прочее')
    ps=src['_c'].value_counts(normalize=True); pt=tgt['_c'].value_counts(normalize=True)
    w=tgt['_c'].map(lambda c:(ps.get(c,0.0)/pt[c]) if pt.get(c,0)>0 else 0.0)
    return tgt,w.values,keep,ps,pt

def std_pair(A,B,cellcol,label):
    """Возвращает прямое и обратное остаточное отношение с CI."""
    tgt,w,keep,ps,pt = reweight(A,B,cellcol)
    wmB = wmedian(tgt['reads'].values,w)
    rF = np.median(A['reads'])/max(wmB,1e-9)
    lr=np.random.default_rng(SEED); out=np.empty(NB)
    av=A['reads'].values.astype(float); bv=tgt['reads'].values.astype(float); bw=np.asarray(w,float)
    for i in range(NB):
        ia=lr.integers(0,len(av),len(av)); ib=lr.integers(0,len(bv),len(bv))
        out[i]=np.median(av[ia])/max(wmedian(bv[ib],bw[ib]),1e-9)
    loF,hiF=np.percentile(out,2.5),np.percentile(out,97.5)
    tgt2,w2,keep2,ps2,pt2 = reweight(B,A,cellcol)
    wmA = wmedian(tgt2['reads'].values,w2)
    rR = wmA/max(np.median(B['reads']),1e-9)
    lr=np.random.default_rng(SEED); out=np.empty(NB)
    av2=tgt2['reads'].values.astype(float); aw2=np.asarray(w2,float); bv2=B['reads'].values.astype(float)
    for i in range(NB):
        ia=lr.integers(0,len(av2),len(av2)); ib=lr.integers(0,len(bv2),len(bv2))
        out[i]=wmedian(av2[ia],aw2[ia])/max(np.median(bv2[ib]),1e-9)
    loR,hiR=np.percentile(out,2.5),np.percentile(out,97.5)
    return dict(вариант=label, ячейка=cellcol, ячеек_n5_в_B=len(keep), ячеек_n5_в_A=len(keep2),
                nA=len(A), nB=len(B),
                медA=int(np.median(A['reads'])), медB=int(np.median(B['reads'])),
                взвешB=int(wmB), прямое=round(rF,2), CI_пр=f"[{loF:.2f};{hiF:.2f}]",
                взвешA=int(wmA), обратное=round(rR,2), CI_обр=f"[{loR:.2f};{hiR:.2f}]")

m['cell2']=m['сцена'].astype(str)+'|'+m['функция'].astype(str)

print("="*110)
print("A. ДИАГНОСТИКА: почему ступень 4 в формулировке критика не идентифицируется")
print("="*110)
B3 = m[(m['half']=='2026H1') & m['ceT'] & (m['age_days']>=150)]
print(f"Выборка ступени 3 для 2026H1: n={len(B3)}, окно публикаций {B3['date'].min().date()}..{B3['date'].max().date()}")
print("Размеры ячеек сцена|функция|порог в этой выборке:")
print(B3['cell'].value_counts().to_string())
print(f"=> ячеек с n>=5: {(B3['cell'].value_counts()>=5).sum()}. Все ячейки схлопываются в 'прочее', "
      f"веса становятся 1, стандартизация НЕ ПРОИСХОДИТ.")
print("\nРазмеры ячеек сцена|функция:"); print(B3['cell2'].value_counts().to_string())
print("\nРазмеры ячеек сцена:"); print(B3['сцена'].value_counts().to_string())

print("\n" + "="*110)
print("B. СТУПЕНЬ 4 НА ВЫБОРКАХ С ДОСТАТОЧНЫМ n: разные определения ячейки и разные окна")
print("="*110)
variants = []
# (1) как просил критик
A1 = m[(m['half']=='2025H1') & m['ceT'] & (m['age_days']>=150)]
variants.append(('2025H1 -> 2026H1, ce=T, age>=150 (как просил критик)', A1, B3))
# (2) без ценза зрелости (n больше)
A2 = m[(m['half']=='2025H1') & m['ceT']]
B2 = m[(m['half']=='2026H1') & m['ceT']]
variants.append(('2025H1 -> 2026H1, ce=T, без ценза', A2, B2))
# (3) эпохи, ce=T, с цензом зрелости для дна
A3 = m[(m['эпоха']=='1_до_спада') & m['ceT']]
B3b = m[(m['эпоха']=='3_дно') & m['ceT'] & (m['age_days']>=150)]
variants.append(('до спада -> дно, ce=T, age>=150 (дно = ноя25-фев26)', A3, B3b))
# (4) эпохи, ce=T, без ценза
B4 = m[(m['эпоха']=='3_дно') & m['ceT']]
variants.append(('до спада -> дно, ce=T, без ценза', A3, B4))
# (5) эпохи, сырьё (для контраста: что даёт стандартизация БЕЗ снятия ce=False)
A5 = m[m['эпоха']=='1_до_спада']; B5 = m[m['эпоха']=='3_дно']
variants.append(('до спада -> дно, СЫРЬЁ (ce=False внутри)', A5, B5))

rows=[]
for lbl,A,B in variants:
    for cc in ['cell','cell2','сцена']:
        rows.append(std_pair(A,B,cc,lbl))
r = pd.DataFrame(rows)
print(r[['вариант','ячейка','nA','nB','ячеек_n5_в_B','медA','медB','взвешB','прямое','CI_пр','взвешA','обратное','CI_обр']].to_string(index=False))

print("\n" + "="*110)
print("C. ГДЕ СИДИТ 'ЭФФЕКТ СОСТАВА': стол_еда на дне с разбивкой по ce")
print("="*110)
d = m[m['эпоха']=='3_дно']
t = d.groupby(['сцена','ceF'])['reads'].agg(['size','median']).unstack()
print(t.to_string())
se = d[d['сцена']=='стол_еда']
print(f"\nстол_еда на дне: всего {len(se)}; ce=False {int(se['ceF'].sum())} ({se['ceF'].mean()*100:.1f}%); ce=True {int(se['ceT'].sum())}")
print(f"  медиана reads: ce=False {se[se['ceF']]['reads'].median():,.0f} (n={int(se['ceF'].sum())})  |  ce=True {se[se['ceT']]['reads'].median():,.0f} (n={int(se['ceT'].sum())})")
print(f"  медиана reads стол_еда до спада (ce=True): {m[(m['эпоха']=='1_до_спада')&(m['сцена']=='стол_еда')&m['ceT']]['reads'].median():,.0f}")
print("\nДоля ce=False внутри 'дна' по сценам:")
print(d.groupby('сцена')['ceF'].agg(['size','sum','mean']).rename(columns={'size':'n','sum':'ce=False','mean':'доля'}).sort_values('доля',ascending=False).to_string())
