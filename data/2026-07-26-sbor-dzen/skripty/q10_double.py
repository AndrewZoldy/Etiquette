# -*- coding: utf-8 -*-
"""Двойная чистка: ce=True минус рубрика «Светская жизнь Петербурга». Устойчивость всех выводов."""
import pandas as pd, numpy as np, os
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['ymS'] = m['ym'].astype(str)
m['halfX'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['свет'] = m['title_studio'].str.contains('Светская жизнь Петербурга', na=False)
rng = np.random.default_rng(555)

print("=" * 120)
print("U1. Рубрика «Светская жизнь Петербурга» внутри ce=True: воронка")
print("=" * 120)
z = m[m['свет']]
print(z[['date', 'shows', 'opens', 'reads', 'ctr', 'read_rate']].sort_values('date').to_string(index=False, float_format=lambda v: f'{v:,.4f}'))
print(f"\n   n={len(z)}, медианы: shows {z['shows'].median():,.0f}, opens {z['opens'].median():,.0f}, reads {z['reads'].median():,.0f}, "
      f"ctr {z['ctr'].median():.4f}, read_rate {z['read_rate'].median():.4f}")
print("   -> раздача есть (десятки-сотни тыс. показов), обрушен КЛИК: ctr ~0,2-0,4% против ~6-8% у канала.")
print(f"   Досье утверждает «показы 291–661» — не подтверждается: минимум показов {z['shows'].min():,.0f}.")

ct = m[m['ce'] == True]
dc = m[(m['ce'] == True) & (~m['свет'])]
print("\n" + "=" * 120)
print("U2. Месячные медианы: ce=True против ce=True-минус-«Светская жизнь» (двойная чистка)")
print("=" * 120)
months = [x for x in sorted(m['ymS'].unique()) if x >= '2025-05']
rows = []
for k in months:
    a = ct[ct['ymS'] == k]; b = dc[dc['ymS'] == k]
    rows.append({'месяц': k, 'n_ce': len(a), 'reads_ce': a['reads'].median(), 'shows_ce': a['shows'].median(),
                 'n_2x': len(b), 'reads_2x': b['reads'].median(), 'shows_2x': b['shows'].median(),
                 'убрано': len(a) - len(b)})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.0f}'))

print("\n" + "=" * 120)
print("U3. Устойчивость ключевых чисел на двойной чистке")
print("=" * 120)


def br(a, b, n=20000):
    a = np.asarray(pd.Series(a).dropna(), float); b = np.asarray(pd.Series(b).dropna(), float)
    ra = np.median(rng.choice(a, size=(n, len(a)), replace=True), axis=1)
    rb = np.median(rng.choice(b, size=(n, len(b)), replace=True), axis=1)
    q = ra / np.where(rb == 0, np.nan, rb)
    return np.nanpercentile(q, 2.5), np.nanpercentile(q, 97.5)


print("\n  (1) Амплитуда ступени: пик (май-сен25) / дно с цензом (ноя25-мар26)")
for nm, s in [('ce=True', ct), ('двойная чистка', dc)]:
    pk = s[(s['ymS'] >= '2025-05') & (s['ymS'] <= '2025-09')]
    dn = s[(s['ymS'] >= '2025-11') & (s['ymS'] <= '2026-03')]
    for col in ['shows', 'reads']:
        lo, hi = br(pk[col], dn[col])
        print(f"     {nm:16s} {col:6s} {pk[col].median():>10,.0f} / {dn[col].median():>9,.0f} = {pk[col].median()/dn[col].median():>5,.2f}x  CI [{lo:.2f}; {hi:.2f}]  n={len(pk)}/{len(dn)}")

print("\n  (2) Требование 3: базы против 2026H1 (двойная чистка, БЕЗ ценза и С цензом)")
for tn, tg in [('2026H1 без ценза', dc[(dc['ymS'] >= '2026-01') & (dc['ymS'] <= '2026-06')]),
               ('2026H1 ценз янв-мар', dc[(dc['ymS'] >= '2026-01') & (dc['ymS'] <= '2026-03')])]:
    print(f"\n    цель: {tn} (n={len(tg)})")
    for bn in ['2023H2', '2024H1', '2024H2', '2025H1']:
        bg = dc[dc['halfX'] == bn]
        out = []
        for col in ['shows', 'opens', 'reads']:
            lo, hi = br(bg[col], tg[col])
            out.append(f"{col} {bg[col].median()/tg[col].median():.2f} [{lo:.2f};{hi:.2f}]{'*' if not (lo<=1<=hi) else ''}")
        print(f"      {bn} (n={len(bg)}): " + " | ".join(out))
print("\n      * = CI не содержит 1")

print("\n  (3) Продолжающееся убывание после ноя25 на двойной чистке")
from scipy import stats as st
post = dc[dc['ymS'] >= '2025-11'].copy()
post['mi'] = post['ymS'].map({k: i for i, k in enumerate(sorted(post['ymS'].unique()))})
for lbl, sub in [('всё дно', post), ('ценз ноя25-мар26', post[post['ymS'] <= '2026-03'])]:
    for col in ['reads', 'shows']:
        r = st.spearmanr(sub['mi'], sub[col])
        print(f"      {lbl:20s} {col:6s} n={len(sub):3d} Спирмен {r.statistic:+.3f} p={r.pvalue:.3f}")

print("\n  (4) Требование 4: индекс стол_еда на дне, двойная чистка")
e1 = dc[dc['эпоха'] == '1_до_спада']; e3 = dc[dc['эпоха'] == '3_дно']
for nm, g, ref in [('до спада', e1, e1), ('дно', e3, e3)]:
    s = g[g['сцена'] == 'стол_еда']
    print(f"      {nm}: n={len(s)} медиана reads {s['reads'].median():,.0f}, эпоха {ref['reads'].median():,.0f}, индекс {s['reads'].median()/ref['reads'].median():.2f}")
print(f"      история_высший_свет на дне после чистки: n={len(e3[e3['сцена']=='история_высший_свет'])}, "
      f"индекс {e3[e3['сцена']=='история_высший_свет']['reads'].median()/e3['reads'].median():.2f} "
      f"(до чистки было 0.11)")

print("\n  (5) Требование 1: лестница cpr на двойной чистке")
d = dc[dc['эпоха'] == '3_дно']
sat = dc[(dc['эпоха'] == '1_до_спада') & (dc['age_days'] > 550)]
cs = sat['comments_per_read'].median()
for a, b in [(0, 45), (45, 75), (75, 110), (110, 150), (150, 200), (200, 270)]:
    g = d[(d['age_days'] >= a) & (d['age_days'] < b)]
    print(f"      {a}-{b}: n={len(g):2d} cpr={g['comments_per_read'].median():.4f} множитель={g['comments_per_read'].median()/cs:.2f}")
print(f"      эталон cpr (age>550, двойная чистка, n={len(sat)}) = {cs:.6f}")
