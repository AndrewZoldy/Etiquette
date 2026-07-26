# -*- coding: utf-8 -*-
"""Скачать страницы 10 выпусков рубрики и сохранить сырые draftJsState-блоки с inlineStyleRanges."""
import json, os, re, sys, time, random
import pandas as pd
sys.path.insert(0, r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad')
from dzenlib import Dzen

OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
RAWD = os.path.join(OUT, 'vraw'); os.makedirs(RAWD, exist_ok=True)
DEC = json.JSONDecoder()

ves = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
v10 = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date')
d = Dzen()
for i, r in enumerate(v10.itertuples()):
    dst = os.path.join(RAWD, r.oid + '.json')
    if os.path.exists(dst):
        print('skip', r.oid); continue
    try:
        html = d.get(r.share_link, timeout=60)
    except Exception as e:
        print('FAIL', r.oid, type(e).__name__, e); continue
    draft = None
    k = html.find('"contentState":')
    if k >= 0:
        try:
            s, _ = DEC.raw_decode(html, html.index('"', k + len('"contentState":')))
            draft = json.loads(s)
        except Exception as e:
            print('parse fail', e)
    if draft is None:
        print('NO DRAFT', r.oid); continue
    json.dump({'oid': r.oid, 'title': r.title_studio, 'draft': draft}, open(dst,'w',encoding='utf-8'), ensure_ascii=False)
    blocks = (draft.get('draftJsState') or {}).get('blocks') or []
    nst = sum(len(b.get('inlineStyleRanges') or []) for b in blocks)
    print('OK', r.oid, r.title_studio, 'blocks', len(blocks), 'styleranges', nst)
    time.sleep(0.4 + random.random()*0.4)
print('done, files:', len(os.listdir(RAWD)))
