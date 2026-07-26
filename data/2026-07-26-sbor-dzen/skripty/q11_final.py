# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']; m['ymS'] = m['ym'].astype(str)
print("V. «Застрявшие» из Факта 5/9 — целиком ли это серия ce=False?")
for nm, g in [('эпоха 1_до_спада', m[m['эпоха'] == '1_до_спада']), ('эпоха 3_дно', m[m['эпоха'] == '3_дно'])]:
    for flt, lab in [(g['oid'] == g['oid'], 'вся смесь'), (g['ce'] == True, 'ce=True')]:
        s = g[flt]
        print(f"   {nm:18s} {lab:10s} n={len(s):3d}  доля shows<10k={(s['shows']<10000).mean():.3f} ({(s['shows']<10000).sum()} шт)"
              f"  доля<3k={(s['shows']<3000).mean():.3f} ({(s['shows']<3000).sum()} шт)"
              f"  доля>1млн={(s['shows']>1e6).mean():.3f}")
d3 = m[m['эпоха'] == '3_дно']
st = d3[d3['shows'] < 10000]
print(f"\n   Состав «застрявших» (<10k показов) эпохи дно: n={len(st)}, из них ce=False {(st['ce']==False).sum()} ({(st['ce']==False).mean():.1%})")
print("   по сценам:", st['сцена'].value_counts().to_dict())
print("   ce=True среди застрявших:")
print(st[st['ce'] == True][['date', 'title_studio', 'shows', 'reads', 'сцена']].to_string(index=False, float_format=lambda v: f'{v:,.0f}'))
print("\nW. Факт 5: связь CTR-показы (Спирмен) на ce=True против всей смеси")
from scipy import stats as st2
for nm, g in [('1_до_спада', m[m['эпоха'] == '1_до_спада']), ('3_дно', m[m['эпоха'] == '3_дно'])]:
    for flt, lab in [(g['oid'] == g['oid'], 'вся смесь'), (g['ce'] == True, 'ce=True')]:
        s = g[flt].dropna(subset=['ctr'])
        r = st2.spearmanr(s['ctr'], s['shows'])
        print(f"   {nm:12s} {lab:10s} n={len(s):3d}  Спирмен(ctr,shows)={r.statistic:+.3f} p={r.pvalue:.4f}")
print("\nX. Квинтили CTR (Факт 5) на ce=True")
for nm, g in [('1_до_спада', m[(m['эпоха'] == '1_до_спада') & (m['ce'] == True)]),
              ('3_дно', m[(m['эпоха'] == '3_дно') & (m['ce'] == True)])]:
    g = g.dropna(subset=['ctr']).copy()
    g['q'] = pd.qcut(g['ctr'], 5, labels=[1, 2, 3, 4, 5])
    t = g.groupby('q', observed=True).agg(n=('oid', 'size'), ctr=('ctr', 'median'), shows=('shows', 'median'))
    print(f"   --- {nm} (ce=True) ---")
    print(t.to_string(float_format=lambda v: f'{v:,.4f}'))
    print(f"   отношение показов Q5/Q1 = {t['shows'].iloc[-1]/t['shows'].iloc[0]:.2f}x")
