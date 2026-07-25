# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
m = pd.read_pickle('out/full.pkl')
a=pd.read_pickle('out/art.pkl'); r=pd.read_pickle('out/rol.pkl'); p=pd.read_pickle('out/pos.pkl')
allp=pd.concat([a,r,p],ignore_index=True)
allp['ym']=allp['date'].dt.to_period('M').astype(str)
s=allp.groupby('ym')['subs'].sum()
base_gross = s.cumsum().shift(1).fillna(0)
NET = 88465/106029
base = base_gross*NET
mon = m.assign(ym=m.date.dt.to_period('M').astype(str)).groupby('ym').agg(
    n=('reads','size'), reads_sum=('reads','sum'), shows_sum=('shows','sum'), reads_med=('reads','median'))
mon['база_на_начало']=base.reindex(mon.index).round(0)
mon['дочит_на_подписчика_в_мес']=(mon.reads_sum/mon['база_на_начало']).round(2)
mon['дочит_медиана_/_база_%']=(mon.reads_med/mon['база_на_начало']*100).round(2)
print(mon.loc['2024-06':].to_string())
print()
print('Итого дочитываний статей: 2025H1 = %d, 2026H1 = %d' % (
    m[(m.date>='2025-01-01')&(m.date<'2025-07-01')].reads.sum(),
    m[(m.date>='2026-01-01')&(m.date<'2026-07-01')].reads.sum()))
print('Статей: 2025H1 = %d, 2026H1 = %d' % (
    len(m[(m.date>='2025-01-01')&(m.date<'2025-07-01')]), len(m[(m.date>='2026-01-01')&(m.date<'2026-07-01')])))
