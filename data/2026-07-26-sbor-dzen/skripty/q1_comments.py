# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
B = os.path.dirname(os.path.abspath(__file__))
c = pd.read_pickle(os.path.join(B, 'out', 'comments_all.pkl'))
print("comments_all shape", c.shape)
print("cols:", list(c.columns))
print(c.head(3).T.to_string()[:3000])
print("\n--- dtypes ---")
print(c.dtypes.to_string())
# look for a time field
for col in c.columns:
    if c[col].dtype == 'O':
        continue
print("\n--- comm_per_article ---")
a = pd.read_pickle(os.path.join(B, 'out', 'comm_per_article.pkl'))
print(a.shape, list(a.columns))
print(a.head(3).to_string())
# sample raw json
cd = os.path.join(B, 'out', 'comments')
fs = sorted(os.listdir(cd))[:3]
print("\n--- raw comment json keys ---", len(os.listdir(cd)), "files")
for f in fs:
    j = json.load(open(os.path.join(cd, f), encoding='utf-8'))
    print(f, type(j), (list(j.keys()) if isinstance(j, dict) else len(j)))
    if isinstance(j, dict):
        for k, v in j.items():
            print("  ", k, type(v), (list(v[0].keys()) if isinstance(v, list) and v and isinstance(v[0], dict) else str(v)[:200]))
    elif isinstance(j, list) and j:
        print("  first item:", json.dumps(j[0], ensure_ascii=False)[:800])
    break
