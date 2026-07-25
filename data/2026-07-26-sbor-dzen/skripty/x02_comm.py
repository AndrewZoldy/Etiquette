# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
c = pd.read_pickle('out/comments_all.pkl')
print("comments_all shape", c.shape)
print(c.dtypes)
print(c.head(3).to_string()[:2000])
print()
cp = pd.read_pickle('out/comm_per_article.pkl')
print("comm_per_article shape", cp.shape); print(cp.dtypes); print(cp.head(3).to_string()[:1500])
print()
m = pd.read_pickle('out/full.pkl')
# ce=False composition
f = m[m['comments_enabled']==False]
print("ce=False n=", len(f))
print(f.groupby(f['ym'].astype(str)).size().to_string())
print("сцена:", f['сцена'].value_counts().to_dict())
print("серийная_рубрика:", f['серийная_рубрика'].value_counts().to_dict())
print("медиана shows ce=False:", f['shows'].median(), " ce=True:", m[m['comments_enabled']==True]['shows'].median())
print("примеры заголовков ce=False (2026):")
print(f[f['date']>='2026-01-01']['title_studio'].head(25).to_string())
