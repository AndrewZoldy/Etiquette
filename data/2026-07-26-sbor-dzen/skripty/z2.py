import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 300)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + np.where(m['date'].dt.month <= 6, '1', '2')
E1, E2, E3 = '1_до_спада', '2_склон', '3_дно'
a = m[m['эпоха'] == E1]; c = m[m['эпоха'] == E3]

print('=== 0. база')
for nm, d in [('до', a), ('дно', c)]:
    print(nm, 'n=%d' % len(d), 'med shows %.0f' % d.shows.median(), 'med reads %.0f' % d.reads.median(),
          'med ctr %.4f' % d.ctr.median(), 'med rr %.3f' % d.read_rate.median())
print('ratio shows %.2f  reads %.2f' % (a.shows.median()/c.shows.median(), a.reads.median()/c.reads.median()))

print('\n=== 1. доли сцен по эпохам (%)')
tab = pd.crosstab(m['сцена'], m['эпоха'], normalize='columns')*100
tab['delta_п.п.'] = tab[E3]-tab[E1]
print(tab.round(1).sort_values('delta_п.п.'))
print('\nn по сценам/эпохам')
print(pd.crosstab(m['сцена'], m['эпоха']))

print('\n=== 2. внутрисценовые медианы показов и дочитываний (эпоха 1 vs 3), только группы n>=10 в обеих')
rows = []
for s in sorted(m['сцена'].unique()):
    A = a[a['сцена'] == s]; C = c[c['сцена'] == s]
    rows.append(dict(сцена=s, n1=len(A), n3=len(C),
                     shows1=A.shows.median(), shows3=C.shows.median(),
                     reads1=A.reads.median(), reads3=C.reads.median(),
                     ctr1=A.ctr.median(), ctr3=C.ctr.median()))
r = pd.DataFrame(rows)
r['shows_ratio'] = r.shows1/r.shows3
r['reads_ratio'] = r.reads1/r.reads3
print(r.round(3).to_string())

print('\n=== 3. Oaxaca-декомпозиция среднего log10(shows), эпоха1 -> эпоха3, по сценам')
def oaxaca(a, c, key, val='shows'):
    a = a.copy(); c = c.copy()
    a['L'] = np.log10(a[val].clip(lower=1)); c['L'] = np.log10(c[val].clip(lower=1))
    pa = a[key].value_counts(normalize=True); pc = c[key].value_counts(normalize=True)
    ma = a.groupby(key)['L'].mean(); mc = c.groupby(key)['L'].mean()
    ks = sorted(set(pa.index) | set(pc.index))
    pa = pa.reindex(ks).fillna(0); pc = pc.reindex(ks).fillna(0)
    # для отсутствующих категорий берём средний уровень эпохи
    ma = ma.reindex(ks); mc = mc.reindex(ks)
    ma_f = ma.fillna(a['L'].mean()); mc_f = mc.fillna(c['L'].mean())
    tot = c['L'].mean() - a['L'].mean()
    comp = float(((pc-pa)*ma_f).sum())           # эффект состава при старых уровнях
    within = float((pc*(mc_f-ma_f)).sum())       # эффект внутри категорий при новом составе
    return tot, comp, within, pd.DataFrame(dict(share1=pa, share3=pc, L1=ma, L3=mc,
                                                comp=(pc-pa)*ma_f, within=pc*(mc_f-ma_f)))
for key in ['сцена','функция','порог_входа','фокус']:
    for val in ['shows','reads']:
        tot, comp, within, det = oaxaca(a, c, key, val)
        print('\n%s / %s: total dlog=%.3f (=%.1fx), состав=%.3f (%.0f%%, =%.2fx), внутри=%.3f (%.0f%%, =%.2fx)'
              % (key, val, tot, 10**(-tot), comp, 100*comp/tot, 10**(-comp), within, 100*within/tot, 10**(-within)))
        if key in ('сцена','функция'):
            print(det.round(3).to_string())
