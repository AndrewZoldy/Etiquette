# -*- coding: utf-8 -*-
"""Поиск спецификации, воспроизводящей цифры критика -1.012/-0.699/-0.625/-0.545 и ceF=-1.78."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width',260); pd.set_option('display.max_columns',40)
m=load();
def ols(X,y):
    b,*_=np.linalg.lstsq(X,y,rcond=None); return b
def build(df,spec):
    n=len(df); cols=[np.ones(n)]; names=['const']
    cols.append(df['post'].values.astype(float)); names.append('post')
    if 'ce' in spec: cols.append(df['ceF'].values.astype(float)); names.append('ceF')
    if 'age' in spec: cols.append(np.log10(df['age_days'].values+1)); names.append('log10(age)')
    if 'mix' in spec:
        for c in ['сцена','функция','порог_входа']:
            for v in sorted(df[c].astype(str).unique())[1:]:
                cols.append((df[c].astype(str)==v).values.astype(float)); names.append(f'{c}={v}')
    return np.column_stack(cols),names
def series(df,ycol,logfn,lbl):
    y=logfn(df[ycol].values.astype(float)); ok=np.isfinite(y); df=df[ok]; y=y[ok]
    r={'спецификация':lbl,'n':len(df)}
    for spec,k in [([],'M1'),(['ce'],'M2'),(['ce','age'],'M3'),(['ce','age','mix'],'M4')]:
        X,names=build(df,spec); b=ols(X,y); r[k+' post']=round(b[names.index('post')],3)
        if 'ceF' in names and k=='M4': r['M4 ceF']=round(b[names.index('ceF')],3)
        if 'ceF' in names and k=='M2': r['M2 ceF']=round(b[names.index('ceF')],3)
    return r

rows=[]
lg1=lambda v: np.log10(v+1)
lg0=lambda v: np.where(v>0,np.log10(np.maximum(v,1e-9)),np.nan)
rows.append(series(m,'reads',lg1,'все 623, log10(reads+1)'))
rows.append(series(m,'reads',lg0,'все 623, log10(reads), нули выброшены'))
rows.append(series(m,'shows',lg1,'все 623, log10(shows+1)'))
rows.append(series(m,'opens',lg1,'все 623, log10(opens+1)'))
mm=m[m['ce'].notna()]
rows.append(series(mm,'reads',lg1,'620 (ce не NaN), log10(reads+1)'))
rows.append(series(m[m['эпоха']!='2_склон'],'reads',lg1,'без склона (556), log10(reads+1)'))
rows.append(series(m[m['date']>=pd.Timestamp('2024-01-01')],'reads',lg1,'с 2024-01-01 (529)'))
rows.append(series(m[m['date']>=pd.Timestamp('2025-01-01')],'reads',lg1,'с 2025-01-01 (402)'))
rows.append(series(m[m['half'].isin(['2025H1','2026H1'])],'reads',lg1,'2025H1+2026H1 (250)'))
rows.append(series(m[m['half'].isin(['2025H1','2025H2','2026H1'])],'reads',lg1,'2025H1+2025H2+2026H1 (388)'))
t=pd.DataFrame(rows)
print("ЦИФРЫ КРИТИКА: M1 post=-1.012, M2 post=-0.699, M3 post=-0.625, M4 post=-0.545, ceF=-1.78")
print(t.to_string(index=False))

# доля лог-разрыва, снимаемая каждым контролем, на нашей основной спецификации
print("\n=== Доля лог-разрыва между эпохами, снимаемая контролями (по медианам reads) ===")
def lg(x): return np.log10(x+1)
A=m[m['эпоха']=='1_до_спада']; B=m[m['эпоха']=='3_дно']
raw=lg(A['reads'].median())-lg(B['reads'].median())
Ac=A[A['ceT']]; Bc=B[B['ceT']]
after_ce=lg(Ac['reads'].median())-lg(Bc['reads'].median())
print(f"сырой лог-разрыв (до спада vs дно)      = {raw:.3f}  ({10**raw:.2f}x)")
print(f"после снятия ce=False                    = {after_ce:.3f}  ({10**after_ce:.2f}x)  снято {(1-after_ce/raw)*100:.1f}% лог-разрыва")
A1=m[m['half']=='2025H1']; B1=m[m['half']=='2026H1']
raw1=lg(A1['reads'].median())-lg(B1['reads'].median())
r2=lg(A1[A1['ceT']]['reads'].median())-lg(B1[B1['ceT']]['reads'].median())
b3=B1[B1['ceT']&(B1['age_days']>=150)]; a3=A1[A1['ceT']&(A1['age_days']>=150)]
r3=lg(a3['reads'].median())-lg(b3['reads'].median())
print(f"\n2025H1 vs 2026H1: сырой {raw1:.3f} ({10**raw1:.2f}x) -> ce=True {r2:.3f} ({10**r2:.2f}x) [снято {(1-r2/raw1)*100:.1f}%]"
      f" -> +age>=150 {r3:.3f} ({10**r3:.2f}x) [снято накопл. {(1-r3/raw1)*100:.1f}%]")
