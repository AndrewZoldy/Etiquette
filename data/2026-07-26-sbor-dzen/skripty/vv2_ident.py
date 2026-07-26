# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
df = pd.read_pickle('out/full.pkl')
tf = pd.read_pickle('out/text_feats.pkl')
print("full oid dup:", df.oid.duplicated().sum(), " tf oid dup:", tf.oid.duplicated().sum())
d = df.merge(tf, on='oid', how='left', suffixes=('','_tf'))
print("merged", d.shape)
d.to_pickle('vv_merged.pkl')

m = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
print("=== Светская жизнь matches:", m.sum())
print(d.loc[m, ['date','title_studio','shows','opens','reads','read_rate','ctr','n_words','слов','comments','comments_enabled','эпоха']].sort_values('date').to_string())

print()
print("=== эпоха counts ===")
print(d['эпоха'].value_counts())
print()
print("=== comments_enabled ===")
print(d['comments_enabled'].value_counts(dropna=False))
ce = d[d.comments_enabled==False]
print("CE=False n=", len(ce))
print(ce[['date','title_studio','n_words','read_rate','эпоха']].sort_values('date').head(40).to_string())

v = pd.read_pickle('out/vestnik.pkl')
print()
print("=== vestnik.pkl titles ===")
print(v[['date','title_studio','n_words','reads','read_rate']].sort_values('date').to_string())
