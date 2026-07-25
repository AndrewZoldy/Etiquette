# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
m = pd.read_pickle('out/full.pkl')
pre=m[m['эпоха']=='1_до_спада']; bot=m[m['эпоха']=='3_дно']
print('=== N. Разложение падения медианы дочитываний по эпохам ===')
print('до спада: медиана %.0f  среднее %.0f  мед/сред %.4f' % (pre.reads.median(), pre.reads.mean(), pre.reads.median()/pre.reads.mean()))
print('дно     : медиана %.0f  среднее %.0f  мед/сред %.4f' % (bot.reads.median(), bot.reads.mean(), bot.reads.median()/bot.reads.mean()))
print('падение медианы = %.2fx ;  падение среднего = %.2fx ;  рост неравенства = %.2fx' % (
    pre.reads.median()/bot.reads.median(), pre.reads.mean()/bot.reads.mean(),
    (pre.reads.median()/pre.reads.mean())/(bot.reads.median()/bot.reads.mean())))
print('в логарифмах: доля неравенства = %.0f%%, доля общего объёма = %.0f%%' % (
    100*np.log((pre.reads.median()/pre.reads.mean())/(bot.reads.median()/bot.reads.mean()))/np.log(pre.reads.median()/bot.reads.median()),
    100*np.log(pre.reads.mean()/bot.reads.mean())/np.log(pre.reads.median()/bot.reads.median())))

print()
print('=== O. Вклад «стол_еда» в медиану дна ===')
b2=bot[bot['сцена']!='стол_еда']
print('дно всё: n=%d медиана дочит=%.0f медиана показов=%.0f' % (len(bot), bot.reads.median(), bot.shows.median()))
print('дно без стол_еда: n=%d медиана дочит=%.0f медиана показов=%.0f' % (len(b2), b2.reads.median(), b2.shows.median()))
p2=pre[pre['сцена']!='стол_еда']
print('до спада всё: медиана дочит=%.0f | без стол_еда: n=%d медиана=%.0f' % (pre.reads.median(), len(p2), p2.reads.median()))
print('падение с стол_еда = %.1fx, без стол_еда = %.1fx' % (pre.reads.median()/bot.reads.median(), p2.reads.median()/b2.reads.median()))
print()
print('=== P. Доля «выработанных» справочных сцен в объёме публикаций ===')
for lab,d in [('до спада',pre),('дно',bot)]:
    v=d['сцена'].value_counts(normalize=True)*100
    print(lab, {k: round(x,1) for k,x in v.head(6).items()})
print()
print('=== Q. Функция: доля публикаций ===')
for lab,d in [('до спада',pre),('дно',bot)]:
    v=d['функция'].value_counts(normalize=True)*100
    print(lab, {k: round(x,1) for k,x in v.items()})
