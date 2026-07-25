import pandas as pd, numpy as np, re
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['title'] = m['title_public'].fillna(m['title_studio']).astype(str)
E1, E2, E3 = '1_до_спада', '2_склон', '3_дно'
a = m[m['эпоха']==E1]; c = m[m['эпоха']==E3]

def wmed(v, w):
    o = np.argsort(v); v = np.asarray(v)[o]; w = np.asarray(w, float)[o]
    cw = np.cumsum(w)/w.sum()
    return float(v[np.searchsorted(cw, 0.5)])

print('=== КОНТРФАКТИК 1: дно, перевзвешенное к составу сцен эпохи 1')
pa = a['сцена'].value_counts(normalize=True); pc = c['сцена'].value_counts(normalize=True)
w = c['сцена'].map(pa/pc)
print('факт медиана дна: %.0f ; перевзвешенная к старому составу: %.0f' % (c.shows.median(), wmed(c.shows.values, w.values)))
print('факт reads: %.0f ; перевзвешенная: %.0f' % (c.reads.median(), wmed(c.reads.values, w.values)))
print('медиана эпохи 1: %.0f (reads %.0f)' % (a.shows.median(), a.reads.median()))

print('\n=== КОНТРФАКТИК 2: дно без стол_еда')
cn = c[c['сцена']!='стол_еда']
print('n=%d медиана показов %.0f, дочитываний %.0f' % (len(cn), cn.shows.median(), cn.reads.median()))
an = a[a['сцена']!='стол_еда']
print('эпоха1 без стол_еда: n=%d медиана %.0f, reads %.0f -> падение %.1fx / %.1fx'
      % (len(an), an.shows.median(), an.reads.median(), an.shows.median()/cn.shows.median(), an.reads.median()/cn.reads.median()))

print('\n=== КОНТРФАКТИК 3: доля падения медианы, объяснимая ТОЛЬКО провалом стол_еда')
# заменяем показы статей стол_еда на дне их квантильными аналогами из стол_еда эпохи 1
se1 = np.sort(a[a['сцена']=='стол_еда'].shows.values); se3 = c[c['сцена']=='стол_еда']
q = se3.shows.rank(pct=True).values
imput = np.quantile(se1, q)
mix = np.concatenate([cn.shows.values, imput])
print('дно с «вылеченной» стол_еда: медиана %.0f (факт %.0f, эпоха1 %.0f)' % (np.median(mix), c.shows.median(), a.shows.median()))
print('объяснённая доля log-падения: %.0f%%' % (100*(np.log10(np.median(mix))-np.log10(c.shows.median()))/(np.log10(a.shows.median())-np.log10(c.shows.median()))))

print('\n=== стол_еда по месяцам (дно)')
g = c[c['сцена']=='стол_еда'].groupby(c['date'].dt.to_period('M'))
print(g.agg(n=('shows','size'), med_shows=('shows','median'), med_reads=('reads','median'), med_ctr=('ctr','median')).to_string())
print('\n=== стол_еда по полугодиям, доля узкая / познавательное')
se = m[m['сцена']=='стол_еда'].copy()
se['half'] = se['date'].dt.year.astype(str)+'H'+np.where(se['date'].dt.month<=6,'1','2')
print(se.groupby('half').agg(n=('shows','size'), med=('shows','median'),
      узкая=('порог_входа', lambda s:(s=='узкая').mean()),
      познават=('функция', lambda s:(s=='познавательное').mean()),
      вопрос=('вопрос','mean'), якорь=('конкретный_якорь','mean'), цифра=('цифра_в_заголовке','mean'),
      негатив=('негативная_рамка','mean'), спорн=('спорность','mean'), слов=('n_words','median')).round(3).to_string())

print('\n=== узкая/бытовая внутри стол_еда: эпоха1 vs дно (медианы показов)')
for ep, d in [('до', a), ('дно', c)]:
    x = d[d['сцена']=='стол_еда']
    for p in ['бытовая','узкая']:
        y = x[x['порог_входа']==p]
        print('%s %s n=%d med_shows=%.0f med_reads=%.0f med_ctr=%.3f' % (ep, p, len(y), y.shows.median(), y.reads.median(), y.ctr.median()))
