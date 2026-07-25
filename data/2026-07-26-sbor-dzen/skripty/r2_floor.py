# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 100); pd.set_option('display.max_rows', 400)

m = load()
HALVES = ['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']

print("="*110)
print("ТРЕБОВАНИЕ 2. ПЕРЕСЧЁТ ФАКТОВ 4 и 5 НА ce==True")
print("="*110)

def floor_table(sub, label):
    rows=[]
    for h in HALVES:
        s = sub[sub['half']==h]['shows']
        if len(s)==0: continue
        p10,p50,p90 = np.percentile(s,[10,50,90])
        rows.append(dict(полугодие=h, n=len(s),
                         доля_shows_lt_10k=round((s<10000).mean()*100,1),
                         доля_shows_lt_3k=round((s<3000).mean()*100,1),
                         n_lt_10k=int((s<10000).sum()), n_lt_3k=int((s<3000).sum()),
                         p10=round(p10), p50=round(p50), p90=round(p90),
                         p90_div_p10=round(p90/p10,1) if p10>0 else np.nan,
                         min=int(s.min()), max=int(s.max())))
    df = pd.DataFrame(rows)
    print(f"--- {label} ---"); print(df.to_string(index=False)); print()
    return df

t_raw = floor_table(m, "A. СЫРЬЁ (как в Факте 4 досье) — контроль воспроизводимости")
t_ce  = floor_table(m[m['ce']==True], "B. ТОЛЬКО comments_enabled==True  <-- ТРЕБОВАНИЕ КРИТИКА")
t_cf  = floor_table(m[m['ce']==False], "C. Только comments_enabled==False (справочно; n мал по полугодиям)")

print("--- Сводка: что даёт удаление серии ce=False ---")
cmp = pd.DataFrame({
    'сырьё_доля<10k': t_raw.set_index('полугодие')['доля_shows_lt_10k'],
    'ce=True_доля<10k': t_ce.set_index('полугодие')['доля_shows_lt_10k'],
    'сырьё_доля<3k': t_raw.set_index('полугодие')['доля_shows_lt_3k'],
    'ce=True_доля<3k': t_ce.set_index('полугодие')['доля_shows_lt_3k'],
    'сырьё_p90/p10': t_raw.set_index('полугодие')['p90_div_p10'],
    'ce=True_p90/p10': t_ce.set_index('полугодие')['p90_div_p10'],
})
print(cmp.to_string()); print()

# --- то же для эпохи «дно» целиком (ноя2025-июл2026) — база утверждений досье
print("--- Эпоха 3_дно целиком: доля застрявших, сырьё vs ce=True ---")
for lab, sub in [('сырьё', m), ('ce=True', m[m['ce']==True]), ('ce=False', m[m['ce']==False])]:
    for ep in ['1_до_спада','3_дно']:
        s = sub[sub['эпоха']==ep]['shows']
        if len(s)<10:
            print(f"{lab:9s} {ep:12s} n={len(s):4d}  -- группа <10, вывод не формулируется"); continue
        p10,p90 = np.percentile(s,[10,90])
        print(f"{lab:9s} {ep:12s} n={len(s):4d}  <10k={(s<10000).mean()*100:5.1f}%  <3k={(s<3000).mean()*100:5.1f}%  "
              f"p10={p10:>10,.0f}  p50={s.median():>10,.0f}  p90={p90:>11,.0f}  p90/p10={p90/p10:7.1f}"
              .replace(',', ' '))
print()

# --------- квинтили CTR
print("="*110)
print("ФАКТ 5: медиана показов по квинтилям CTR внутри эпохи")
print("="*110)

def quint(sub, ep, label):
    d = sub[(sub['эпоха']==ep) & sub['ctr'].notna()].copy()
    if len(d) < 10:
        print(f"[{label}] n={len(d)} -- группа <10, вывод не формулируется"); return None
    d['q'] = pd.qcut(d['ctr'], 5, labels=[1,2,3,4,5])
    g = d.groupby('q', observed=True).agg(n=('shows','size'), мед_CTR=('ctr','median'),
                                          мед_показов=('shows','median'), мед_дочит=('reads','median'),
                                          p25_показов=('shows', lambda s: np.percentile(s,25)),
                                          p75_показов=('shows', lambda s: np.percentile(s,75)))
    g['мед_CTR'] = (g['мед_CTR']*100).round(2)
    g[['мед_показов','мед_дочит','p25_показов','p75_показов']] = g[['мед_показов','мед_дочит','p25_показов','p75_показов']].round(0)
    print(f"[{label}] n={len(d)}")
    print(g.to_string())
    r = g.loc[5,'мед_показов']/g.loc[1,'мед_показов']
    mono = list(g['мед_показов']) == sorted(g['мед_показов'])
    sp = d['ctr'].corr(d['shows'], method='spearman')
    print(f"  отношение q5/q1 = {r:.2f}x ; монотонность по возрастанию: {mono} ; Спирмен CTR-показы = {sp:+.3f}")
    print(f"  max/min по квинтилям = {g['мед_показов'].max()/g['мед_показов'].min():.2f}x")
    print()
    return g

quint(m, '1_до_спада', 'СЫРЬЁ, эпоха до_спада')
quint(m, '3_дно',      'СЫРЬЁ, эпоха дно')
quint(m[m['ce']==True], '1_до_спада', 'ce=True, эпоха до_спада')
quint(m[m['ce']==True], '3_дно',      'ce=True, эпоха дно   <-- ТРЕБОВАНИЕ КРИТИКА')
quint(m[m['ce']==True], '2_склон',    'ce=True, эпоха склон')

# устойчивость: квинтили на ce=True дно, но только 2026H1
d = m[(m['ce']==True) & (m['half']=='2026H1') & m['ctr'].notna()].copy()
if len(d)>=10:
    d['q']=pd.qcut(d['ctr'],5,labels=[1,2,3,4,5])
    g=d.groupby('q',observed=True).agg(n=('shows','size'),мед_CTR=('ctr','median'),мед_показов=('shows','median'))
    print("[ce=True, только 2026H1]"); print(g.to_string())
    print(f"  q5/q1 = {g.loc[5,'мед_показов']/g.loc[1,'мед_показов']:.2f}x")
print()

# --------- доля миллионников
print("--- Доля 'миллионников' (shows>1 000 000) ---")
rows=[]
for h in HALVES:
    for lab, sub in [('сырьё',m), ('ce=True',m[m['ce']==True])]:
        s=sub[sub['half']==h]['shows']
        if len(s)==0: continue
        rows.append(dict(полугодие=h, выборка=lab, n=len(s), доля_gt_1M=round((s>1e6).mean()*100,1)))
print(pd.DataFrame(rows).pivot(index='полугодие',columns='выборка',values='доля_gt_1M').to_string())
print()

# --------- кто именно сидит ниже 10k в 2026H1
print("--- Состав 'застрявших' (shows<10000) в 2026H1 ---")
z = m[(m['half']=='2026H1') & (m['shows']<10000)]
print(f"всего застрявших в 2026H1: {len(z)}; из них ce=False: {(z['ce']==False).sum()}; "
      f"ce=True: {(z['ce']==True).sum()}; ce=NaN: {z['ce'].isna().sum()}")
print("\nПо сценам:")
print(pd.crosstab(z['сцена'], z['ce'].astype(str)).to_string())
print("\n9 самых низких по показам в 2026H1 (все):")
print(z.nsmallest(9,'shows')[['date','title_studio','shows','opens','reads','ce','сцена']].to_string())
print("\nЗастрявшие ce=True в 2026H1 целиком:")
print(z[z['ce']==True][['date','title_studio','shows','opens','reads','ctr','сцена','функция']].sort_values('shows').to_string())
