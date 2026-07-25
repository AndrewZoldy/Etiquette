import pandas as pd, numpy as np, re
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 140); pd.set_option('display.max_rows', 500)
m = pd.read_pickle('out/full_sim.pkl')
m['title'] = m['title_public'].fillna(m['title_studio']).astype(str)
VERB = re.compile(r'\b(как|можно ли|почему|зачем|что делать|нужно ли|стоит ли|кто|когда|где|надо ли|правда ли)\b', re.I)
def reg(t):
    t=t.strip()
    if '?' in t or VERB.search(t): return 'вопрос_читателя'
    if re.search(r'\b\w+(ть|тся|ет|ют|ит|ат|ят|ете|йте|ла|ло|ли)\b', t, re.I): return 'утверждение'
    return 'номенклатура'
m['регистр']=m['title'].map(reg)
m['half']=m.date.dt.year.astype(str)+'H'+np.where(m.date.dt.month<=6,'1','2')
print('=== перцентили CTR по эпохам')
for ep in ['1_до_спада','2_склон','3_дно']:
    x=m[m['эпоха']==ep].dropna(subset=['ctr'])
    print(ep,'n=%d'%len(x),' '.join('p%d=%.4f'%(q,np.percentile(x.ctr,q)) for q in [5,10,25,50,75,90,95]))

print('\n=== качество/глубина по полугодиям (медианы)')
print(m.groupby('half').agg(n=('shows','size'), слов=('n_words','median'), картинок=('n_images','median'),
    абзацев=('n_paragraphs','median'), ttr_s=('time_to_read_s','median'),
    мин_на_дочит=('min_per_read','median'), дочитываемость=('read_rate','median'),
    лайк_на_дочит=('likes_per_read','median'), подп_на_дочит=('subs_per_read','median'),
    яркость=('brightness','median'), насыщ=('saturation','median'), контраст=('contrast','median'),
    тепло=('warm','median'), aspect=('aspect','median')).round(4).to_string())

print('\n=== «ядро» (бытовая+польза/разъяснение+вопрос_читателя) по полугодиям — проверка на артефакт состава')
core=m[(m['порог_входа']=='бытовая')&(m['функция'].isin(['польза','разъяснение_нормы']))&(m['регистр']=='вопрос_читателя')]
print(core.groupby('half').agg(n=('shows','size'), med=('shows','median'), reads=('reads','median'), ctr=('ctr','median')).round(4).to_string())
p=core[(core.date>='2025-01-01')&(core.date<'2025-08-01')]; q=core[(core.date>='2025-11-01')&(core.date<'2026-07-01')]
print('ядро, окно Факта 1: n=%d -> %d ; медиана %.0f -> %.0f (%.1fx) ; дочит %.0f -> %.0f (%.1fx) ; ctr %.3f -> %.3f'
      % (len(p),len(q),p.shows.median(),q.shows.median(),p.shows.median()/q.shows.median(),
         p.reads.median(),q.reads.median(),p.reads.median()/q.reads.median(),p.ctr.median(),q.ctr.median()))

print('\n=== ВНУТРИ ДНА: что отделяет выживших от застрявших (n>=10 групп)')
c=m[m['эпоха']=='3_дно'].copy()
c['grp']=np.where(c.shows>500000,'выжившие',np.where(c.shows<10000,'застрявшие','середина'))
print(c.groupby('grp').agg(n=('shows','size'), ctr=('ctr','median'), rr=('read_rate','median'),
    слов=('n_words','median'), карт=('n_images','median'), ttr=('time_to_read_s','median'),
    мин_дочит=('min_per_read','median'), sim=('text_sim_prev','median'), яркость=('brightness','median'),
    насыщ=('saturation','median'), контраст=('contrast','median')).round(4).to_string())
print(pd.crosstab(c['регистр'],c['grp'],normalize='columns').round(3).to_string())
print(pd.crosstab(c['порог_входа'],c['grp'],normalize='columns').round(3).to_string())
print(pd.crosstab(c['фокус'],c['grp'],normalize='columns').round(3).to_string())
print('час публикации:'); print(c.groupby('grp').hour.describe().round(1).to_string())

print('\n=== ТО ЖЕ ДО СПАДА (правило 5): выжившие/застрявшие по тем же ОТНОСИТЕЛЬНЫМ порогам (верх/низ квинтиля показов)')
a=m[m['эпоха']=='1_до_спада'].copy()
lo,hi=np.percentile(a.shows,[20,80])
a['grp']=np.where(a.shows>=hi,'верх',np.where(a.shows<=lo,'низ','сер'))
print(a.groupby('grp').agg(n=('shows','size'), ctr=('ctr','median'), rr=('read_rate','median'),
    слов=('n_words','median'), мин_дочит=('min_per_read','median'), яркость=('brightness','median')).round(4).to_string())
print(pd.crosstab(a['регистр'],a['grp'],normalize='columns').round(3).to_string())
print(pd.crosstab(a['сцена'],a['grp'],normalize='columns').round(3).to_string())
c2=c.copy(); lo2,hi2=np.percentile(c2.shows,[20,80]); c2['grp']=np.where(c2.shows>=hi2,'верх',np.where(c2.shows<=lo2,'низ','сер'))
print('\nдно, те же квинтили:')
print(pd.crosstab(c2['сцена'],c2['grp'],normalize='columns').round(3).to_string())
print(pd.crosstab(c2['регистр'],c2['grp'],normalize='columns').round(3).to_string())
