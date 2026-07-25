# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 100)
m = pd.read_pickle('out/full.pkl')
print("SHAPE", m.shape)
print("COLS", list(m.columns))
print()
print(m.dtypes.to_string())
print()
print("--- head ---")
print(m.head(3).T.to_string())
