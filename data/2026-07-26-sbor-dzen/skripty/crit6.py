import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + ((m['date'].dt.month > 6).astype(int) + 1).astype(str)
m['ce'] = m['comments_enabled'].map({True:'T', False:'F'}).fillna('NA')

print('=== A. H1 quality-controlled comparison, replicated + ce=True ===')
q = m[(m.ctr>=0.08)&(m.read_rate>=0.50)&(m['сцена']!='стол_еда')]
for ep in ['1_до_спада','3_дно']:
    for cef in ['all','T']:
        d = q[q['эпоха']==ep]
        if cef=='T': d=d[d.ce=='T']
        print(f'{ep:12s} {cef:4s} n={len(d):3d} shows={d.shows.median():,.0f} reads={d.reads.median():,.0f}')
print()
print('  -- same but П-test: by half --')
for h in ['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']:
    d = q[(q.half==h)]; dT=d[d.ce=="T"]
    print(f'  {h} n={len(d):3d}/{len(dT):3d}  shows_all={d.shows.median() if len(d) else np.nan:,.0f}  shows_T={dT.shows.median() if len(dT) else np.nan:,.0f}  reads_T={dT.reads.median() if len(dT) else np.nan:,.0f}')

print()
print('=== B. П-test from H1: CTR 5-8% & read_rate 50-60%, by half ===')
q2 = m[(m.ctr>=0.05)&(m.ctr<0.08)&(m.read_rate>=0.50)&(m.read_rate<0.60)]
for h in ['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']:
    d=q2[q2.half==h]; dT=d[d.ce=='T']
    print(f'{h} n={len(d):3d}/{len(dT):3d} shows_all={d.shows.median() if len(d) else np.nan:,.0f} shows_T={dT.shows.median() if len(dT) else np.nan:,.0f} reads_T={dT.reads.median() if len(dT) else np.nan:,.0f}')

print()
print('=== C. content mix across halves (did author change before the boost?) ===')
print(pd.crosstab(m['half'], m['сцена'], normalize='index').round(3).to_string())
print()
print(pd.crosstab(m['half'], m['функция'], normalize='index').round(3).to_string())
print()
print(m.groupby('half')[['n_words','n_images','n_paragraphs','цифра_в_заголовке','вопрос','спорность','негативная_рамка','конкретный_якорь']].median(numeric_only=True).to_string())

print()
print('=== D. age gradient of comments_per_read within bottom epoch, ce=True ===')
d = m[(m['эпоха']=='3_дно')&(m.ce=='T')].copy()
d['ab'] = pd.cut(d.age_days, [0,45,75,110,150,200,270,400])
print(d.groupby('ab', observed=True).agg(n=('reads','size'), cpr=('comments_per_read','median'), lpr=('likes_per_read','median'), med_reads=('reads','median'), med_shows=('shows','median')).to_string())
print()
print('mature reference (epoch 1, age>550):')
d1 = m[(m['эпоха']=='1_до_спада')&(m.age_days>550)]
print(f'n={len(d1)} cpr={d1.comments_per_read.median():.4f} lpr={d1.likes_per_read.median():.4f}')

print()
print('=== E. per-month article count & channel totals (H10 n-effect) ===')
print(m.groupby('half').agg(n=('shows','size'), months=('ym', lambda s: s.nunique())).assign(per_month=lambda x: x.n/x.months).to_string())
