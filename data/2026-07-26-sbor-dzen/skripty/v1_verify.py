# -*- coding: utf-8 -*-
"""Независимая проверка критика, раунд 2. Пишу с нуля."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd

pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 60)
D = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/'
m = pd.read_pickle(D + 'full.pkl')
print('shape', m.shape)
print('COLS:', list(m.columns))
print()
print('--- есть ли comments_enabled / modificationTime ---')
for c in m.columns:
    lc = c.lower()
    if 'comment' in lc or 'modif' in lc or 'publish' in lc or 'time' in lc or 'enab' in lc:
        print('  ', c, m[c].dtype, 'nonnull', m[c].notna().sum())
print()
m['date'] = pd.to_datetime(m['date'])
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
ce = m['comments_enabled']
print('comments_enabled value_counts(dropna=False):')
print(ce.value_counts(dropna=False))
m['ceT'] = (ce == True)
m['ceF'] = (ce == False)
print()
print('=== A. Класс ce=False ===')
f = m[m['ceF']]
print('n =', len(f), ' окно:', f['date'].min().date(), '->', f['date'].max().date())
print('дни недели:', f['date'].dt.dayofweek.value_counts().sort_index().to_dict(), '(0=пн)')
print('показов >1e6:', (f['shows'] > 1e6).sum(), sorted(f.loc[f['shows'] > 1e6, 'shows'].tolist(), reverse=True))
print('медиана shows', f['shows'].median(), 'медиана reads', f['reads'].median())
print('p10/p50/p90 shows', np.percentile(f['shows'], [10, 50, 90]).round(0))
print('доля <3k', round((f['shows'] < 3000).mean(), 3), ' <10k', round((f['shows'] < 10000).mean(), 3))
print('сцены:', f['сцена'].value_counts().to_dict())
print('серийная_рубрика:', f['серийная_рубрика'].value_counts(dropna=False).to_dict())
w = m[(m['date'] >= '2025-09-16') & (m['date'] <= '2026-05-21')]
print()
print('в окне серии всего', len(w), ' ceF', w['ceF'].sum(), ' ceT', w['ceT'].sum())
tue_thu = w['date'].dt.dayofweek.isin([1, 3])
print('таблица 2x2 (слот вт/чт x флаг):')
print(pd.crosstab(np.where(tue_thu, 'вт/чт', 'др.дни'), np.where(w['ceF'], 'ce=False', 'ce=True')))
print('медианы reads в клетках:')
print(w.groupby([np.where(tue_thu, 'вт/чт', 'др.дни'), np.where(w['ceF'], 'F', 'T')])['reads'].agg(['size', 'median']))
