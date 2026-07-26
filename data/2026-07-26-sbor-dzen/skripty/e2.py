# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os, json, glob
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 300); pd.set_option('display.max_rows', 400)
SP = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad'
OUT = os.path.join(SP,'out')

print('=== raw dir ===')
for p in glob.glob(os.path.join(SP,'raw','*')):
    print(os.path.getsize(p), p)
print()
print('=== out/pages sample ===')
pg = glob.glob(os.path.join(OUT,'pages','*'))
print('n pages files', len(pg)); print(pg[:5])
print('=== out/comments ===')
cm = glob.glob(os.path.join(OUT,'comments','*'))
print('n comment files', len(cm)); print(cm[:3])
print('=== out/recon ===')
for p in glob.glob(os.path.join(OUT,'recon','*'))[:20]:
    print(os.path.getsize(p), p)
print()
# texts
for name in ['texts_joined.pkl','body_joined.pkl','articles_joined.pkl','master_raw.pkl']:
    try:
        d = pd.read_pickle(os.path.join(OUT,name))
        print('---', name, d.shape)
        print(list(d.columns)[:80])
    except Exception as e:
        print('---', name, 'ERR', e)
