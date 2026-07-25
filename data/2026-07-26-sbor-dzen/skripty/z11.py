import pandas as pd, numpy as np, re
pd.set_option('display.width',260); pd.set_option('display.max_rows',400)
m = pd.read_pickle('out/full_sim.pkl')
m['title']=m['title_public'].fillna(m['title_studio']).astype(str)
E1,E3='1_до_спада','3_дно'
se=m[m['сцена']=='стол_еда'].copy()
# "как есть/пить/подавать <еда>" — деятельностная формула
FORM=re.compile(r'^(как\s+(правильно\s+|изящно\s+|элегантно\s+)?(есть|съесть|пить|держать|наливать|подавать|пользоваться))', re.I)
se['формула']=np.where(se.title.str.match(FORM), 'как_есть_X', 'прочее')
print('=== формула «как есть/пить X» внутри стол_еда')
for ep in [E1,E3]:
    x=se[se['эпоха']==ep]
    print(ep, x.groupby('формула').agg(n=('shows','size'), med=('shows','median'), ctr=('ctr','median')).round(4).to_string())
print('\nна дне, «как есть X» поштучно:')
print(se[(se['эпоха']==E3)&(se['формула']=='как_есть_X')][['date','shows','ctr','title']].sort_values('shows',ascending=False).to_string())

# доля некликабельных (CTR ниже старого p10=0.0217)
print('\n=== доля статей с CTR ниже старого 10-го перцентиля (0,0217)')
for ep in ['1_до_спада','2_склон','3_дно']:
    x=m[m['эпоха']==ep].dropna(subset=['ctr'])
    print(ep,'n=%d доля=%.3f'%(len(x),(x.ctr<0.0217).mean()))
c=m[m['эпоха']==E3].dropna(subset=['ctr'])
z=c[c.ctr<0.0217]
print('среди них стол_еда: %.1f%%; медиана показов %.0f'%(100*(z['сцена']=='стол_еда').mean(), z.shows.median()))

# серийная рубрика
print('\n=== серийная рубрика на дне')
print(m[(m['эпоха']==E3)&(m['серийная_рубрика']==1)][['date','shows','ctr','reads','title']].sort_values('shows').to_string())

# контрфактик «убрать стол_еда» в окне Факта 1
p=m[(m.date>='2025-01-01')&(m.date<'2025-08-01')]; q=m[(m.date>='2025-11-01')&(m.date<'2026-07-01')]
qn=q[q['сцена']!='стол_еда']; pn=p[p['сцена']!='стол_еда']
print('\n=== окно Факта 1 без стол_еда: пик n=%d med=%.0f -> дно n=%d med=%.0f (%.1fx); с стол_еда 16,9x'
      %(len(pn),pn.shows.median(),len(qn),qn.shows.median(),pn.shows.median()/qn.shows.median()))
print('доля log-разрыва, снимаемая удалением стол_еда со дна: %.1f%%'
      %(100*(np.log10(qn.shows.median())-np.log10(q.shows.median()))/(np.log10(p.shows.median())-np.log10(q.shows.median()))))
