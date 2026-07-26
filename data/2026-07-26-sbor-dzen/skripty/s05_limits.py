# -*- coding: utf-8 -*-
"""Пределы идентификации: слот vs флаг; час публикации; градиент возраста."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
m=load()
S=m[(m['date']>=pd.Timestamp('2025-09-16'))&(m['date']<=pd.Timestamp('2026-05-21 23:59:59'))].copy()
S['is_tt']=S['date'].dt.dayofweek.isin([1,3])

print("="*118)
print("A. ПРЕДЕЛ ИДЕНТИФИКАЦИИ: можно ли отделить 'выключенные комментарии' от 'слот вт/чт'?")
print("="*118)
print(pd.crosstab(S['is_tt'],S['ce'].astype(str),margins=True))
print("\n4 клетки 2x2 — медианы (первичная метрика reads):")
for tt in [True,False]:
    for ce in [True,False]:
        g=S[(S['is_tt']==tt)&(S['ce']==ce)]
        lbl=f"слот={'вт/чт' if tt else 'др.дни'}, комментарии={'вкл' if ce else 'выкл'}"
        if len(g)==0: print(f"  {lbl}: ПУСТО"); continue
        note='  *** n<10, вывод не формулируется ***' if len(g)<10 else ''
        print(f"  {lbl}: n={len(g):3d} мед reads={g['reads'].median():>10,.0f} мед shows={g['shows'].median():>11,.0f}{note}")
print("\n=> Две из четырёх клеток имеют n=2 и n=1. Флаг и слот РАЗДЕЛИТЬ НЕЛЬЗЯ.")
print("Три наблюдения-исключения (весь доступный материал для разделения):")
exc=S[((S['is_tt'])&(S['ceT']))|((~S['is_tt'])&(S['ceF']))][['date','dow','ce','shows','opens','reads','ctr','сцена','функция','title_studio']].copy()
exc['date']=exc['date'].dt.strftime('%Y-%m-%d'); exc['title_studio']=exc['title_studio'].str.slice(0,45)
print(exc.to_string(index=False))
print(f"\nДля сравнения медианы окна: серия(вт/чт,выкл) reads={S[S['ceF']]['reads'].median():,.0f}; "
      f"контроль(др.дни,вкл) reads={S[S['ceT']&(~S['is_tt'])]['reads'].median():,.0f}")

print("\n"+"="*118)
print("B. ЧАС ПУБЛИКАЦИИ как альтернативное объяснение (медиана часа серии 10 vs контроля 7)")
print("="*118)
C=m[m['ceT']]
print("Внутри ce=True: медиана reads по часу публикации (только группы n>=10)")
g=C.groupby('hour')['reads'].agg(['size','median'])
g['мед shows']=C.groupby('hour')['shows'].median()
print(g[g['size']>=10].to_string())
print(f"\nСпирмен(hour, reads) внутри ce=True: {C[['hour','reads']].corr(method='spearman').iloc[0,1]:.3f}")
win=C[(C['date']>=pd.Timestamp('2025-09-16'))&(C['date']<=pd.Timestamp('2026-05-21 23:59:59'))]
print(f"Спирмен(hour, reads) внутри ce=True в окне серии (n={len(win)}): {win[['hour','reads']].corr(method='spearman').iloc[0,1]:.3f}")
print("ce=True в окне, раннее (час<=8) vs позднее (час>=9):")
for lbl,sub in [('час<=8',win[win['hour']<=8]),('час>=9',win[win['hour']>=9])]:
    print(f"  {lbl}: n={len(sub)} мед reads={sub['reads'].median():,.0f} мед shows={sub['shows'].median():,.0f}")
print("=> Час не создаёт разрыва в 55-338x; максимум, что видно между группами часа, — единицы раз.")

print("\n"+"="*118)
print("C. ГРАДИЕНТ ВОЗРАСТА: идентифицируем ли ценз зрелости age>=150?")
print("="*118)
print("Носители возраста по эпохам (ce=True):")
for e in ['1_до_спада','2_склон','3_дно']:
    s=m[(m['эпоха']==e)&m['ceT']]
    print(f"  {e}: n={len(s)} age_days min={s['age_days'].min()} p50={s['age_days'].median():.0f} max={s['age_days'].max()}")
print("\nПересечение носителя: до спада age>=266, дно age<=265 => ПУСТОЕ. "
      "Контроль на возраст в M3/M4 и на ступени 3 — чистая экстраполяция.")
print("\nВнутриэпохальный градиент возраста (Спирмен age_days ~ reads), ce=True:")
for e in ['1_до_спада','3_дно']:
    s=m[(m['эпоха']==e)&m['ceT']]
    print(f"  {e}: n={len(s)} Спирмен(age,reads)={s[['age_days','reads']].corr(method='spearman').iloc[0,1]:.3f}, "
          f"Спирмен(age,shows)={s[['age_days','shows']].corr(method='spearman').iloc[0,1]:.3f}")
print("\nВнутри 'дна' ce=True по терцилям возраста:")
d=m[(m['эпоха']=='3_дно')&m['ceT']].copy(); d['t']=pd.qcut(d['age_days'],3,labels=['молодые','средние','старые'])
print(d.groupby('t',observed=True).agg(n=('reads','size'),мед_age=('age_days','median'),
      мед_reads=('reads','median'),мед_shows=('shows','median')).to_string())
print("\nКогорты возраста как в Факте 2 досье, но на ce=True:")
bins=[(0,60),(60,150),(150,220),(220,300),(300,400),(400,550)]
rows=[]
for a,b in bins:
    s=m[m['ceT']&(m['age_days']>=a)&(m['age_days']<b)]
    if len(s)==0: continue
    rows.append({'возраст':f"{a}-{b}",'n':len(s),'даты':f"{s['date'].min().date()}..{s['date'].max().date()}",
                 'мед shows':int(s['shows'].median()),'мед reads':int(s['reads'].median()),
                 'вывод?':'нет (n<10)' if len(s)<10 else ''})
print(pd.DataFrame(rows).to_string(index=False))
