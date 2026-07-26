# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
D = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/'
m = pd.read_pickle(D + 'full.pkl')
m['date'] = pd.to_datetime(m['date'])
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['ceT'] = (m['comments_enabled'] == True)
rng = np.random.default_rng(20260726)

def bootci(a, b, stat=np.median, n=4000):
    a = np.asarray(a, float); b = np.asarray(b, float)
    r = np.empty(n)
    for i in range(n):
        r[i] = stat(rng.choice(a, len(a), True)) / max(stat(rng.choice(b, len(b), True)), 1e-9)
    return np.percentile(r, [2.5, 97.5])

print('=== B. ПОЛ по полугодиям, только ce=True ===')
rows = []
for h in ['2023H2', '2024H1', '2024H2', '2025H1', '2025H2', '2026H1', '2026H2']:
    for lab, sub in [('сырьё', m[m['half'] == h]), ('ce=True', m[(m['half'] == h) & m['ceT']])]:
        s = sub['shows'].dropna()
        if len(s) < 1: continue
        p10, p50, p90 = np.percentile(s, [10, 50, 90])
        rows.append(dict(half=h, вид=lab, n=len(s), lt10k=round((s < 1e4).mean(), 3), lt3k=round((s < 3e3).mean(), 3),
                         p10=int(p10), p50=int(p50), p90=int(p90), p90_p10=round(p90 / p10, 1),
                         rel_lt10pct=round((s < 0.10 * p50).mean(), 3)))
print(pd.DataFrame(rows).to_string(index=False))

print()
print('=== C. Квинтили CTR внутри эпохи дно ===')
for lab, sub in [('дно сырьё', m[m['эпоха'] == '3_дно']), ('дно ce=True', m[(m['эпоха'] == '3_дно') & m['ceT']]),
                 ('дно ce=False', m[(m['эпоха'] == '3_дно') & (m['comments_enabled'] == False)]),
                 ('до_спада ce=True', m[(m['эпоха'] == '1_до_спада') & m['ceT']])]:
    s = sub.dropna(subset=['ctr']).copy()
    s['q'] = pd.qcut(s['ctr'], 5, labels=[1, 2, 3, 4, 5])
    g = s.groupby('q', observed=True).agg(n=('shows', 'size'), ctr=('ctr', 'median'), shows=('shows', 'median'), reads=('reads', 'median'))
    print(lab, ' n=', len(s))
    print(g.to_string())
    print('  q5/q1 shows =', round(g['shows'].iloc[-1] / g['shows'].iloc[0], 2), ' reads =', round(g['reads'].iloc[-1] / max(g['reads'].iloc[0], 1), 1))
    print('  Спирмен ctr~shows =', round(s[['ctr', 'shows']].corr(method='spearman').iloc[0, 1], 3))

print()
print('=== D. Индекс сцены стол_еда, ce=True, по эпохам ===')
for ep in ['1_до_спада', '3_дно']:
    sub = m[(m['эпоха'] == ep) & m['ceT']]
    med_ep_r = sub['reads'].median(); med_ep_s = sub['shows'].median()
    st = sub[sub['сцена'] == 'стол_еда']
    ci = bootci(st['reads'], sub['reads'])
    print(f'{ep}: n_эпохи={len(sub)} мед_reads={med_ep_r:.0f} | стол_еда n={len(st)} мед={st["reads"].median():.0f} '
          f'индекс_reads={st["reads"].median()/med_ep_r:.2f} CI=[{ci[0]:.2f};{ci[1]:.2f}] индекс_shows={st["shows"].median()/med_ep_s:.2f}')
    # доля сцены
    print('   доля стол_еда в эпохе (ce=True):', round((sub['сцена'] == 'стол_еда').mean(), 3),
          ' на смеси:', round((m[m['эпоха'] == ep]['сцена'] == 'стол_еда').mean(), 3))

print()
print('=== E. Вторая рубрика: Светская жизнь Петербурга ===')
mask = m['title_studio'].astype(str).str.contains('етерб|ветск', case=False, regex=True, na=False)
sv = m[mask]
print('найдено по заголовку:', len(sv))
print(sv[['date', 'title_studio', 'shows', 'opens', 'reads', 'ctr', 'read_rate', 'comments_enabled']].to_string(index=False))
