# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 100)
m = load()
rng = np.random.default_rng(5)

print("="*110)
print("ТРЕБОВАНИЕ 2 — УСТОЙЧИВОСТЬ")
print("="*110)

# 1) бутстрап q5/q1 на ce=True дно
def q51(d):
    d = d.copy()
    try: d['q'] = pd.qcut(d['ctr'], 5, labels=[1,2,3,4,5])
    except Exception: return np.nan
    g = d.groupby('q', observed=True)['shows'].median()
    if 1 not in g.index or 5 not in g.index or g.loc[1] <= 0: return np.nan
    return g.loc[5]/g.loc[1]

for lab, d in [('ce=True, дно', m[(m['ce']==True)&(m['эпоха']=='3_дно')&m['ctr'].notna()]),
               ('сырьё,  дно',  m[(m['эпоха']=='3_дно')&m['ctr'].notna()]),
               ('ce=True, до_спада', m[(m['ce']==True)&(m['эпоха']=='1_до_спада')&m['ctr'].notna()])]:
    pt = q51(d)
    bs = np.array([q51(d.iloc[rng.integers(0,len(d),len(d))]) for _ in range(4000)])
    bs = bs[np.isfinite(bs)]
    lo,hi = np.percentile(bs,[2.5,97.5])
    # спирмен
    sp = d['ctr'].corr(d['shows'],method='spearman')
    sps = np.array([d.iloc[rng.integers(0,len(d),len(d))][['ctr','shows']].corr(method='spearman').iloc[0,1] for _ in range(2000)])
    slo,shi = np.percentile(sps[np.isfinite(sps)],[2.5,97.5])
    print(f"{lab:18s} n={len(d):4d}  q5/q1={pt:6.2f}x  CI95=[{lo:.2f}; {hi:.2f}]   "
          f"Спирмен CTR-показы={sp:+.3f} CI95=[{slo:+.3f}; {shi:+.3f}]")
print()

# 2) доля <10k в 2026H1 ce=True — бутстрап и сравнение с 2024H1
print("--- Доля shows<10000: бутстрап-CI ---")
for h in ['2024H1','2025H1','2026H1']:
    s = m[(m['half']==h)&(m['ce']==True)]['shows'].values
    p = (s<10000).mean()
    bs = np.array([(s[rng.integers(0,len(s),len(s))]<10000).mean() for _ in range(4000)])
    print(f"{h} ce=True n={len(s):3d}: доля<10k={p*100:5.1f}%  CI95=[{np.percentile(bs,2.5)*100:.1f}%; {np.percentile(bs,97.5)*100:.1f}%]")
print()

# 3) p90/p10 бутстрап
print("--- p90/p10: бутстрап-CI (ce=True) ---")
for h in ['2024H1','2025H1','2025H2','2026H1']:
    s = m[(m['half']==h)&(m['ce']==True)]['shows'].values
    f = lambda a: np.percentile(a,90)/np.percentile(a,10)
    bs = np.array([f(s[rng.integers(0,len(s),len(s))]) for _ in range(4000)])
    print(f"{h} ce=True n={len(s):3d}: p90/p10={f(s):7.1f}  CI95=[{np.percentile(bs,2.5):.1f}; {np.percentile(bs,97.5):.1f}]")
print()

# 4) КОНТРПРИМЕР-ПРОВЕРКА: не создан ли «неупавший пол» цензом зрелости?
print("--- Контрпроверка: 2026H1 ce=True по месяцам (пол по месяцам) ---")
d = m[(m['half']=='2026H1')&(m['ce']==True)]
g = d.groupby(d['date'].dt.to_period('M')).agg(n=('shows','size'), p10=('shows',lambda s: np.percentile(s,10)),
                                               p50=('shows','median'), p90=('shows',lambda s: np.percentile(s,90)),
                                               доля_lt10k=('shows', lambda s: round((s<10000).mean()*100,1)))
print(g.round(0).to_string())
print()
print("--- То же для 2026H2 (июль 2026) и 2025H2 по месяцам, ce=True ---")
d2 = m[(m['half'].isin(['2025H2','2026H2']))&(m['ce']==True)]
g2 = d2.groupby(d2['date'].dt.to_period('M')).agg(n=('shows','size'), p10=('shows',lambda s: np.percentile(s,10)),
                                                  p50=('shows','median'), доля_lt10k=('shows', lambda s: round((s<10000).mean()*100,1)))
print(g2.round(0).to_string())
print()

# 5) первичная метрика: тот же пол на ДОЧИТЫВАНИЯХ
print("--- Пол на первичной метрике (reads), ce=True ---")
rows=[]
for h in ['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']:
    s = m[(m['half']==h)&(m['ce']==True)]['reads']
    p10,p50,p90 = np.percentile(s,[10,50,90])
    rows.append(dict(полугодие=h,n=len(s),p10=round(p10),p50=round(p50),p90=round(p90),
                     p90_p10=round(p90/p10,1), доля_reads_lt_500=round((s<500).mean()*100,1)))
print(pd.DataFrame(rows).to_string(index=False))
