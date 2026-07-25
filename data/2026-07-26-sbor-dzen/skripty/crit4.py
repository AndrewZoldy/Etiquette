import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + ((m['date'].dt.month > 6).astype(int) + 1).astype(str)
m['ce'] = m['comments_enabled'].map({True:'T', False:'F'}).fillna('NA')

print('=== A. monthly medians, ALL vs ce=True, 2025-01..2026-07 ===')
g = m[m.date >= '2024-10-01']
rows = []
for ym, d in g.groupby('ym'):
    t = d[d.ce=='T']; f = d[d.ce=='F']
    rows.append(dict(ym=str(ym), n=len(d), nT=len(t), nF=len(f),
                     med_shows_all=d.shows.median(), med_shows_T=t.shows.median() if len(t) else np.nan,
                     med_reads_all=d.reads.median(), med_reads_T=t.reads.median() if len(t) else np.nan))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f'{x:,.0f}'))

print()
print('=== B. the 4 ce=False rows with comments>0 (join sanity) ===')
d = m[(m.ce=='F') & (m.comments>0)]
print(d[['date','title_studio','shows','opens','reads','comments','comments_public','likes','likes_public']].to_string())
print('\nany other article with comments==380?')
print(m[m.comments==380][['date','title_studio','shows','comments','ce']].to_string())

print()
print('=== C. stratified by scene, ce=True, 2025H1 vs 2026H1, n>=10 both sides ===')
for h1,h2 in [('2025H1','2026H1'),('2024H1','2026H1')]:
    print(f'--- {h1} vs {h2} (ce=True) ---')
    a = m[(m.half==h1)&(m.ce=='T')]; b = m[(m.half==h2)&(m.ce=='T')]
    for sc in sorted(set(a['сцена']) | set(b['сцена'])):
        na = (a['сцена']==sc).sum(); nb = (b['сцена']==sc).sum()
        flag = 'OK ' if (na>=10 and nb>=10) else 'n<10'
        ma = a.loc[a['сцена']==sc,'reads'].median(); mb = b.loc[b['сцена']==sc,'reads'].median()
        sa = a.loc[a['сцена']==sc,'shows'].median(); sb = b.loc[b['сцена']==sc,'shows'].median()
        print(f'  {flag} {sc:26s} n={na:3d}/{nb:3d} reads {ma:9.0f} -> {mb:9.0f} ({ma/max(mb,1):6.2f}x)  shows {sa:10.0f} -> {sb:10.0f} ({sa/max(sb,1):6.2f}x)')
    print()

print('=== D. bootstrap CI: 2026H1 ce=True vs 2024H1 (all ce=True) ===')
rng = np.random.default_rng(0)
a = m[(m.half=='2024H1')&(m.ce=='T')]; b = m[(m.half=='2026H1')&(m.ce=='T')]
for col in ['shows','opens','reads']:
    r = [np.median(rng.choice(a[col].values, len(a)))/max(np.median(rng.choice(b[col].values, len(b))),1) for _ in range(4000)]
    print(f'{col:6s} point={a[col].median()/max(b[col].median(),1):6.3f}  CI95=[{np.percentile(r,2.5):.3f}, {np.percentile(r,97.5):.3f}]')

print()
print('=== E. 2026H2 (14 art, all ce=True) and age of 2026H1 ce=True ===')
print(m[m.half=='2026H1'].groupby('ce')['age_days'].describe().to_string())
