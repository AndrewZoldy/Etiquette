# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 200)
df = pd.read_pickle('out/full.pkl')
print("SHAPE", df.shape)
print("--- COLUMNS ---")
for i, c in enumerate(df.columns):
    nn = df[c].notna().sum()
    print(f"{i:3d} {c:38s} {str(df[c].dtype):12s} nonnull={nn:4d} sample={repr(df[c].dropna().iloc[0])[:70] if nn else 'NA'}")
