# -*- coding: utf-8 -*-
import sys, io, json, os, glob, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
m = pd.read_pickle('out/full.pkl')
oid2 = m.set_index('oid')[['date','эпоха','сцена','shows','reads','comments']].to_dict('index')
files = sorted(glob.glob('out/comments/*.json'))
rows=[]; au=collections.defaultdict(list)
for f in files:
    oid=os.path.splitext(os.path.basename(f))[0]
    info=oid2.get(oid)
    j=json.load(open(f,encoding='utf-8'))
    cs=j.get('comments',[])
    if info is None:
        rows.append((oid,None,None,len(cs))); continue
    rows.append((oid,info['date'],info['эпоха'],len(cs)))
    for c in cs:
        if c.get('author_uid'):
            au[str(c['author_uid'])].append((info['date'], info['эпоха'], oid))
df=pd.DataFrame(rows,columns=['oid','date','эпоха','n_comm'])
print('файлов:', len(df), 'сматчено со статьями:', df['эпоха'].notna().sum())
print(df.groupby('эпоха', dropna=False).agg(файлов=('oid','size'), комментов=('n_comm','sum')).to_string())
print('диапазон дат покрытых статей:', df.date.min(), '—', df.date.max())
print()
print('уникальных авторов комментариев всего:', len(au))
eps=collections.defaultdict(set)
for a,lst in au.items():
    for d,e,o in lst: eps[e].add(a)
for e in ['1_до_спада','2_склон','3_дно']:
    print(e, 'уник. авторов =', len(eps[e]))
A,B,C=eps['1_до_спада'],eps['2_склон'],eps['3_дно']
if A and C:
    print('пересечение до_спада ∩ дно =', len(A&C), '(%.1f%% авторов дна)'%(100*len(A&C)/len(C)))
if B and C:
    print('пересечение склон ∩ дно =', len(B&C), '(%.1f%% авторов дна)'%(100*len(B&C)/len(C)))
# повторные комментаторы внутри дна
cnt3=collections.Counter()
for a,lst in au.items():
    k=sum(1 for d,e,o in lst if e=='3_дно')
    if k: cnt3[a]=k
if cnt3:
    v=np.array(list(cnt3.values()))
    print('дно: комментариев на автора median=%.1f mean=%.2f; доля авторов с >=2 комм = %.1f%%; доля комментов от них = %.1f%%'
          % (np.median(v), v.mean(), 100*(v>=2).mean(), 100*v[v>=2].sum()/v.sum()))
cnt1=collections.Counter()
for a,lst in au.items():
    k=sum(1 for d,e,o in lst if e=='1_до_спада')
    if k: cnt1[a]=k
if cnt1:
    v=np.array(list(cnt1.values()))
    print('до спада: комментариев на автора median=%.1f mean=%.2f; доля авторов с >=2 комм = %.1f%%; доля комментов от них = %.1f%%'
          % (np.median(v), v.mean(), 100*(v>=2).mean(), 100*v[v>=2].sum()/v.sum()))
