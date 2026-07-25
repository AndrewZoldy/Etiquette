import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + ((m['date'].dt.month > 6).astype(int) + 1).astype(str)
m['ce'] = m['comments_enabled'].map({True: 'T', False: 'F'}).fillna('NA')

print('=== A. weekday pattern of ce=False series ===')
d = m[m.ce == 'F']
print(d['date'].dt.dayofweek.value_counts().sort_index().to_string())
print('gap days between consecutive ce=False:', np.diff(d.date.sort_values().values).astype('timedelta64[D]').astype(int)[:40])

print()
print('=== B. стол_еда by half, split by ce ===')
s = m[m['сцена'] == 'стол_еда']
print(s.groupby(['half','ce']).agg(n=('shows','size'), med_shows=('shows','median'), med_reads=('reads','median'), med_ctr=('ctr','median')).to_string())

print()
print('=== C. Fact 2 redone on ce=True only (age cohorts) ===')
t = m[m.ce == 'T'].copy()
bins = [0,60,150,220,300,400,550,2000]
t['agebin'] = pd.cut(t.age_days, bins)
print(t.groupby('agebin', observed=True).agg(n=('shows','size'), med_shows=('shows','median'), med_reads=('reads','median'), dmin=('date','min'), dmax=('date','max')).to_string())
print()
print('--- same, ALL articles (as in dossier) ---')
a = m.copy(); a['agebin'] = pd.cut(a.age_days, bins)
print(a.groupby('agebin', observed=True).agg(n=('shows','size'), med_shows=('shows','median'), med_reads=('reads','median')).to_string())

print()
print('=== D. peak (2025H1) vs bottom (2026H1) medians, ce=True only ===')
for h in ['2024H1','2024H2','2025H1','2025H2','2026H1']:
    d2 = m[(m.half == h) & (m.ce == 'T')]
    print(f'{h} n={len(d2)} shows={d2.shows.median():.0f} reads={d2.reads.median():.0f} opens={d2.opens.median():.0f}')

print()
print('=== E. Composition standardization: 2026H1 reweighted to 2025H1 scene mix (ce=True) ===')
def wmedian(vals, wts):
    o = np.argsort(vals); v = np.asarray(vals)[o]; w = np.asarray(wts)[o]
    c = np.cumsum(w) / np.sum(w)
    return v[np.searchsorted(c, 0.5)]
for key in [['сцена'], ['функция'], ['сцена','функция'], ['сцена','порог_входа']]:
    for sub in ['T','all']:
        base = m[(m.half=='2025H1')] if sub=='all' else m[(m.half=='2025H1')&(m.ce=='T')]
        tgt  = m[(m.half=='2026H1')] if sub=='all' else m[(m.half=='2026H1')&(m.ce=='T')]
        pb = base.groupby(key, observed=True).size() / len(base)
        pt = tgt.groupby(key, observed=True).size() / len(tgt)
        wmap = (pb / pt).replace([np.inf,-np.inf], np.nan)
        w = tgt.set_index(key).index.map(wmap).astype(float)
        w = np.where(np.isnan(w), 0, w)
        for col in ['shows','reads']:
            raw = tgt[col].median(); std = wmedian(tgt[col].values, w)
            b = base[col].median()
            print(f'{"+".join(key):22s} {sub:4s} {col:6s} base={b:10.0f} raw2026={raw:9.0f} std2026={std:9.0f}  ratio_raw={b/max(raw,1):6.2f} ratio_std={b/max(std,1):6.2f}')
    print()
