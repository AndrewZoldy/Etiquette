# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 200)
m = pd.read_pickle('out/full.pkl')
print("SHAPE", m.shape)
print("\n=== COLUMNS ===")
for i, c in enumerate(m.columns):
    print(i, c, m[c].dtype, "nonnull=", m[c].notna().sum())
print("\n=== HEAD dates ===")
print(m[['date','ym','эпоха','half']].head(3))
print(m[['date','ym','эпоха','half']].tail(3))
print("\n=== half values ===")
print(m['half'].value_counts(dropna=False).sort_index())
print("\n=== эпоха ===")
print(m['эпоха'].value_counts(dropna=False))
print("\n=== comments_enabled ===")
for c in m.columns:
    if 'comment' in c.lower() or 'enab' in c.lower():
        print(c, m[c].dtype)
        print(m[c].value_counts(dropna=False).head(10))
