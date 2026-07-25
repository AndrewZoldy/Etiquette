# -*- coding: utf-8 -*-
import sys, io, json, os, glob, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
from scipy.stats import spearmanr
m = pd.read_pickle('out/full.pkl').sort_values('date').reset_index(drop=True)

print('=== E. Как строилась база подписчиков (сумма subs по статьям + все типы) ===')
tot = None
try:
    a=pd.read_pickle('out/art.pkl'); r=pd.read_pickle('out/rol.pkl'); p=pd.read_pickle('out/pos.pkl')
    for nm,d in [('art',a),('rol',r),('pos',p)]:
        print(nm, d.shape, 'subs sum=', d['subs'].sum() if 'subs' in d.columns else '?')
    allp = pd.concat([x.assign(_t=n) for n,x in [('art',a),('rol',r),('pos',p)]], ignore_index=True)
    allp['ym'] = allp['date'].dt.to_period('M').astype(str)
    s = allp.groupby('ym')['subs'].sum()
    print('\nПодписки суммарно по месяцам (все форматы), и накопленная доля:')
    cs = s.cumsum()/s.sum()*100
    for k in s.index:
        print('  %s  subs=%7d  накоплено %5.1f%%' % (k, s[k], cs[k]))
    print('ВСЕГО подписок за всё время:', s.sum())
except Exception as e:
    print('ERR', e)

print()
print('=== F. Насыщение: глубина архива сцены vs масштаб обвала сцены ===')
m['half'] = m.date.dt.year.astype(str) + 'H' + np.where(m.date.dt.month<=6,'1','2')
depth_at_bottom = m[m.date < '2025-11-01'].groupby('сцена').size()
res=[]
for sc, d in m.groupby('сцена'):
    a = d[(d.half=='2025H1')]; b = d[d['эпоха']=='3_дно']
    if len(a)>=5 and len(b)>=5:
        res.append((sc, depth_at_bottom.get(sc,0), len(a), len(b), a.shows.median(), b.shows.median(), a.shows.median()/max(b.shows.median(),1)))
res = pd.DataFrame(res, columns=['сцена','архив_до_ноя25','n_2025H1','n_дно','мед_2025H1','мед_дно','кратность_падения'])
res=res.sort_values('архив_до_ноя25', ascending=False)
print(res.to_string(index=False, float_format=lambda x:'%.0f'%x))
if len(res)>=5:
    print('Спирмен глубина_архива x кратность_падения = %.3f (n=%d)' % (spearmanr(res.архив_до_ноя25, res.кратность_падения).statistic, len(res)))

print()
print('=== G. Смена состава читателей: авторы комментариев ===')
files = glob.glob('comments/*.json')
print('файлов комментариев:', len(files))
oid2date = dict(zip(m.oid, m.date))
oid2ep = dict(zip(m.oid, m['эпоха']))
au = collections.defaultdict(set)   # author -> set of epochs
au_cnt = collections.Counter()
per_ep_authors = collections.defaultdict(set)
per_ep_comments = collections.Counter()
bad=0
for f in files:
    oid = os.path.splitext(os.path.basename(f))[0]
    ep = oid2ep.get(oid)
    if ep is None: continue
    try:
        j=json.load(open(f, encoding='utf-8'))
    except Exception:
        bad+=1; continue
    items = j if isinstance(j,list) else j.get('comments', j.get('items', []))
    def walk(node):
        out=[]
        if isinstance(node, dict):
            for k in ('author','user','userName','authorName','publisherId','author_id'):
                if k in node: out.append(node)
            for v in node.values():
                if isinstance(v,(list,dict)): out.extend(walk(v))
        elif isinstance(node,list):
            for v in node: out.extend(walk(v))
        return out
    nodes = walk(items)
    for nd in nodes:
        a = nd.get('author') or nd.get('user') or {}
        if isinstance(a, dict):
            aid = a.get('id') or a.get('publisherId') or a.get('name') or a.get('displayName')
        else:
            aid = a
        if not aid: aid = nd.get('publisherId') or nd.get('authorName') or nd.get('userName')
        if not aid: continue
        aid=str(aid)
        per_ep_authors[ep].add(aid); per_ep_comments[ep]+=1; au_cnt[aid]+=1
print('битых файлов:', bad)
for ep in ['1_до_спада','2_склон','3_дно']:
    print(ep, 'комментов=%d  уникальных авторов=%d' % (per_ep_comments[ep], len(per_ep_authors[ep])))
A=per_ep_authors['1_до_спада']; C=per_ep_authors['3_дно']
if A and C:
    print('пересечение до_спада & дно = %d  (%.1f%% от авторов дна, %.1f%% от авторов до спада)' % (len(A&C), 100*len(A&C)/len(C), 100*len(A&C)/len(A)))
    print('комментов на автора: до спада %.2f, дно %.2f' % (per_ep_comments['1_до_спада']/len(A), per_ep_comments['3_дно']/len(C)))
