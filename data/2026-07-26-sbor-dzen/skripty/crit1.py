import pandas as pd, numpy as np
pd.set_option('display.width', 200)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + ((m['date'].dt.month > 6).astype(int) + 1).astype(str)
print('=== 1. comments_enabled distribution ===')
print(m['comments_enabled'].value_counts(dropna=False))
print(m.groupby('half')['comments_enabled'].apply(lambda s: pd.Series({'n': len(s), 'nTrue': (s == True).sum(), 'nFalse': (s == False).sum(), 'nNA': s.isna().sum()})).unstack())

print()
print('=== 2. ce=False by month ===')
t = m[m['comments_enabled'] == False].groupby('ym').size()
print(t.to_string())

print()
print('=== 3. Medians by half x ce ===')
for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2','2026H1','2026H2']:
    d = m[m['half'] == h]
    for lab, sub in [('ALL', d), ('ce=True', d[d['comments_enabled'] == True]), ('ce=False', d[d['comments_enabled'] == False]), ('ceNA', d[d['comments_enabled'].isna()])]:
        if len(sub) == 0: continue
        print(f'{h:8s} {lab:9s} n={len(sub):4d} shows={sub.shows.median():12.0f} opens={sub.opens.median():9.0f} reads={sub.reads.median():9.0f} ctr={sub.ctr.median():.4f} rr={sub.read_rate.median():.3f}')
    print()
