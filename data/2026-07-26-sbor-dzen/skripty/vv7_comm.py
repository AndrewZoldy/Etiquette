# -*- coding: utf-8 -*-
import pandas as pd, json, os, sys
d = pd.read_pickle('vv_merged.pkl')
d['is_rub'] = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
rub = d[d.is_rub].sort_values('date')
p='out/comments'
avail=set(os.listdir(p))
print("файлов комментариев всего:", len(avail))
for oid,t in zip(rub.oid, rub.title_studio):
    print(oid, f"{oid}.json" in avail, t)
# structure of one
oid=rub.oid.iloc[0]
j=json.load(open(f'{p}/{oid}.json',encoding='utf-8'))
print("\nTYPE:",type(j))
if isinstance(j,dict): print("KEYS:",list(j.keys())[:30])
print(json.dumps(j, ensure_ascii=False)[:3000])
