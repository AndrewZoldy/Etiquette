# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os, json, sys
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 200)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'

full = pd.read_pickle(os.path.join(OUT,'full.pkl'))
ves  = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
tf   = pd.read_pickle(os.path.join(OUT,'text_feats.pkl'))

print('=== full.pkl shape', full.shape)
for i,c in enumerate(full.columns):
    print(i, repr(c), full[c].dtype, '| nonnull', full[c].notna().sum())
print()
print('=== vestnik.pkl shape', ves.shape)
for i,c in enumerate(ves.columns):
    print(i, repr(c), ves[c].dtype, '| nonnull', ves[c].notna().sum())
print()
print('=== text_feats shape', tf.shape)
for i,c in enumerate(tf.columns):
    print(i, repr(c), tf[c].dtype, '| nonnull', tf[c].notna().sum())
