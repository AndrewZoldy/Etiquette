import pandas as pd, numpy as np, re
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 140); pd.set_option('display.max_rows', 500)
m = pd.read_pickle('out/full_sim.pkl')
m['title'] = m['title_public'].fillna(m['title_studio']).astype(str)
VERB = re.compile(r'\b(как|можно ли|почему|зачем|что делать|нужно ли|стоит ли|кто|когда|где|надо ли|правда ли)\b', re.I)
def reg(t):
    t = t.strip()
    if '?' in t or VERB.search(t): return 'вопрос_читателя'
    if re.search(r'\b\w+(ть|тся|ет|ют|ит|ат|ят|ете|йте|ла|ло|ли)\b', t, re.I): return 'утверждение'
    return 'номенклатура'
m['регистр'] = m['title'].map(reg)
E1, E3 = '1_до_спада', '3_дно'
d = m[m['эпоха'].isin([E1, E3])].copy()
d['post'] = (d['эпоха'] == E3).astype(float)
d['y'] = np.log10(d.shows.clip(lower=1))
d['yr'] = np.log10(d.reads.clip(lower=1))

def ols(y, X):
    X = np.asarray(X, float); y = np.asarray(y, float)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X@b
    s2 = resid@resid/(len(y)-X.shape[1])
    se = np.sqrt(np.diag(s2*np.linalg.pinv(X.T@X)))
    return b, se

def design(cols):
    parts = [np.ones((len(d),1)), d[['post']].values]
    names = ['const','post']
    for c in cols:
        du = pd.get_dummies(d[c], prefix=c, drop_first=True).astype(float)
        parts.append(du.values); names += list(du.columns)
    return np.hstack(parts), names

print('=== эффект эпохи на log10(показы) при разных наборах контентных контролей')
base = None
for cols in [[], ['сцена'], ['функция'], ['сцена','функция'], ['сцена','функция','регистр','порог_входа','фокус'],
             ['сцена','функция','регистр','порог_входа','фокус','вопрос','цифра_в_заголовке','негативная_рамка','обращение_вы','конкретный_якорь','спорность','серийная_рубрика']]:
    X, names = design(cols)
    b, se = ols(d.y.values, X)
    coef = b[1]
    if base is None: base = coef
    print('контроли %-90s post=%.3f (=%.1fx), se=%.3f, объяснено смесью: %.1f%%'
          % (','.join(cols) if cols else 'нет', coef, 10**(-coef), se[1], 100*(1-coef/base)))
print()
base = None
for cols in [[], ['сцена','функция','регистр','порог_входа','фокус']]:
    X, names = design(cols)
    b, se = ols(d.yr.values, X)
    if base is None: base = b[1]
    print('reads: контроли %-50s post=%.3f (=%.1fx), объяснено смесью: %.1f%%' % (','.join(cols) if cols else 'нет', b[1], 10**(-b[1]), 100*(1-b[1]/base)))

# ---- ПИК против ДНА как в Факте 1
print('\n=== то же на окне Факта 1: янв-июл 2025 vs ноя2025-июн2026')
p = m[(m.date >= '2025-01-01') & (m.date < '2025-08-01')].copy()
q = m[(m.date >= '2025-11-01') & (m.date < '2026-07-01')].copy()
print('n пик=%d дно=%d; медианы показов %.0f -> %.0f (%.1fx); дочит %.0f -> %.0f (%.1fx)'
      % (len(p), len(q), p.shows.median(), q.shows.median(), p.shows.median()/q.shows.median(),
         p.reads.median(), q.reads.median(), p.reads.median()/q.reads.median()))
pa = p['сцена'].value_counts(normalize=True); pc = q['сцена'].value_counts(normalize=True)
w = q['сцена'].map(pa/pc).values
def wmed(v, w):
    o = np.argsort(v); v = np.asarray(v)[o]; w = np.asarray(w, float)[o]
    return float(v[np.searchsorted(np.cumsum(w)/w.sum(), 0.5)])
print('дно, перевзвешенное к составу сцен пика: показы %.0f (факт %.0f)' % (wmed(q.shows.values, w), q.shows.median()))
print('доля log-падения, объяснённая составом сцен: %.1f%%' %
      (100*(np.log10(wmed(q.shows.values, w))-np.log10(q.shows.median()))/(np.log10(p.shows.median())-np.log10(q.shows.median()))))
# то же на связке сцена+функция+регистр
key = p['сцена']+'|'+p['функция']+'|'+p['регистр']; key3 = q['сцена']+'|'+q['функция']+'|'+q['регистр']
pa = key.value_counts(normalize=True); pc = key3.value_counts(normalize=True)
w = key3.map(pa).fillna(0)/key3.map(pc)
w = w.fillna(0).values
if w.sum() > 0:
    print('дно, перевзвешенное к составу сцена+функция+регистр: %.0f' % wmed(q.shows.values, w))
    print('доля log-падения: %.1f%%' % (100*(np.log10(wmed(q.shows.values, w))-np.log10(q.shows.median()))/(np.log10(p.shows.median())-np.log10(q.shows.median()))))

print('\n=== «неизменный» срез: бытовая + польза/разъяснение + вопрос_читателя (ядро канала)')
core = m[(m['порог_входа']=='бытовая') & (m['функция'].isin(['польза','разъяснение_нормы'])) & (m['регистр']=='вопрос_читателя')]
for ep in [E1, '2_склон', E3]:
    x = core[core['эпоха']==ep]
    print('%s n=%d med_shows=%.0f med_reads=%.0f med_ctr=%.3f' % (ep, len(x), x.shows.median(), x.reads.median(), x.ctr.median()))
x1 = core[core['эпоха']==E1]; x3 = core[core['эпоха']==E3]
print('ядро упало в %.1fx по показам, %.1fx по дочитываниям (весь канал: 8.5x / 10.4x)'
      % (x1.shows.median()/x3.shows.median(), x1.reads.median()/x3.reads.median()))

print('\n=== перцентили CTR по эпохам')
for ep in [E1, '2_склон', E3]:
    x = m[m['эпоха']==ep]
    print(ep, 'n=%d' % len(x), ' '.join('p%d=%.3f' % (q, np.percentile(x.ctr, q)) for q in [10,25,50,75,90]))
