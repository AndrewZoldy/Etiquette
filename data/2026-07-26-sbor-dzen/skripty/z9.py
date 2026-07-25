import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 140); pd.set_option('display.max_rows', 500)
art = pd.read_pickle('out/art.pkl'); rol = pd.read_pickle('out/rol.pkl'); pos = pd.read_pickle('out/pos.pkl')
m = pd.read_pickle('out/full_sim.pkl')
print('=== перцентили CTR по эпохам (без NaN)')
for ep in ['1_до_спада','2_склон','3_дно']:
    x = m[m['эпоха']==ep].dropna(subset=['ctr'])
    print(ep, 'n=%d' % len(x), ' '.join('p%d=%.3f' % (q, np.percentile(x.ctr, q)) for q in [5,10,25,50,75,90]))

# --- помесячный ряд
def mo(d): return d['date'].dt.to_period('M')
idx = pd.period_range('2023-02','2026-07',freq='M')
t = pd.DataFrame(index=idx)
t['n_art'] = mo(art).value_counts().reindex(idx).fillna(0)
t['n_rol'] = mo(rol).value_counts().reindex(idx).fillna(0)
t['n_pos'] = mo(pos).value_counts().reindex(idx).fillna(0)
t['nonart'] = t.n_rol + t.n_pos
t['share_nonart'] = t.nonart/(t.n_art+t.nonart)
t['art_med'] = art.groupby(mo(art)).shows.median().reindex(idx)
t['art_reads'] = art.groupby(mo(art)).reads.median().reindex(idx)
t['L'] = np.log10(t.art_med)
print('\n=== ряд')
print(t.round(3).to_string())

print('\n=== Спирмен: объём НЕ-статей (ролики+посты) в месяц t-k против медианы показов статей в месяц t')
tt = t.dropna(subset=['L'])
for k in range(0,5):
    x = t.nonart.shift(k).reindex(tt.index)
    v = pd.concat([x, tt.L], axis=1).dropna()
    print(' лаг %d: rho=%.3f (n=%d)' % (k, v.iloc[:,0].corr(v.iloc[:,1], method='spearman'), len(v)))
print('\nТО ЖЕ, но только ДО обвала (по июль 2025) — внутрипериодная проверка')
pre = tt[tt.index <= pd.Period('2025-07')]
for k in range(0,5):
    x = t.nonart.shift(k).reindex(pre.index)
    v = pd.concat([x, pre.L], axis=1).dropna()
    print(' лаг %d: rho=%.3f (n=%d)' % (k, v.iloc[:,0].corr(v.iloc[:,1], method='spearman'), len(v)))
print('\nТО ЖЕ, только ПОСЛЕ ноября 2025')
post = tt[tt.index >= pd.Period('2025-11')]
for k in range(0,5):
    x = t.nonart.shift(k).reindex(post.index)
    v = pd.concat([x, post.L], axis=1).dropna()
    print(' лаг %d: rho=%.3f (n=%d)' % (k, v.iloc[:,0].corr(v.iloc[:,1], method='spearman'), len(v)))

# --- ПОСТАТЕЙНО: сколько НЕ-статей канал выпустил в ±30 дней вокруг статьи, внутри эпохи
allp = pd.concat([rol.assign(k='rol')[['date','k']], pos.assign(k='pos')[['date','k']]])
dates = np.sort(allp.date.values)
m2 = m.copy()
def cnt(d, w):
    lo = np.searchsorted(dates, d - np.timedelta64(w,'D')); hi = np.searchsorted(dates, d + np.timedelta64(w,'D'))
    return hi-lo
for w in [7,30]:
    m2[f'nonart_{w}'] = [cnt(np.datetime64(x), w) for x in m2.date]
print('\n=== внутриэпоховая связь «не-статей вокруг» с показами статьи (Спирмен)')
for ep in ['1_до_спада','3_дно']:
    x = m2[m2['эпоха']==ep]
    for w in [7,30]:
        print('%s окно±%dд: rho(shows)=%.3f rho(ctr)=%.3f n=%d' % (ep, w,
              x[f'nonart_{w}'].corr(x.shows, method='spearman'), x[f'nonart_{w}'].corr(x.ctr, method='spearman'), len(x)))
print('\nтерцили не-статей за ±30д, медианы показов статей, внутри эпохи')
for ep in ['1_до_спада','3_дно']:
    x = m2[m2['эпоха']==ep].copy()
    x['t'] = pd.qcut(x['nonart_30'], 3, labels=['мало','средне','много'], duplicates='drop')
    print(ep); print(x.groupby('t', observed=True).agg(n=('shows','size'), nonart=('nonart_30','median'),
        med_shows=('shows','median'), med_ctr=('ctr','median')).round(3).to_string())
