# -*- coding: utf-8 -*-
import pandas as pd, json, os, re, io
d = pd.read_pickle('vv_merged.pkl')
d['is_rub'] = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
rub = d[d.is_rub].sort_values('date')
p='out/comments'
rows=[]
buf=io.StringIO()
for i,(oid,t,dt) in enumerate(zip(rub.oid,rub.title_studio,rub.date),1):
    j=json.load(open(f'{p}/{oid}.json',encoding='utf-8'))
    cs=j['comments']
    buf.write(f"\n{'='*110}\nВЫПУСК {i}: {t}  ({dt:%d.%m.%Y})  meta={j['meta']}\n{'='*110}\n")
    for c in cs:
        rows.append({'вып':i,'дата':dt.strftime('%d.%m'),'oid':oid,'level':c['level'],'author':c['author_name'],
                     'by_channel':c['published_by_channel'],'state':c['state'],'likes':c['likes'],
                     'dislikes':c['dislikes'],'text':c['text'] or ''})
        tag = 'АВТОР' if c['published_by_channel'] else c['author_name']
        buf.write(f"[{c['level']:5s}|{c['state']:8s}|+{c['likes']}/-{c['dislikes']}] {tag}: {(c['text'] or '(пусто)')}\n")
C=pd.DataFrame(rows)
C.to_pickle('vv_comments.pkl')
open('vv_comments_dump.txt','w',encoding='utf-8').write(buf.getvalue())
print("всего собрано комментариев:", len(C))
print(C.groupby('вып').agg(n=('text','size'), удалённых=('state',lambda s:(s!='visible').sum()),
     от_автора=('by_channel','sum'), пустых=('text',lambda s:(s.str.strip()=='').sum())).to_string())
print("\nдлина дампа, симв:", len(buf.getvalue()))
