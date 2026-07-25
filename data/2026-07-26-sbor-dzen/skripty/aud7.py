# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
m = pd.read_pickle('out/full.pkl').sort_values('date').reset_index(drop=True)
a=pd.read_pickle('out/art.pkl'); r=pd.read_pickle('out/rol.pkl'); p=pd.read_pickle('out/pos.pkl')
allp=pd.concat([a,r,p],ignore_index=True); allp['ym']=allp['date'].dt.to_period('M').astype(str)
s=allp.groupby('ym')['subs'].sum(); base=(s.cumsum().shift(1).fillna(0))*(88465/106029)
mon=m.assign(ym=m.date.dt.to_period('M').astype(str)).groupby('ym').agg(n=('reads','size'),reads_med=('reads','median'),reads_sum=('reads','sum'))
mon['база']=base.reindex(mon.index).round(0)
mon['мед_дочит_/_база_%']=(mon.reads_med/mon['база']*100).round(2)
mon['дочит_на_подписч_в_мес']=(mon.reads_sum/mon['база']).round(2)
print('=== Полный ряд (только месяцы с n>=10 статей) ===')
print(mon[mon.n>=10].to_string())

print()
print('=== K. Тест разбавления: статьи после виральной волны vs в «тихие» периоды (эпоха дно) ===')
bot=m[m['эпоха']=='3_дно'].copy()
viral_dates = m[(m.shows>1_000_000)].date.tolist()
def after_viral(d, win=14):
    return any(0 < (d-v).days <= win for v in viral_dates)
bot['после_вирала']=bot.date.map(after_viral)
for k,d in bot.groupby('после_вирала'):
    print('после_вирала=%s n=%d  медиана CTR=%.4f  медиана показов=%.0f  медиана дочитываний=%.0f'%(k,len(d),d.ctr.median(),d.shows.median(),d.reads.median()))
print()
print('=== L. Устойчивость: то же до спада (плацебо-проверка) ===')
pre=m[m['эпоха']=='1_до_спада'].copy(); pre['после_вирала']=pre.date.map(after_viral)
for k,d in pre.groupby('после_вирала'):
    print('после_вирала=%s n=%d  медиана CTR=%.4f  медиана показов=%.0f'%(k,len(d),d.ctr.median(),d.shows.median()))

print()
print('=== M. Лайки на дочитывание при сопоставимом возрасте (>=300 дней у обеих эпох невозможно; берём >=240) ===')
for lab,d in [('до спада', m[m['эпоха']=='1_до_спада']), ('дно age>=240', m[(m['эпоха']=='3_дно')&(m.age_days>=240)])]:
    print('%s n=%d likes_per_read=%.4f comments_per_read=%.4f min_per_read=%.3f read_rate=%.3f'%(
        lab,len(d),d.likes_per_read.median(),d.comments_per_read.median(),d.min_per_read.median(),d.read_rate.median()))
