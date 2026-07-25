# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 100)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month<=6,'H1','H2')

print("comments_enabled value_counts:", m['comments_enabled'].value_counts(dropna=False).to_dict())
print("серийная_рубрика value_counts:", m['серийная_рубрика'].value_counts(dropna=False).to_dict())
print()
print("crosstab ce x серия:")
print(pd.crosstab(m['comments_enabled'].astype(str), m['серийная_рубрика']))
print()
h1 = m[m['half']=='2026H1']
print("2026H1 всего:", len(h1))
print("  ce==True:", (h1['comments_enabled']==True).sum(), " серия==0:", (h1['серийная_рубрика']==0).sum())
se = h1[h1['сцена']=='стол_еда']
print("2026H1 стол_еда всего:", len(se))
print("  ce==True:", (se['comments_enabled']==True).sum(), " серия==0:", (se['серийная_рубрика']==0).sum(),
      " ce&неserия:", ((se['comments_enabled']==True)&(se['серийная_рубрика']==0)).sum())
print("  серия==1:", (se['серийная_рубрика']==1).sum())
print()
# критик: 2026H1 ce=True медианы shows 87276, opens 5449, reads 2366
for name, sub in [('ce==True', m[m['comments_enabled']==True]),
                  ('серия==0', m[m['серийная_рубрика']==0]),
                  ('ce&nonser', m[(m['comments_enabled']==True)&(m['серийная_рубрика']==0)])]:
    s = sub[sub['half']=='2026H1']
    print(f"{name:12s} 2026H1 n={len(s):3d} shows={s['shows'].median():.0f} opens={s['opens'].median():.0f} reads={s['reads'].median():.0f}")
    s24 = sub[sub['half']=='2024H1']
    print(f"{'':12s} 2024H1 n={len(s24):3d} shows={s24['shows'].median():.0f} opens={s24['opens'].median():.0f} reads={s24['reads'].median():.0f}")
print()
# критик (а): месячные медианы reads ce=True: авг25 16837, сен 14269, окт 4119, ноя 5055, дек 2874, янв26 5313, фев 5982, мар 4764, апр 3222, май 2216, июн 1086, июл 750
tgt = {'2025-08':16837,'2025-09':14269,'2025-10':4119,'2025-11':5055,'2025-12':2874,
       '2026-01':5313,'2026-02':5982,'2026-03':4764,'2026-04':3222,'2026-05':2216,'2026-06':1086,'2026-07':750}
for name, sub in [('ce==True', m[m['comments_enabled']==True]),
                  ('серия==0', m[m['серийная_рубрика']==0]),
                  ('ce&nonser', m[(m['comments_enabled']==True)&(m['серийная_рубрика']==0)]),
                  ('ВСЕ', m)]:
    g = sub.groupby(sub['ym'].astype(str))['reads'].median()
    row = [f"{k}:{g.get(k,float('nan')):.0f}/{v}" for k,v in tgt.items()]
    print(name, ' '.join(row))
