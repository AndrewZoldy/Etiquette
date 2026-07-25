# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np
m = pd.read_pickle('out/full.pkl')
print('COLUMNS:', list(m.columns))
print()
SUBS = 88465
g = m.groupby('epoha' if 'epoha' in m.columns else m.columns[m.columns.str.contains('эпох')][0])
key = [c for c in m.columns if 'эпох' in c][0]
print('epoch key:', key)
for name, d in m.groupby(key):
    print('---', name, 'n=', len(d))
    for c in ['shows','opens','reads','subs','ctr','read_rate','subs_per_read','likes_per_read','comments_per_read','min_per_read']:
        if c in d.columns:
            print('   %-18s median=%.6g  mean=%.6g' % (c, d[c].median(), d[c].mean()))
    print('   shows_median / subscribers = %.3f' % (d['shows'].median()/SUBS))
    print('   reads_median / subscribers = %.4f' % (d['reads'].median()/SUBS))
