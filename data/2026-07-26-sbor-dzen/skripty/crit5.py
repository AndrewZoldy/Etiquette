import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + ((m['date'].dt.month > 6).astype(int) + 1).astype(str)
m['ce'] = m['comments_enabled'].map({True:'T', False:'F'}).fillna('NA')

print('=== A. views_public vs opens ratio by ce (is it special?) ===')
m['vp_op'] = m.views_public / m.opens.replace(0, np.nan)
print(m.groupby('ce')['vp_op'].describe().to_string())

print()
print('=== B. sums: articles/rollers/posts, H1 comparisons (H10 claims) ===')
art = m
for h in ['2024H1','2025H1','2026H1']:
    d = art[art.half==h]
    print(f'{h} n={len(d):4d} sum_shows={d.shows.sum():,} sum_opens={d.opens.sum():,} sum_reads={d.reads.sum():,} sum_subs={d.subs.sum():,} mean_reads={d.reads.mean():,.0f} med_reads={d.reads.median():,.0f} skew={d.reads.mean()/max(d.reads.median(),1):.2f}')
    dT = d[d.ce=='T']
    print(f'      ce=T n={len(dT):4d} sum_reads={dT.reads.sum():,} mean={dT.reads.mean():,.0f} med={dT.reads.median():,.0f} skew={dT.reads.mean()/max(dT.reads.median(),1):.2f}')

print()
print('=== C. subs total (base reconstruction sanity) ===')
rol = pd.read_pickle('out/rol.pkl'); pos = pd.read_pickle('out/pos.pkl')
print('cols rol:', [c for c in rol.columns][:20])
print('articles subs total:', m.subs.sum())
for nm, df in [('rol',rol),('pos',pos)]:
    if 'subs' in df.columns: print(nm, 'subs total:', df.subs.sum(), 'n=', len(df))

print()
print('=== D. H8 test: after-viral vs quiet, epoch bottom & pre ===')
m2 = m.sort_values('date').reset_index(drop=True)
viral = m2[m2.shows > 1_000_000]['date'].values
def days_since_viral(d):
    prev = viral[viral < np.datetime64(d)]
    return (np.datetime64(d) - prev[-1]) / np.timedelta64(1,'D') if len(prev) else np.nan
m2['dsv'] = m2['date'].apply(days_since_viral)
for ep in ['1_до_спада','3_дно']:
    d = m2[m2['эпоха']==ep]
    for lab, sub in [('<=14d', d[d.dsv<=14]), ('>14d', d[d.dsv>14])]:
        print(f'{ep} {lab:6s} n={len(sub):4d} ctr={sub.ctr.median():.4f} shows={sub.shows.median():,.0f} reads={sub.reads.median():,.0f}')
    # bins
    d3 = d[d.ce=='T'] if 'ce' in d else d
    print(f'   ce=True only:')
    for lab, lo, hi in [('0-3',0,3),('4-7',4,7),('8-14',8,14),('15-30',15,30),('31+',31,10000)]:
        sub = d3[(d3.dsv>=lo)&(d3.dsv<=hi)]
        if len(sub)>=1: print(f'     {lab:6s} n={len(sub):3d} ctr={sub.ctr.median():.4f} shows={sub.shows.median():,.0f}')
    print()

print('=== E. H2 conditional dispersion: IQR log10(shows) within CTR bands ===')
m['lg'] = np.log10(m.shows.clip(lower=1))
bands = [(0.03,0.05),(0.05,0.08),(0.08,0.12)]
for ep in ['1_до_спада','3_дно']:
    for lo,hi in bands:
        for cef in ['all','T']:
            d = m[(m['эпоха']==ep)&(m.ctr>=lo)&(m.ctr<hi)]
            if cef=='T': d = d[d.ce=='T']
            if len(d)<10:
                print(f'{ep} ctr[{lo},{hi}) {cef:3s} n={len(d)} <10 skip'); continue
            q = d.lg.quantile([.1,.25,.75,.9])
            print(f'{ep} ctr[{lo},{hi}) {cef:3s} n={len(d):3d} IQRlog={q[.75]-q[.25]:.2f} p90/p10={10**(q[.9]-q[.1]):.0f} med={d.shows.median():,.0f}')
    print()
