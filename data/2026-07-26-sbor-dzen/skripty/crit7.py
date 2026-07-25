import pandas as pd, numpy as np
import statsmodels.api as sm
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + ((m['date'].dt.month > 6).astype(int) + 1).astype(str)
m['ce'] = m['comments_enabled'].map({True:'T', False:'F'}).fillna('NA')
m['lgr'] = np.log10(m.reads.clip(lower=1)); m['lgs'] = np.log10(m.shows.clip(lower=1))

print('=== A. Ladder: what each control removes (2025H1 -> 2026H1, reads) ===')
def med(d,c='reads'): return d[c].median()
a = m[m.half=='2025H1']; b = m[m.half=='2026H1']
steps = [
 ('raw', a, b),
 ('ce=True only', a[a.ce=='T'], b[b.ce=='T']),
 ('ce=T + age>=150d', a[a.ce=='T'], b[(b.ce=='T')&(b.age_days>=150)]),
]
for nm, x, y in steps:
    print(f'{nm:20s} n={len(x):3d}/{len(y):3d} reads {med(x):9,.0f} -> {med(y):9,.0f} = {med(x)/max(med(y),1):6.2f}x | shows {med(x,"shows"):11,.0f} -> {med(y,"shows"):10,.0f} = {med(x,"shows")/max(med(y,"shows"),1):6.2f}x')

print()
print('=== B. Same ladder vs 2024H1 base ===')
a2 = m[m.half=='2024H1']
for nm, y in [('raw 2026H1', b), ('ce=True', b[b.ce=='T']), ('ce=T+age>=150', b[(b.ce=='T')&(b.age_days>=150)])]:
    print(f'2024H1 vs {nm:16s} n={len(a2)}/{len(y):3d} reads {med(a2):8,.0f} -> {med(y):9,.0f} = {med(a2)/max(med(y),1):6.2f}x | shows {med(a2,"shows"):10,.0f} -> {med(y,"shows"):10,.0f} = {med(a2,"shows")/max(med(y,"shows"),1):6.2f}x')

print()
print('=== C. OLS log10(reads) ~ epoch + controls, articles from 2024H2 onward ===')
d = m[(m.half.isin(['2024H2','2025H1','2025H2','2026H1','2026H2']))].copy()
d['post'] = (d.date >= '2025-11-01').astype(int)
d['ceF'] = (d.ce=='F').astype(int)
d['lage'] = np.log10(d.age_days.clip(lower=1))
base = ['post']
mods = {
 'M1 post only': ['post'],
 'M2 +ceF': ['post','ceF'],
 'M3 +ceF+log(age)': ['post','ceF','lage'],
 'M4 +ceF+log(age)+scene+func': None,
}
for nm, cols in mods.items():
    if cols is None:
        X = pd.get_dummies(d[['сцена','функция','порог_входа']], drop_first=True).astype(float)
        X = pd.concat([d[['post','ceF','lage']].astype(float), X], axis=1)
    else:
        X = d[cols].astype(float)
    X = sm.add_constant(X)
    r = sm.OLS(d.lgr.values, X.values).fit()
    i = list(X.columns).index('post')
    print(f'{nm:30s} post={r.params[i]:+.3f} (se {r.bse[i]:.3f})  => {10**(-r.params[i]):.2f}x   R2={r.rsquared:.3f} n={len(d)}')
    if 'ceF' in X.columns:
        j = list(X.columns).index('ceF'); print(f'{"":30s} ceF ={r.params[j]:+.3f} (se {r.bse[j]:.3f}) => {10**(-r.params[j]):.2f}x')

print()
print('=== D. стол_еда: is the theme punished, once the series is removed? (index to epoch median) ===')
for ep,lab in [('1_до_спада','pre'),('3_дно','bottom')]:
    d = m[(m['эпоха']==ep)&(m.ce=='T')]
    tot = d.reads.median()
    for sc in ['стол_еда','отношения_общение','гости_праздники','прочее','история_высший_свет']:
        s = d[d['сцена']==sc]
        if len(s)<10: print(f'  {lab:6s} {sc:22s} n={len(s):3d} <10 SKIP'); continue
        print(f'  {lab:6s} {sc:22s} n={len(s):3d} idx_reads={s.reads.median()/tot:6.2f} idx_shows={s.shows.median()/d.shows.median():6.2f}')
    print()

print('=== E. how much of 2026H1 стол_еда volume is the series ===')
s26 = m[(m.half=='2026H1')&(m['сцена']=='стол_еда')]
print('n=',len(s26),' ce=F:',(s26.ce=='F').sum(),' share:',(s26.ce=="F").mean().round(3))
s25h2 = m[(m.half=='2025H2')&(m['сцена']=='стол_еда')]
print('2025H2 n=',len(s25h2),' ce=F:',(s25h2.ce=='F').sum())
