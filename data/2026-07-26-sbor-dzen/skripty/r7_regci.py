# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load, ols, dummies
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 120)
m = load()

print("="*110)
print("РЕГРЕССИОННЫЙ ОСТАТОК ЭПОХИ: точечная оценка + 95% CI НА КРАТНОСТИ (HC1)")
print("="*110)
specs = [('(1) post', [], None), ('(2) +ceF', ['ceF'], None),
         ('(3) +log10(age)', ['ceF','logage'], None),
         ('(4) +ceF+log10(age)+сцена+функция+порог', ['ceF','logage'], ['сцена','функция','порог_входа'])]

samples = [
  ('A. вся выборка (n=620), post=дата>=01.11.2025',  m[m['ce'].notna()], 'post'),
  ('B. 2025H1+2026H1, post=2026H1',                  m[m['half'].isin(['2025H1','2026H1']) & m['ce'].notna()], 'halfpost'),
  ('C. c 01.01.2025, post=дата>=01.11.2025',         m[(m['date']>=pd.Timestamp('2025-01-01')) & m['ce'].notna()], 'post'),
  ('D. c 01.07.2024, post=дата>=01.11.2025 (ВЫБОРКА КРИТИКА)', m[(m['date']>=pd.Timestamp('2024-07-01')) & m['ce'].notna()], 'post'),
]
allrows=[]
for lab, d, pc in samples:
    d = d.copy(); d['y']=np.log10(d['reads']+1); d['logage']=np.log10(d['age_days']+1)
    if pc=='halfpost': d['post']=(d['half']=='2026H1').astype(int)
    for tag, ex, cats in specs:
        X = pd.DataFrame({'const':1.0,'post':d['post'].astype(float)}, index=d.index)
        for c in ex: X[c]=d[c].astype(float)
        if cats:
            for c in cats: X=pd.concat([X,dummies(d,c)],axis=1)
        b,se,sh,r2,n = ols(d['y'].values, X.values, list(X.columns))
        lo_b, hi_b = b['post']-1.96*sh['post'], b['post']+1.96*sh['post']
        row = dict(выборка=lab, модель=tag, n=n, beta_post=round(b['post'],4), se_hc1=round(sh['post'],4),
                   кратность=round(10**(-b['post']),2),
                   CI_кратн_lo=round(10**(-hi_b),2), CI_кратн_hi=round(10**(-lo_b),2), R2=round(r2,3))
        if 'ceF' in b:
            lo_c, hi_c = b['ceF']-1.96*sh['ceF'], b['ceF']+1.96*sh['ceF']
            row['beta_ceF']=round(b['ceF'],4); row['кратн_ceF']=round(10**(-b['ceF']),1)
            row['CI_ceF_lo']=round(10**(-hi_c),1); row['CI_ceF_hi']=round(10**(-lo_c),1)
        allrows.append(row)
R = pd.DataFrame(allrows)
for lab,_,_ in samples:
    print(f"\n[{lab}]")
    print(R[R['выборка']==lab].drop(columns=['выборка']).to_string(index=False))
print()
print("Правило решения критика по Требованию 1: остаток >=8x И нижняя граница CI >5x  -> платформа;")
print("остаток <=4x -> аннулировать 17-21x; 4-8x -> вилка.")
print()
print("--- Сводка ступени 4 (все варианты, медианный подход) ---")
summ = pd.DataFrame([
 dict(вариант='буквально по критику: сетка сцена x функция x порог, ценз age>=150', отношение=6.19, CI='[1.89; 49.03]', примечание='сетка вырождена (0 ячеек n>=5 при n=26) — стандартизация НЕ применилась'),
 dict(вариант='сетка сцена, ценз age>=150',                    отношение=3.90, CI='[1.49; 46.48]', примечание='n 2026H1 = 26'),
 dict(вариант='сетка сцена x порог, ценз age>=150',            отношение=4.89, CI='[1.59; 50.13]', примечание='n 2026H1 = 26'),
 dict(вариант='сетка сцена, БЕЗ ценза',                        отношение=6.04, CI='[2.15; 22.67]', примечание='n 2026H1 = 108, покрытие 93,5%'),
 dict(вариант='сетка сцена x функция x порог, БЕЗ ценза',      отношение=5.72, CI='[2.24; 20.87]', примечание='n 2026H1 = 108, покрытие 44,4%'),
 dict(вариант='сетка функция x порог, БЕЗ ценза',              отношение=6.55, CI='[2.82; 19.68]', примечание='n 2026H1 = 108, покрытие 97,2%'),
 dict(вариант='ОБРАТНАЯ Оахака, сетка сцена, БЕЗ ценза',       отношение=12.93, CI='[3.46; 39.92]', примечание='2025H1 к составу 2026H1'),
 dict(вариант='ОБРАТНАЯ Оахака, сцена x функция x порог, БЕЗ ценза', отношение=8.25, CI='[3.25; 24.33]', примечание='2025H1 к составу 2026H1'),
 dict(вариант='ОБРАТНАЯ Оахака, сетка сцена, ценз age>=150',   отношение=5.98, CI='[1.82; 54.97]', примечание='n 2026H1 = 26'),
])
print(summ.to_string(index=False))
