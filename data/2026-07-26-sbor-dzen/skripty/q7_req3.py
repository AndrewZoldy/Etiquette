# -*- coding: utf-8 -*-
"""Устойчивость шкалы сумм (треб.2) + ТРЕБОВАНИЕ 3: тест на аномальность базы сравнения."""
import pandas as pd, numpy as np, os
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['ymS'] = m['ym'].astype(str)
m['halfX'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
rng = np.random.default_rng(777)

print("=" * 130)
print("N. УСТОЙЧИВОСТЬ ШКАЛЫ СУММ (требование 2б): суммы — статистика средневого типа, ломается выбросом")
print("=" * 130)
months = [x for x in sorted(m['ymS'].unique()) if x >= '2025-05']
rows = []
for k in months:
    g = m[m['ymS'] == k].sort_values('reads', ascending=False)
    s = g['reads'].sum()
    rows.append({'месяц': k, 'n': len(g), 'сумма_млн': s / 1e6,
                 'доля_топ1': g['reads'].iloc[0] / s if s else np.nan,
                 'доля_топ2': g['reads'].iloc[:2].sum() / s if s else np.nan,
                 'сумма_без_топ1_млн': (s - g['reads'].iloc[0]) / 1e6,
                 'сумма_без_топ2_млн': (s - g['reads'].iloc[:2].sum()) / 1e6,
                 'медиана': g['reads'].median()})
N = pd.DataFrame(rows)
print(N.to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
print("\n   Вывод по устойчивости: сравните колонки 'сумма_млн' и 'сумма_без_топ2_млн'.")

print("\n" + "=" * 130)
print("ТРЕБОВАНИЕ 3. 2026H1 (ce=True, ценз зрелости) против трёх доспадовых окон")
print("=" * 130)


def boot_ratio_med(a, b, n=20000):
    a = np.asarray(pd.Series(a).dropna(), float); b = np.asarray(pd.Series(b).dropna(), float)
    ra = np.median(rng.choice(a, size=(n, len(a)), replace=True), axis=1)
    rb = np.median(rng.choice(b, size=(n, len(b)), replace=True), axis=1)
    q = ra / np.where(rb == 0, np.nan, rb)
    return np.nanpercentile(q, 2.5), np.nanpercentile(q, 97.5)


def boot_ratio_share(a, b, thr=320000, n=20000):
    a = np.asarray(pd.Series(a).dropna(), float); b = np.asarray(pd.Series(b).dropna(), float)
    ra = (rng.choice(a, size=(n, len(a)), replace=True) > thr).mean(axis=1)
    rb = (rng.choice(b, size=(n, len(b)), replace=True) > thr).mean(axis=1)
    q = ra / np.where(rb == 0, np.nan, rb)
    return np.nanpercentile(q, 2.5), np.nanpercentile(q, 97.5)


ct = m[m['ce'] == True]
targets = {
    '2026H1 ce=True БЕЗ ценза (янв-июн 26)': ct[(ct['ymS'] >= '2026-01') & (ct['ymS'] <= '2026-06')],
    '2026H1 ce=True ЦЕНЗ (янв-мар 26)': ct[(ct['ymS'] >= '2026-01') & (ct['ymS'] <= '2026-03')],
    'ДНО ce=True ЦЕНЗ (ноя25-мар26)': ct[(ct['ymS'] >= '2025-11') & (ct['ymS'] <= '2026-03')],
}
bases = {'2023H2': ct[ct['halfX'] == '2023H2'], '2024H1': ct[ct['halfX'] == '2024H1'],
         '2024H2': ct[ct['halfX'] == '2024H2'], '2025H1 (пик)': ct[ct['halfX'] == '2025H1']}

print("\n--- Уровни (медианы; для shows>320k — доля) ---")
rows = []
for nm, g in list(bases.items()) + list(targets.items()):
    rows.append({'окно': nm, 'n': len(g), 'age_мед': g['age_days'].median(),
                 'shows': g['shows'].median(), 'opens': g['opens'].median(), 'reads': g['reads'].median(),
                 'ctr': g['ctr'].median(), 'read_rate': g['read_rate'].median(),
                 'доля_shows>320k': (g['shows'] > 320000).mean(),
                 'reads_mean': g['reads'].mean(), 'скос_mean/med': g['reads'].mean() / g['reads'].median()})
lv = pd.DataFrame(rows)
print(lv.to_string(index=False, float_format=lambda v: f'{v:,.4f}'))

for tn, tg in targets.items():
    print("\n" + "-" * 126)
    print(f"ОТНОШЕНИЯ  <база> / <{tn}>   (>1 = у базы было больше)")
    print("-" * 126)
    rows = []
    for bn, bg in bases.items():
        r = {'база': bn, 'n_база': len(bg), 'n_цель': len(tg)}
        for col in ['shows', 'opens', 'reads', 'ctr', 'read_rate']:
            rat = bg[col].median() / tg[col].median()
            lo, hi = boot_ratio_med(bg[col], tg[col])
            r[col] = rat; r[col + '_CI'] = f"[{lo:.2f}; {hi:.2f}]"
            r[col + '_1в_CI'] = 'ДА' if (lo <= 1 <= hi) else '-'
        sa = (bg['shows'] > 320000).mean(); sb = (tg['shows'] > 320000).mean()
        lo, hi = boot_ratio_share(bg['shows'], tg['shows'])
        r['доля320k'] = sa / sb if sb else np.inf
        r['доля320k_CI'] = f"[{lo:.2f}; {hi:.2f}]"
        r['доля320k_1в_CI'] = 'ДА' if (lo <= 1 <= hi) else '-'
        rows.append(r)
    R = pd.DataFrame(rows)
    print(R[['база', 'n_база', 'n_цель', 'shows', 'shows_CI', 'shows_1в_CI', 'opens', 'opens_CI', 'opens_1в_CI',
             'reads', 'reads_CI', 'reads_1в_CI']].to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
    print()
    print(R[['база', 'ctr', 'ctr_CI', 'ctr_1в_CI', 'read_rate', 'read_rate_CI', 'read_rate_1в_CI',
             'доля320k', 'доля320k_CI', 'доля320k_1в_CI']].to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print("\n" + "=" * 130)
print("O. Сверка с цифрами критика (2024H1 против 2026H1 ce=True): shows 78 616 -> 87 276, opens 2 275 -> 5 449, reads 1 336 -> 2 366")
print("=" * 130)
b24 = ct[ct['halfX'] == '2024H1']
for nm, g in [('2026H1 ce=True янв-июн', targets['2026H1 ce=True БЕЗ ценза (янв-июн 26)']),
              ('2026H1 ce=True календ. halfX', ct[ct['halfX'] == '2026H1'])]:
    print(f"   2024H1 ce=True (n={len(b24)}): shows {b24['shows'].median():,.0f} opens {b24['opens'].median():,.0f} reads {b24['reads'].median():,.0f}")
    print(f"   {nm} (n={len(g)}): shows {g['shows'].median():,.0f} opens {g['opens'].median():,.0f} reads {g['reads'].median():,.0f}")
    print(f"      скос mean/median reads: 2024H1 {b24['reads'].mean()/b24['reads'].median():.2f}  цель {g['reads'].mean()/g['reads'].median():.2f}")

print("\n" + "=" * 130)
print("P. ФОРМА РАСПРЕДЕЛЕНИЯ: перцентили shows по окнам, ce=True (проверка «обрушился пол»)")
print("=" * 130)
rows = []
for nm, g in list(bases.items()) + list(targets.items()):
    q = g['shows'].quantile([.1, .25, .5, .75, .9]).values
    rows.append({'окно': nm, 'n': len(g), 'p10': q[0], 'p25': q[1], 'p50': q[2], 'p75': q[3], 'p90': q[4],
                 'max': g['shows'].max(), 'p90/p10': q[4] / q[0] if q[0] else np.nan,
                 'доля<10k': (g['shows'] < 10000).mean(), 'доля<3k': (g['shows'] < 3000).mean()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
