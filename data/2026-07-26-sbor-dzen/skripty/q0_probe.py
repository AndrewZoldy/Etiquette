# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
print("shape", m.shape)
print("\ncolumns:", list(m.columns))
print("\n--- age_days: max date, cutoff check ---")
print("date max", m['date'].max())
print("age_days vs (2026-07-25 - date):")
chk = (pd.Timestamp('2026-07-25') - m['date']).dt.days
print("diff describe:", (m['age_days'] - chk).describe().to_string())
print("\n--- ce ---")
m['ce'] = m['comments_enabled']
print(m['ce'].value_counts(dropna=False).to_dict())
print("\n--- cpr/lpr formulas check ---")
sub = m[(m['reads'] > 0)].copy()
print("cpr resid:", (sub['comments_per_read'] - sub['comments']/sub['reads']).abs().max())
print("lpr resid:", (sub['likes_per_read'] - sub['likes']/sub['reads']).abs().max())
print("ctr resid:", (sub['ctr'] - sub['opens']/sub['shows']).abs().max())
print("rr resid:", (sub['read_rate'] - sub['reads']/sub['opens']).abs().max())
print("\n--- half column present? ---")
print('half' in m.columns, m['half'].value_counts(dropna=False).to_string() if 'half' in m.columns else '')
print("\n--- эпоха x ce ---")
print(pd.crosstab(m['эпоха'], m['ce'].astype(str)))
print("\n--- monthly n by ce ---")
mm = m.copy(); mm['ymS'] = mm['ym'].astype(str)
t = mm.pivot_table(index='ymS', columns=mm['ce'].astype(str), values='oid', aggfunc='count', fill_value=0)
print(t.to_string())
print("\n--- ce=False: how do they relate to серийная_рубрика ---")
print(pd.crosstab(m['ce'].astype(str), m['серийная_рубрика']))
print("\n--- 2026H1 стол_еда breakdown ---")
m['halfX'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
h = m[(m['halfX'] == '2026H1')]
se = h[h['сцена'] == 'стол_еда']
print("2026H1 all n", len(h), " стол_еда n", len(se),
      " ce=False among стол_еда:", (se['ce'] == False).sum(),
      " ce=True:", (se['ce'] == True).sum(), " NaN:", se['ce'].isna().sum())
print("\n--- reads==0 / comments NaN in dno ce=True ---")
d = m[(m['эпоха'] == '3_дно') & (m['ce'] == True)]
print("n dno ce=True", len(d), "reads==0:", (d['reads'] == 0).sum(),
      "comments NaN:", d['comments'].isna().sum(), "likes NaN:", d['likes'].isna().sum())
print("age_days range dno ce=True:", d['age_days'].min(), d['age_days'].max())
print("\n--- epoch1 age>550 ce=True n ---")
e1 = m[(m['эпоха'] == '1_до_спада')]
print("epoch1 n", len(e1), " age>550 n", (e1['age_days'] > 550).sum(),
      " age>550 & ce=True n", ((e1['age_days'] > 550) & (e1['ce'] == True)).sum())
print("epoch1 date range", e1['date'].min(), e1['date'].max())
print("\n--- shows>320000 share overall by half ---")
print(m.groupby('halfX').apply(lambda g: pd.Series({'n': len(g), 'sh320k': (g['shows'] > 320000).mean()}), include_groups=False).to_string())
