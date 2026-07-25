# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 100)
m = pd.read_pickle('out/full.pkl')
print("SHAPE", m.shape)
print("COLUMNS:")
for i,c in enumerate(m.columns):
    print(f"  {i:3d} {c!r:35s} {str(m[c].dtype):12s} nn={m[c].notna().sum():4d}")
print()
print("--- dtypes/head of key cols ---")
for c in ['date','ym','эпоха','half','shows','opens','reads','ctr','read_rate','сцена','серийная_рубрика','функция']:
    if c in m.columns:
        print(c, '|', m[c].head(3).tolist())
print()
print("--- эпоха counts ---"); print(m['эпоха'].value_counts())
print("--- half counts ---"); print(m['half'].value_counts().sort_index())
print("--- сцена counts ---"); print(m['сцена'].value_counts())
print("--- серийная_рубрика counts ---")
if 'серийная_рубрика' in m.columns:
    print(m['серийная_рубрика'].value_counts(dropna=False))
print("--- функция counts ---"); print(m['функция'].value_counts())
