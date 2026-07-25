# -*- coding: utf-8 -*-
import sys, io, json, os, glob, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
from scipy.stats import spearmanr
m = pd.read_pickle('out/full.pkl').sort_values('date').reset_index(drop=True)
SUBS = 88465

print('=== A. Вовлечённость с контролем возраста (эпоха дно, age>=180) ===')
pre = m[m['эпоха']=='1_до_спада']
bot = m[m['эпоха']=='3_дно']
bot_old = bot[bot['age_days']>=180]
print('до спада n=%d: comm/read=%.4f likes/read=%.4f' % (len(pre), pre.comments_per_read.median(), pre.likes_per_read.median()))
print('дно, age>=180 n=%d: comm/read=%.4f likes/read=%.4f' % (len(bot_old), bot_old.comments_per_read.median(), bot_old.likes_per_read.median()))
bot_new = bot[bot['age_days']<180]
print('дно, age<180 n=%d: comm/read=%.4f likes/read=%.4f' % (len(bot_new), bot_new.comments_per_read.median(), bot_new.likes_per_read.median()))
print('Спирмен age_days x comments_per_read внутри дна: %.3f' % spearmanr(bot.age_days, bot.comments_per_read, nan_policy='omit').statistic)
# сопоставимый возраст: до спада тоже ограничим age>=180 (все такие)
print()
print('=== B. Активация базы подписчиков: reads/подписчик по месяцам ===')
mm = m.groupby('ym').agg(n=('shows','size'), sh=('shows','median'), rd=('reads','median'),
                          sb=('subs','median'), spr=('subs_per_read','median'),
                          lpr=('likes_per_read','median'), cpr=('comments_per_read','median'))
mm = mm[mm.n>=10]
mm['reads_per_sub_%'] = mm.rd/SUBS*100
mm['shows_per_sub'] = mm.sh/SUBS
print(mm.to_string(float_format=lambda x: '%.4f' % x))

print()
print('=== C. Сезонность: медиана показов по календарному месяцу внутри каждого года ===')
m['year']=m.date.dt.year; m['mon']=m.date.dt.month
piv = m.pivot_table(index='mon', columns='year', values='shows', aggfunc=['median','size'])
print(piv.to_string(float_format=lambda x: '%.0f' % x))

print()
print('=== D. Насыщение темы: сколько статей той же сцены вышло ДО этой ===')
m['prior_same_scene'] = 0
cnt = collections.Counter()
vals=[]
for i,r in m.iterrows():
    vals.append(cnt[r['сцена']])
    cnt[r['сцена']] += 1
m['prior_same_scene']=vals
for ep in ['1_до_спада','3_дно']:
    d=m[m['эпоха']==ep]
    print(ep, 'n=%d Спирмен prior_same_scene x shows = %.3f' % (len(d), spearmanr(d.prior_same_scene, d.shows, nan_policy='omit').statistic))
    print('   ', ep, 'Спирмен prior_same_scene x ctr = %.3f' % spearmanr(d.prior_same_scene, d.ctr, nan_policy='omit').statistic)
# внутри стол_еда на дне
for ep in ['1_до_спада','3_дно']:
    d=m[(m['эпоха']==ep)&(m['сцена']=='стол_еда')]
    if len(d)>=10:
        print('стол_еда', ep, 'n=%d  Спирмен prior x shows=%.3f  prior x ctr=%.3f' % (len(d), spearmanr(d.prior_same_scene,d.shows,nan_policy='omit').statistic, spearmanr(d.prior_same_scene,d.ctr,nan_policy='omit').statistic))
