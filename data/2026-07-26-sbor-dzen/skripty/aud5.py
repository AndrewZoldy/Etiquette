# -*- coding: utf-8 -*-
import sys, io, json, os, glob, collections, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
from scipy.stats import spearmanr
m = pd.read_pickle('out/full.pkl').sort_values('date').reset_index(drop=True)

STOP=set('и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех никогда можно при наконец два об другой хоть после над больше тот через эти нас про всего них какая много разве три эту моя впрочем свою этой перед иногда лучше чуть том нельзя такой им более всегда конечно всю между'.split())
def toks(s):
    return set(w for w in re.findall(r'[а-яёa-z]+', str(s).lower()) if len(w)>3 and w not in STOP)
T=[toks(t) for t in m.title_studio]
mx=[]
for i in range(len(m)):
    best=0.0
    for j in range(max(0,i-120), i):
        a,b=T[i],T[j]
        if a and b:
            jac=len(a&b)/len(a|b)
            if jac>best: best=jac
    mx.append(best)
m['title_repeat']=mx
print('=== H. Повтор темы в заголовке (max Jaccard к 120 предыдущим) ===')
for ep in ['1_до_спада','3_дно']:
    d=m[m['эпоха']==ep]
    print(ep,'n=%d медиана повтора=%.3f  Спирмен повтор x shows=%.3f  x ctr=%.3f'%(
        len(d), d.title_repeat.median(),
        spearmanr(d.title_repeat,d.shows,nan_policy='omit').statistic,
        spearmanr(d.title_repeat,d.ctr,nan_policy='omit').statistic))
    hi=d[d.title_repeat>=d.title_repeat.quantile(.75)]; lo=d[d.title_repeat<=d.title_repeat.quantile(.25)]
    print('   верхняя четверть по повтору n=%d медиана показов %.0f | нижняя n=%d медиана показов %.0f'%(len(hi),hi.shows.median(),len(lo),lo.shows.median()))

print()
print('=== I. Жалобы читателей на повтор/усталость в комментариях (эпоха дно) ===')
pat = re.compile(r'(в каждой стать|опять|снова про|уже писали|уже был[аои]|повтор|одно и то же|сколько можно|надоел|достал|заезжен|по кругу|каждый раз одно)', re.I)
files=sorted(glob.glob('out/comments/*.json'))
oid2=m.set_index('oid')[['эпоха','date']].to_dict('index')
tot=collections.Counter(); hit=collections.Counter(); ex=[]
for f in files:
    oid=os.path.splitext(os.path.basename(f))[0]; info=oid2.get(oid)
    if not info: continue
    ep=info['эпоха']
    for c in json.load(open(f,encoding='utf-8')).get('comments',[]):
        t=c.get('text') or ''
        tot[ep]+=1
        if pat.search(t):
            hit[ep]+=1
            if len(ex)<12 and len(t)<180: ex.append((info['date'].date(), c.get('likes',0), t.replace('\n',' ')))
for ep in ['2_склон','3_дно']:
    if tot[ep]: print('%s: %d/%d = %.2f%% комментариев с маркером повтора/усталости'%(ep,hit[ep],tot[ep],100*hit[ep]/tot[ep]))
print('примеры:')
for d,l,t in ex: print('  [%s, +%d] %s'%(d,l,t[:170]))

print()
print('=== J. Ядро против охвата: комментаторы и подписчики ===')
bot=m[m['эпоха']=='3_дно']
print('дно: суммарно дочитываний=%d, суммарно комментариев=%d, статей=%d'%(bot.reads.sum(),bot.comments.sum(),len(bot)))
print('медиана дочитываний=%.0f  75-й перцентиль=%.0f  доля дочитываний у топ-10%% статей=%.1f%%'%(
    bot.reads.median(), bot.reads.quantile(.75), 100*bot.reads.nlargest(max(1,len(bot)//10)).sum()/bot.reads.sum()))
pre=m[m['эпоха']=='1_до_спада']
print('до спада: доля дочитываний у топ-10%% статей=%.1f%%'%(100*pre.reads.nlargest(len(pre)//10).sum()/pre.reads.sum()))
