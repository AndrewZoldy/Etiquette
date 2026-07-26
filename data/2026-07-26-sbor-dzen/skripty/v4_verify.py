# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
D = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/'
m = pd.read_pickle(D + 'full.pkl')
m['date'] = pd.to_datetime(m['date'])
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['ceT'] = (m['comments_enabled'] == True)
m['svet'] = m['title_studio'].astype(str).str.startswith('Светская жизнь Петербурга')
m['cl2'] = m['ceT'] & ~m['svet']
rng = np.random.default_rng(20260726)

def rci(a, b, n=4000):
    a = np.asarray(a, float); b = np.asarray(b, float); r = np.empty(n)
    for i in range(n):
        r[i] = np.median(rng.choice(a, len(a), True)) / max(np.median(rng.choice(b, len(b), True)), 1e-9)
    return np.percentile(r, [2.5, 97.5])

print('=== K. Смесь по порог_входа/функция: 2024H2 / 2025H1 / 2026H1 (ce=True) ===')
sub = m[m['ceT'] & m['half'].isin(['2024H1', '2024H2', '2025H1', '2026H1'])]
for col in ['порог_входа', 'функция']:
    print(col); print((pd.crosstab(sub['half'], sub[col], normalize='index') * 100).round(1).to_string())
print('n_words:', sub.groupby('half')['n_words'].median().to_dict())

print()
print('=== L. Идентифицируем ли ПОДЪЁМ? (старшие статьи имеют МЕНЬШЕ дочитываний -> накопление тут ни при чём) ===')
t = sub.groupby('half').agg(n=('reads', 'size'), age=('age_days', 'median'), shows=('shows', 'median'),
                            opens=('opens', 'median'), reads=('reads', 'median'), ctr=('ctr', 'median'), rr=('read_rate', 'median'))
print(t.round(3).to_string())
print('2024H1 старше 2025H1 на', int(t.loc['2024H1', 'age'] - t.loc['2025H1', 'age']), 'дней, но reads в',
      round(t.loc['2025H1', 'reads'] / t.loc['2024H1', 'reads'], 1), 'раза МЕНЬШЕ -> подъём реален без возрастной модели')

print()
print('=== M. Стандартизация ПОДЪЁМА: 2024H2 -> 2025H1, ce=True, веса по (сцена) и (сцена|функция|порог) ===')
def stand(dfA, dfB, keys, minn=5, val='reads'):
    """медиана B, перевзвешенная к составу A (веса = доля ячейки в A / доля в B)"""
    A = dfA.copy(); B = dfB.copy()
    A['cell'] = A[keys].astype(str).agg('|'.join, axis=1); B['cell'] = B[keys].astype(str).agg('|'.join, axis=1)
    big = B['cell'].value_counts(); keep = set(big[big >= minn].index)
    A['cell'] = np.where(A['cell'].isin(keep), A['cell'], 'ПРОЧЕЕ'); B['cell'] = np.where(B['cell'].isin(keep), B['cell'], 'ПРОЧЕЕ')
    pa = A['cell'].value_counts(normalize=True); pb = B['cell'].value_counts(normalize=True)
    B = B[B['cell'].isin(pa.index)]
    w = B['cell'].map(lambda c: pa.get(c, 0) / pb.get(c, 1e-9)).values
    x = B[val].values.astype(float); o = np.argsort(x); x, w = x[o], w[o]
    cw = np.cumsum(w); p = (cw - 0.5 * w) / w.sum()
    return float(np.interp(0.5, p, x)), int((big >= minn).sum())

pairs = [('подъём 2024H2->2025H1', m[m['cl2'] & (m['half'] == '2024H2')], m[m['cl2'] & (m['half'] == '2025H1')]),
         ('падение 2025H1->2026H1', m[m['cl2'] & (m['half'] == '2025H1')], m[m['cl2'] & (m['half'] == '2026H1')]),
         ('до_спада->дно', m[m['cl2'] & (m['эпоха'] == '1_до_спада')], m[m['cl2'] & (m['эпоха'] == '3_дно')])]
for nm, A, B in pairs:
    raw = A['reads'].median() / B['reads'].median()
    r1, k1 = stand(A, B, ['сцена'])
    r2, k2 = stand(A, B, ['сцена', 'функция'])
    r3, k3 = stand(A, B, ['сцена', 'функция', 'порог_входа'])
    ci = rci(A['reads'], B['reads'])
    print(f'{nm:24s} nA={len(A):3d} nB={len(B):3d} сырое={raw:6.2f} CI=[{ci[0]:.2f};{ci[1]:.2f}] '
          f'| станд.сцена={A["reads"].median()/r1:5.2f}(k={k1}) сцена+функц={A["reads"].median()/r2:5.2f}(k={k2}) тройка={A["reads"].median()/r3:5.2f}(k={k3})')

print()
print('=== N. Локализация ступени на ДВОЙНОЙ чистке, месячные медианы ===')
mm = m[m['cl2'] & (m['date'] >= '2025-05-01')].copy()
mm['ym2'] = mm['date'].dt.to_period('M').astype(str)
g = mm.groupby('ym2').agg(n=('reads', 'size'), shows=('shows', 'median'), reads=('reads', 'median'), age=('age_days', 'median'))
print(g.round(0).to_string())
print()
print('стыки "3 мес до / 3 мес после", двойная чистка:')
for cut in pd.period_range('2025-08', '2026-05', freq='M'):
    c = cut.to_timestamp()
    a = m[m['cl2'] & (m['date'] >= c - pd.DateOffset(months=3)) & (m['date'] < c)]['reads']
    b = m[m['cl2'] & (m['date'] >= c) & (m['date'] < c + pd.DateOffset(months=3))]['reads']
    if len(a) < 10 or len(b) < 10: continue
    ci = rci(a.values, b.values)
    star = ' <== CI исключает 1' if ci[0] > 1 else ''
    print(f'  {cut}: n={len(a)}/{len(b)} отн={a.median()/max(b.median(),1):6.2f} CI=[{ci[0]:5.2f};{ci[1]:7.2f}]{star}')

print()
print('=== O. Амплитуда ступени: пик (май-сен 2025) vs дно с цензом (ноя25-мар26), двойная чистка ===')
pk = m[m['cl2'] & (m['date'] >= '2025-05-01') & (m['date'] < '2025-10-01')]
bt = m[m['cl2'] & (m['date'] >= '2025-11-01') & (m['date'] < '2026-04-01')]
for met in ['shows', 'opens', 'reads']:
    ci = rci(pk[met].values, bt[met].values)
    print(f'  {met:6s} пик n={len(pk)} мед={pk[met].median():10.0f} | дно n={len(bt)} мед={bt[met].median():9.0f} '
          f'отн={pk[met].median()/bt[met].median():5.2f} CI=[{ci[0]:.2f};{ci[1]:.2f}]')
print()
print('=== P. 2026H1 (двойная чистка, ценз ноя25-мар26) против доспадовых окон ===')
for base in ['2023H2', '2024H1', '2024H2']:
    A = m[m['cl2'] & (m['half'] == base)]
    for met in ['shows', 'opens', 'reads']:
        ci = rci(A[met].values, bt[met].values)
        print(f'  {base} / дно_ценз {met:6s}: {A[met].median():10.0f} / {bt[met].median():9.0f} = {A[met].median()/bt[met].median():5.2f}  CI=[{ci[0]:.2f};{ci[1]:.2f}]{"  СОДЕРЖИТ 1" if ci[0]<1<ci[1] else ""}')
