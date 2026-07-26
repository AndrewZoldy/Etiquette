# -*- coding: utf-8 -*-
import json, os, pandas as pd
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
ves = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
v10 = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date')
for k in [0, 9]:
    r = v10.iloc[k]
    d = json.load(open(os.path.join(OUT,'pages', r['oid']+'.json'), encoding='utf-8'))
    print('='*110)
    print('ВЫПУСК', r['title_studio'], '| дата', r['date'], '| n_words', r['n_words'])
    print('images pos:', [im['pos'] for im in d['images']])
    print('sequence kinds:', [s['k'] for s in d['sequence']])
    print('links:', d['links'])
    for i, p in enumerate(d['paragraphs']):
        print('  [%02d] (%d сл.) %s' % (i, len(p.split()), p[:400]))
