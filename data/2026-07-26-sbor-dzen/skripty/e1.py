# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 200); pd.set_option('display.max_rows', 400)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
full = pd.read_pickle(os.path.join(OUT,'full.pkl'))
ves  = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))

print('=== vestnik rows ===')
print(ves[['date','title_studio','shows','opens','reads','ctr','read_rate','n_words','слов','comments','n_paragraphs','n_images','подзаголовков','min_per_read','серийная_рубрика']].sort_values('date').to_string())
print()
print('=== эпоха value counts (full) ===')
print(full['эпоха'].value_counts(dropna=False))
print()
print('=== full date range ===', full['date'].min(), full['date'].max())
print('=== src ==='); print(full['src'].value_counts(dropna=False))
print('=== item_type/type ===')
print(full['item_type'].value_counts(dropna=False)); print(full['type'].value_counts(dropna=False))
print()
print('=== by epoch: n, median shows/ctr/read_rate/reads/words ===')
g = full.groupby('эпоха').agg(n=('oid','size'), shows=('shows','median'), ctr=('ctr','median'),
                              rr=('read_rate','median'), reads=('reads','median'), w=('n_words','median'),
                              dmin=('date','min'), dmax=('date','max'))
print(g.to_string())
print()
print('=== monthly ===')
m = full.groupby(full['date'].dt.to_period('M')).agg(n=('oid','size'), shows=('shows','median'),
      ctr=('ctr','median'), rr=('read_rate','median'), reads=('reads','median'), w=('n_words','median'))
print(m.to_string())
print()
print('=== full: rows with date >= 2026-05-18 ===')
sel = full[full['date']>=pd.Timestamp('2026-05-18')]
print('n =', len(sel))
print(sel[['date','title_studio','shows','opens','reads','ctr','read_rate','n_words']].sort_values('date').to_string())
