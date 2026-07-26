# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load, wmedian, std_weights
m = load()
A1 = m[m['half']=='2025H1']; B1 = m[m['half']=='2026H1']
A2 = A1[A1['ce']==True];     B2 = B1[B1['ce']==True]

def std(A,B,keys,minn=5):
    ka=A[keys].astype(str).agg('|'.join,axis=1); kb=B[keys].astype(str).agg('|'.join,axis=1)
    cnt=kb.value_counts(); keep=set(cnt[cnt>=minn].index)
    Ax=A.copy(); Bx=B.copy()
    Ax['cell2']=ka.where(ka.isin(keep),'ПРОЧЕЕ'); Bx['cell2']=kb.where(kb.isin(keep),'ПРОЧЕЕ')
    return wmedian(Ax['reads'].values)/wmedian(Bx['reads'].values, std_weights(Bx,Ax,'cell2')), len(keep)

print("ПОРЯДОК ОПЕРАЦИЙ: занижает ли неудалённая серия оценку вклада состава?")
print()
r_raw = A1['reads'].median()/B1['reads'].median()
r_ce  = A2['reads'].median()/B2['reads'].median()
for gname, keys in [('сцена',['сцена']),('сцена x функция x порог',['сцена','функция','порог_входа'])]:
    s_raw,k1 = std(A1,B1,keys); s_ce,k2 = std(A2,B2,keys)
    print(f"[сетка {gname}]")
    print(f"  СНАЧАЛА состав (серия НЕ удалена): {r_raw:.2f}x -> {s_raw:.2f}x   "
          f"состав снял {(np.log10(r_raw)-np.log10(s_raw))/np.log10(r_raw)*100:5.1f}% общего лог-разрыва (ячеек {k1})")
    print(f"  СНАЧАЛА серия, потом состав:        {r_raw:.2f}x -> {r_ce:.2f}x -> {s_ce:.2f}x   "
          f"серия {(np.log10(r_raw)-np.log10(r_ce))/np.log10(r_raw)*100:5.1f}%, "
          f"состав ещё {(np.log10(r_ce)-np.log10(s_ce))/np.log10(r_raw)*100:5.1f}% (ячеек {k2})")
    print()
print("Состав сцен, 2026H1: сырьё vs ce=True (доли, %)")
c = pd.DataFrame({'2025H1_ce=True': A2['сцена'].value_counts(normalize=True)*100,
                  '2026H1_сырьё': B1['сцена'].value_counts(normalize=True)*100,
                  '2026H1_ce=True': B2['сцена'].value_counts(normalize=True)*100}).fillna(0).round(1)
print(c.sort_values('2026H1_сырьё',ascending=False).to_string())
