# -*- coding: utf-8 -*-
"""Досчёт: накопление комментариев по суткам; длина предложения без рубрики."""
import pandas as pd, numpy as np, os, json
from scipy import stats
np.random.seed(20260726)
pd.set_option('display.width', 320); pd.set_option('display.max_columns', 60)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
full = pd.read_pickle(os.path.join(OUT,'full.pkl'))
ves  = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
V = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date').reset_index(drop=True)
V['num']=np.arange(1,11)
both = full[full['src']=='both'].copy()
isv = both['title_studio'].str.startswith('Светская жизнь Петербурга')

print('='*120)
print('R5(д)-ПРОКСИ: накопление комментариев по суткам от публикации (created_ts, мс)')
print('='*120)
rows=[]
for r in V.itertuples():
    p = os.path.join(OUT,'comments', r.oid+'.json')
    d = json.load(open(p, encoding='utf-8'))
    cs = d['comments']
    pub = r.date.timestamp()
    age = np.array([c['created_ts']/1000.0 - pub for c in cs if c.get('created_ts')])/86400.0
    age = age[age >= -0.1]
    rows.append(dict(выпуск=r.title_studio.replace('Светская жизнь Петербурга: ',''), n=len(age),
        д24=(age<=1).mean(), д48=(age<=2).mean(), д72=(age<=3).mean(), д96=(age<=4).mean(),
        д7=(age<=7).mean(), мед_возраст_дн=np.median(age), макс_дн=age.max()))
A = pd.DataFrame(rows)
print(A.to_string(index=False))
print()
print('МЕДИАНЫ ПО 10 ВЫПУСКАМ: 24 ч = %.3f ; 48 ч = %.3f ; 72 ч = %.3f ; 96 ч = %.3f ; 7 дн = %.3f'
      % (A['д24'].median(), A['д48'].median(), A['д72'].median(), A['д96'].median(), A['д7'].median()))
print('агрегат по всем комментариям рубрики: 24 ч = %.3f ; 48 ч = %.3f ; 72 ч = %.3f'
      % tuple(np.average([A['д24'],A['д48'],A['д72']], axis=1, weights=A['n'])))
# то же по каналу-дну для контекста
d3 = both[(both['эпоха']=='3_дно') & (~isv)]
rows2=[]
for r in d3.itertuples():
    p = os.path.join(OUT,'comments', r.oid+'.json')
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding='utf-8'))
    cs = d.get('comments') or []
    if len(cs) < 5: continue
    pub = r.date.timestamp()
    age = np.array([c['created_ts']/1000.0 - pub for c in cs if c.get('created_ts')])/86400.0
    age = age[age>=-0.1]
    if len(age)<5: continue
    rows2.append(dict(n=len(age), д24=(age<=1).mean(), д48=(age<=2).mean(), д72=(age<=3).mean(), д7=(age<=7).mean()))
A2 = pd.DataFrame(rows2)
print('канал (дно, >=5 комментариев, n=%d статей): медианы 24 ч = %.3f ; 48 ч = %.3f ; 72 ч = %.3f ; 7 дн = %.3f'
      % (len(A2), A2['д24'].median(), A2['д48'].median(), A2['д72'].median(), A2['д7'].median()))
print()
print('ВЫВОД по решающему правилу (д): порог «>=60%% показов за первые двое суток».')
print('  показов по дням в данных НЕТ. Прокси по комментариям: у рубрики %.1f%% за 48 ч, у канала %.1f%% за 48 ч.'
      % (100*A['д48'].median(), 100*A2['д48'].median()))
print('  прокси НЕ измеряет показы и не может ни принять, ни отклонить рекомендацию «окно 3-4 дня».')

print()
print('='*120)
print('ПЕРЕПРОВЕРКА ТЕЗИСА ДОСЬЕ О ДЛИНЕ ПРЕДЛОЖЕНИЯ (>16 слов -> 30,5%) — БЕЗ РУБРИКИ')
print('='*120)
tf = pd.read_pickle(os.path.join(OUT,'text_feats.pkl'))
M = both.merge(tf[['oid','слов_в_предложении_мед']], on='oid', how='inner')
M['рубрика'] = M['title_studio'].str.startswith('Светская жизнь Петербурга')
M['bin'] = pd.cut(M['слов_в_предложении_мед'], [0,10,13,16,100], labels=['<=10','10-13','13-16','>16'])
for nm, d in [('ВСЕ 620 (как в досье)', M), ('БЕЗ 10 выпусков рубрики', M[~M['рубрика']]),
              ('дно, все', M[M['эпоха']=='3_дно']), ('дно, БЕЗ рубрики', M[(M['эпоха']=='3_дно') & (~M['рубрика'])])]:
    g = d.groupby('bin', observed=True).agg(n=('oid','size'), дочитываемость=('read_rate','median'), CTR=('ctr','median'), дочит=('reads','median'))
    print('---', nm); print(g.to_string())
print()
print('в группе «>16 слов» по всему каналу: всего %d, из них рубрика %d (%.0f%%)'
      % ((M['bin']=='>16').sum(), ((M['bin']=='>16')&M['рубрика']).sum(), 100*((M['bin']=='>16')&M['рубрика']).mean()/max((M['bin']=='>16').mean(),1e-9)))
print('в группе «>16 слов» на дне: всего %d, из них рубрика %d'
      % (((M['bin']=='>16')&(M['эпоха']=='3_дно')).sum(), ((M['bin']=='>16')&(M['эпоха']=='3_дно')&M['рубрика']).sum()))
