# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 300)

for f in ['out/text_feats.pkl','out/vestnik.pkl','out/texts_joined.pkl','out/lang_joined.pkl']:
    try:
        d = pd.read_pickle(f)
    except Exception as e:
        print(f, "ERR", e); continue
    print("="*90); print(f, type(d), getattr(d,'shape',None))
    if isinstance(d, pd.DataFrame):
        for c in d.columns:
            nn = d[c].notna().sum()
            print(f"   {c:38s} {str(d[c].dtype):12s} nn={nn:4d} ex={repr(d[c].dropna().iloc[0])[:60] if nn else ''}")
print("="*90)
print("comments dir files:", len(os.listdir('out/comments')))
print(os.listdir('out/comments')[:5])
