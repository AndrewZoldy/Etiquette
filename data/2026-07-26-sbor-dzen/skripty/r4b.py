# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 4 — устойчивость, контрпримеры, пересчёт Факта 9 на ce=True, природа подпродукта ce=False."""
import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
rng = np.random.default_rng(20260726)
m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month<=6,'H1','H2')

print("="*120)
print("У1. УСТОЙЧИВОСТЬ ИНДЕКСА стол_еда НА ДНЕ (ce=True, n=17). Индекс 2,54 — точечная оценка.")
print("="*120)
E3 = m[(m['эпоха']=='3_дно') & m['ce']]
se = E3[E3['сцена']=='стол_еда']; oth = E3[E3['сцена']!='стол_еда']
print(f"  стол_еда n={len(se)}, остальные сцены n={len(oth)}")
print(f"  медиана reads: стол_еда {se['reads'].median():,.0f} / прочие {oth['reads'].median():,.0f} = x{se['reads'].median()/oth['reads'].median():.2f}".replace(',',' '))
# бутстрап отношения к ОСТАЛЬНЫМ (а не ко всей эпохе — так статья не входит в обе части)
a=se['reads'].values.astype(float); b=oth['reads'].values.astype(float)
ra=np.median(a[rng.integers(0,len(a),size=(20000,len(a)))],axis=1); rb=np.median(b[rng.integers(0,len(b),size=(20000,len(b)))],axis=1)
r=ra/rb
print(f"  бутстрап отношения стол_еда/прочие: {np.median(a)/np.median(b):.2f} CI95 [{np.percentile(r,2.5):.2f}; {np.percentile(r,97.5):.2f}]")
print(f"  доля бутстрап-повторов с отношением >1: {(r>1).mean():.3f}; <0.5: {(r<0.5).mean():.3f}")
# ранговый тест без распределительных допущений
from itertools import product
u = sum(1 for x,y in product(a,b) if x>y) + 0.5*sum(1 for x,y in product(a,b) if x==y)
auc = u/(len(a)*len(b))
print(f"  доля пар (стол_еда > прочая статья) = AUC = {auc:.3f}  (0,5 = нет различия)")
print("\n  jackknife: индекс при удалении каждой из 17 статей стол_еда (мин/макс):")
idx=[]
med_ep = E3['reads'].median()
for i in range(len(se)):
    s2 = se.drop(se.index[i]); idx.append(s2['reads'].median()/med_ep)
print(f"    мин={min(idx):.2f} макс={max(idx):.2f} медиана={np.median(idx):.2f}  -> индекс не создан одной статьёй" if min(idx)>1 else f"    мин={min(idx):.2f} макс={max(idx):.2f}")
print("\n  контрпримеры внутри стол_еда ce=True на дне (худшие 5 и лучшие 5 по reads):")
cols=['date','title_studio','shows','reads','ctr','age_days']
print(se.nsmallest(5,'reads')[cols].to_string(index=False))
print(se.nlargest(5,'reads')[cols].to_string(index=False))

print("\n"+"="*120)
print("У2. ПЕРЕСЧЁТ ФАКТА 9 (состав выживших/застрявших) ТОЛЬКО НА ce=True")
print("="*120)
for lab, D in [('ВСЯ ВЫБОРКА (как в досье)', m[m['эпоха']=='3_дно']), ('ТОЛЬКО ce=True', E3)]:
    surv = D[D['shows']>500000]; stuck = D[D['shows']<10000]
    print(f"\n  {lab}: n={len(D)}, выжившие(>500к)={len(surv)}, застрявшие(<10к)={len(stuck)}")
    if len(stuck)<10: print("    застрявших меньше 10 — состав не выводится")
    print(f"    {'сцена':26s} {'выжившие %':>11s} {'застрявшие %':>13s} {'разница п.п.':>13s}")
    scs = sorted(set(D['сцена']))
    for sc in scs:
        p1 = (surv['сцена']==sc).mean()*100 if len(surv) else np.nan
        p2 = (stuck['сцена']==sc).mean()*100 if len(stuck) else np.nan
        if len(stuck)>=10 or len(surv)>=10:
            print(f"    {sc:26s} {p1:11.1f} {p2:13.1f} {p1-p2:+13.1f}")

print("\n"+"="*120)
print("У3. ЧТО ТАКОЕ ПОДПРОДУКТ ce=False: тема или ФОРМАТ?")
print("="*120)
per = m[m['date']>='2025-09-01']
t_=per[per['ce']]; f_=per[~per['ce']]
print(f"  окно сен2025-июл2026: ce=True n={len(t_)}, ce=False n={len(f_)}")
for col,lab in [('n_words','слов'),('n_chars','знаков'),('time_to_read_s','время чтения, с'),
                ('n_images','картинок'),('n_paragraphs','абзацев'),('n_headers','подзаголовков'),
                ('ctr','CTR'),('read_rate','дочитываемость'),('shows','показы'),('reads','дочитывания')]:
    print(f"    медиана {lab:18s}: ce=True {t_[col].median():>10,.3f}   ce=False {f_[col].median():>10,.3f}".replace(',',' '))
print(f"\n  доля 'польза' в функции: ce=True {(t_['функция']=='польза').mean():.2f}, ce=False {(f_['функция']=='польза').mean():.2f}")
print(f"  доля сцен ce=False: {f_['сцена'].value_counts(normalize=True).round(3).to_dict()}")
print(f"  серийная_рубрика==1 среди ce=False: {(f_['серийная_рубрика']==1).sum()} из {len(f_)}")
print("\n  Тот же формат-тест ВНУТРИ сцены стол_еда (сен2025-июл2026):")
se_p = per[per['сцена']=='стол_еда']
a_=se_p[se_p['ce']]; b_=se_p[~se_p['ce']]
for col,lab in [('n_words','слов'),('time_to_read_s','время чтения, с'),('n_images','картинок'),('ctr','CTR'),('shows','показы')]:
    print(f"    {lab:18s}: ce=True(n={len(a_)}) {a_[col].median():>10,.3f}   ce=False(n={len(b_)}) {b_[col].median():>10,.3f}".replace(',',' '))

print("\n"+"="*120)
print("У4. КОНТРПРИМЕР К «ПАДЕНИЮ ce=False»: лучшие статьи подпродукта")
print("="*120)
print(f_.nlargest(5,'shows')[['date','title_studio','сцена','shows','reads','ctr']].to_string(index=False))
print(f"\n  распределение shows у ce=False: 10й перц={f_['shows'].quantile(.1):,.0f} медиана={f_['shows'].median():,.0f} 90й={f_['shows'].quantile(.9):,.0f} макс={f_['shows'].max():,.0f}".replace(',',' '))
print(f"  доля ce=False с shows<10 000: {(f_['shows']<10000).mean():.2f}")
