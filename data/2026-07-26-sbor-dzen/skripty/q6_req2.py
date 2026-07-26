# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 2: локализация события во времени по двум независимым шкалам."""
import pandas as pd, numpy as np, os
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['ymS'] = m['ym'].astype(str)
rng = np.random.default_rng(101)


def bm(x, n=10000):
    x = np.asarray(pd.Series(x).dropna(), float)
    if len(x) < 3:
        return (np.nan, np.nan)
    s = np.median(rng.choice(x, size=(n, len(x)), replace=True), axis=1)
    return (np.percentile(s, 2.5), np.percentile(s, 97.5))


months = [f'{y}-{mo:02d}' for y in (2025, 2026) for mo in range(1, 13)]
months = [x for x in months if '2025-05' <= x <= '2026-07']

print("=" * 130)
print("ТРЕБОВАНИЕ 2(а). МЕСЯЧНЫЕ МЕДИАНЫ shows и reads, ТОЛЬКО ce=True, бутстрап-CI 95%")
print("=" * 130)
ct = m[m['ce'] == True]
rows = []
for k in months:
    g = ct[ct['ymS'] == k]
    slo, shi = bm(g['shows']); rlo, rhi = bm(g['reads'])
    rows.append({'месяц': k, 'n_ce': len(g), 'n_всего': (m['ymS'] == k).sum(),
                 'shows_мед': g['shows'].median(), 'shows_lo': slo, 'shows_hi': shi,
                 'reads_мед': g['reads'].median(), 'reads_lo': rlo, 'reads_hi': rhi,
                 'age_мед': g['age_days'].median()})
A = pd.DataFrame(rows)
print(A.to_string(index=False, float_format=lambda v: f'{v:,.0f}'))

print("\n--- Сверка с цифрами критика (reads, ce=True) ---")
crit = {'2025-08': 16837, '2025-09': 14269, '2025-10': 4119, '2025-11': 5055, '2025-12': 2874,
        '2026-01': 5313, '2026-02': 5982, '2026-03': 4764, '2026-04': 3222}
for k, v in crit.items():
    mine = A.loc[A['месяц'] == k, 'reads_мед'].iloc[0]
    print(f"   {k}: критик {v:>7,}  мой {mine:>10,.0f}  {'СОВПАЛО' if abs(mine - v) <= 1 else 'РАСХОЖДЕНИЕ'}")

print("\n" + "=" * 130)
print("ТРЕБОВАНИЕ 2(б). МЕСЯЧНЫЕ СУММЫ ДОЧИТЫВАНИЙ по ВСЕМ статьям месяца публикации")
print("=" * 130)
rows = []
for k in months:
    g = m[m['ymS'] == k]
    gc = ct[ct['ymS'] == k]
    rows.append({'месяц': k, 'n_статей': len(g), 'сумма_reads_млн': g['reads'].sum() / 1e6,
                 'сумма_shows_млн': g['shows'].sum() / 1e6,
                 'n_ce': len(gc), 'сумма_reads_ce_млн': gc['reads'].sum() / 1e6,
                 'сумма_shows_ce_млн': gc['shows'].sum() / 1e6})
Bt = pd.DataFrame(rows)
print(Bt.to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
print("\n--- Сверка с цифрами критика (суммы reads, млн) ---")
for k, v in {'2025-08': 1.696, '2025-12': 0.295, '2026-02': 0.323, '2026-04': 0.314, '2026-06': 0.340}.items():
    mine = Bt.loc[Bt['месяц'] == k, 'сумма_reads_млн'].iloc[0]
    print(f"   {k}: критик {v:.3f}  мой {mine:.3f}")

print("\n" + "=" * 130)
print("K. ГДЕ СТУПЕНЬ? Отношение медианы reads (ce=True) «3 месяца до» / «3 месяца после» для каждого стыка")
print("=" * 130)
rows = []
allm = sorted(m['ymS'].unique())
allm = [x for x in allm if x >= '2025-01']
for i in range(2, len(allm) - 2):
    cut = allm[i]
    pre = ct[ct['ymS'].isin(allm[i - 3:i])] if i >= 3 else ct[ct['ymS'].isin(allm[:i])]
    post = ct[ct['ymS'].isin(allm[i:i + 3])]
    if len(pre) < 10 or len(post) < 10:
        continue
    lo, hi = None, None
    a = np.asarray(pre['reads'], float); b = np.asarray(post['reads'], float)
    ra = np.median(rng.choice(a, size=(6000, len(a)), replace=True), axis=1)
    rb = np.median(rng.choice(b, size=(6000, len(b)), replace=True), axis=1)
    q = ra / rb
    rows.append({'стык (первый месяц ПОСЛЕ)': cut, 'n_до': len(pre), 'n_после': len(post),
                 'reads_до': np.median(a), 'reads_после': np.median(b), 'отношение': np.median(a) / np.median(b),
                 'CI_lo': np.percentile(q, 2.5), 'CI_hi': np.percentile(q, 97.5),
                 'shows_отн': pre['shows'].median() / post['shows'].median()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print("\n" + "=" * 130)
print("L. ЕСТЬ ЛИ ПРОДОЛЖАЮЩЕЕСЯ УБЫВАНИЕ ПОСЛЕ ноября 2025? (ce=True)")
print("=" * 130)
from scipy import stats as st
post = ct[ct['ymS'] >= '2025-11'].copy()
post['mi'] = post['ymS'].map({k: i for i, k in enumerate(sorted(post['ymS'].unique()))})
for lbl, sub in [('всё дно ноя25-июл26', post),
                 ('ЦЕНЗ ЗРЕЛОСТИ: ноя25-мар26 (age>=110)', post[post['ymS'] <= '2026-03']),
                 ('ЦЕНЗ ЗРЕЛОСТИ строгий: age>=150', post[post['age_days'] >= 150])]:
    for col in ['reads', 'shows']:
        r = st.spearmanr(sub['mi'], sub[col])
        print(f"   {lbl:42s} {col:6s} n={len(sub):3d} Спирмен(месяц,{col}) = {r.statistic:+.3f}  p={r.pvalue:.3f}")
print("\n   Медианы по месяцам с цензом зрелости (ноя25-мар26, ce=True):")
sub = post[post['ymS'] <= '2026-03']
print(sub.groupby('ymS').agg(n=('oid', 'size'), shows=('shows', 'median'), reads=('reads', 'median'),
                             age=('age_days', 'median')).to_string(float_format=lambda v: f'{v:,.0f}'))

print("\n" + "=" * 130)
print("M. АМПЛИТУДА СТУПЕНИ: окно «пик» (май-сен 2025) против окна «дно с цензом» (ноя25-мар26), ce=True")
print("=" * 130)
pk = ct[(ct['ymS'] >= '2025-05') & (ct['ymS'] <= '2025-09')]
dn = ct[(ct['ymS'] >= '2025-11') & (ct['ymS'] <= '2026-03')]
for col in ['shows', 'opens', 'reads']:
    a = np.asarray(pk[col], float); b = np.asarray(dn[col], float)
    ra = np.median(rng.choice(a, size=(10000, len(a)), replace=True), axis=1)
    rb = np.median(rng.choice(b, size=(10000, len(b)), replace=True), axis=1)
    q = ra / rb
    print(f"   {col:6s} пик n={len(a)} мед={np.median(a):>12,.0f} | дно n={len(b)} мед={np.median(b):>10,.0f} | "
          f"отношение {np.median(a)/np.median(b):>6,.2f}  CI95 [{np.percentile(q,2.5):.2f}; {np.percentile(q,97.5):.2f}]")
print("\n   Та же пара БЕЗ ce-фильтра (вся смесь) — для сопоставления с Фактом 1 досье:")
pk2 = m[(m['ymS'] >= '2025-05') & (m['ymS'] <= '2025-09')]
dn2 = m[(m['ymS'] >= '2025-11') & (m['ymS'] <= '2026-03')]
for col in ['shows', 'reads']:
    print(f"   {col:6s} пик n={len(pk2)} мед={pk2[col].median():>12,.0f} | дно n={len(dn2)} мед={dn2[col].median():>10,.0f} | "
          f"отношение {pk2[col].median()/dn2[col].median():>6,.2f}")
print("\n   Полный вариант Факта 1 (янв-июл 2025 против ноя25-июн26):")
for flt, nm in [(m['ce'] == True, 'ce=True'), (m['oid'] == m['oid'], 'вся смесь')]:
    s = m[flt]
    p = s[(s['ymS'] >= '2025-01') & (s['ymS'] <= '2025-07')]
    q_ = s[(s['ymS'] >= '2025-11') & (s['ymS'] <= '2026-06')]
    print(f"   {nm:10s} shows {p['shows'].median():,.0f} -> {q_['shows'].median():,.0f} ({p['shows'].median()/q_['shows'].median():.1f}x)  "
          f"reads {p['reads'].median():,.0f} -> {q_['reads'].median():,.0f} ({p['reads'].median()/q_['reads'].median():.1f}x)  n={len(p)}/{len(q_)}")
A.to_pickle(os.path.join(B, 'q6_A.pkl')); Bt.to_pickle(os.path.join(B, 'q6_B.pkl'))
