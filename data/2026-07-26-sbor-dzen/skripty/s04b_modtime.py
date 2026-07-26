# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 4, добавление: publishTime vs modificationTime — ловим пост-фактум правку флага."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 50)
m = load()
W0, W1 = pd.Timestamp('2025-09-16'), pd.Timestamp('2026-05-21 23:59:59')
win = m[(m['date'] >= W0) & (m['date'] <= W1)].copy()

for df, name in [(win, 'ОКНО 16.09.25-21.05.26')]:
    df = df.copy()
    df['pt'] = pd.to_datetime(df['publishTime'], unit='ms', errors='coerce')
    df['mt'] = pd.to_datetime(df['modificationTime'], unit='ms', errors='coerce')
    df['mod_lag_d'] = (df['mt'] - df['pt']).dt.total_seconds()/86400
    print(f"=== {name} ===")
    for lbl, sub in [('ce=False', df[df['ceF']]), ('ce=True', df[df['ceT']])]:
        s = sub['mod_lag_d'].dropna()
        print(f"{lbl:9s} n={len(s):3d}  медиана лага модификации={s.median():.3f} дн  "
              f"p90={s.quantile(.9):.2f}  max={s.max():.2f}  доля лага>1дн={(s>1).mean()*100:.1f}%  доля>30дн={(s>30).mean()*100:.1f}%")
    print("\nЛаг модификации у 4 аномальных (comments>0) ce=False:")
    an = df[df['ceF'] & (df['comments']>0)][['date','title_studio','shows','comments','comments_public','mod_lag_d']].copy()
    an['date']=an['date'].dt.strftime('%Y-%m-%d'); an['title_studio']=an['title_studio'].str.slice(0,40)
    print(an.to_string(index=False))
    print("\nТоп-8 ce=False по лагу модификации:")
    t = df[df['ceF']].nlargest(8,'mod_lag_d')[['date','title_studio','shows','comments','mod_lag_d']].copy()
    t['date']=t['date'].dt.strftime('%Y-%m-%d'); t['title_studio']=t['title_studio'].str.slice(0,40)
    print(t.to_string(index=False))
    print("\nСвязь лага модификации с исходом внутри ce=False (Спирмен shows~mod_lag):",
          round(df[df['ceF']][['shows','mod_lag_d']].corr(method='spearman').iloc[0,1],3))
    print("Связь внутри ce=True:",
          round(df[df['ceT']][['shows','mod_lag_d']].corr(method='spearman').iloc[0,1],3))

# 1-в-1: детерминированность расписания
print("\n=== Детерминированность 'вт/чт => ce=False' в диапазоне серии ===")
s = m[(m['date']>=pd.Timestamp('2025-09-16')) & (m['date']<=pd.Timestamp('2026-05-21 23:59:59'))]
is_tt = s['date'].dt.dayofweek.isin([1,3])
print(pd.crosstab(np.where(is_tt,'вт/чт','остальные дни'), s['ce'].astype(str)))
print("\nИсключения из правила (вт/чт но ce=True, либо не вт/чт но ce=False):")
exc = s[(is_tt & s['ceT']) | (~is_tt & s['ceF'])][['date','dow','shows','reads','comments','сцена','title_studio']].copy()
exc['date']=exc['date'].dt.strftime('%Y-%m-%d'); exc['title_studio']=exc['title_studio'].str.slice(0,45)
print(exc.to_string(index=False))
