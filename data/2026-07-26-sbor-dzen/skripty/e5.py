# -*- coding: utf-8 -*-
import json, os, pandas as pd
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
ves = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
v10 = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date')
print('n issues', len(v10))
oid = v10.iloc[-1]['oid']
print('oid', oid)
p = os.path.join(OUT,'pages', oid + '.json')
print('exists', os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0)
d = json.load(open(p, encoding='utf-8'))
def walk(o, pre='', depth=0):
    if depth > 3: return
    if isinstance(o, dict):
        for k, v in list(o.items())[:40]:
            t = type(v).__name__
            extra = ''
            if isinstance(v,(str,)): extra = ' len=%d' % len(v)
            if isinstance(v,(list,)): extra = ' n=%d' % len(v)
            print(' '*depth*2, pre+k, t, extra)
            walk(v, pre='', depth=depth+1)
    elif isinstance(o, list) and o:
        walk(o[0], pre='[0].', depth=depth+1)
walk(d)
