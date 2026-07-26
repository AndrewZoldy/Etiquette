# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 4: тематическое обвинение на чистой выборке + стандартизация смеси."""
import pandas as pd, numpy as np, os
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['ymS'] = m['ym'].astype(str)
m['halfX'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
rng = np.random.default_rng(4242)


def bmed(x, n=10000):
    x = np.asarray(pd.Series(x).dropna(), float)
    if len(x) < 3:
        return (np.nan, np.nan)
    s = np.median(rng.choice(x, size=(n, len(x)), replace=True), axis=1)
    return np.percentile(s, 2.5), np.percentile(s, 97.5)


ct = m[m['ce'] == True]
e1 = ct[ct['эпоха'] == '1_до_спада']
e3 = ct[ct['эпоха'] == '3_дно']
print("=" * 130)
print("ТРЕБОВАНИЕ 4(а). ИНДЕКС СЦЕНЫ К МЕДИАНЕ СВОЕЙ ЭПОХИ, ce=True, n>=10 в ячейке")
print(f"   эпоха 1_до_спада ce=True: n={len(e1)}, медиана reads={e1['reads'].median():,.0f}, shows={e1['shows'].median():,.0f}")
print(f"   эпоха 3_дно      ce=True: n={len(e3)}, медиана reads={e3['reads'].median():,.0f}, shows={e3['shows'].median():,.0f}")
print("=" * 130)
r1, s1 = e1['reads'].median(), e1['shows'].median()
r3, s3 = e3['reads'].median(), e3['shows'].median()
rows = []
for sc in sorted(set(ct['сцена'])):
    g1 = e1[e1['сцена'] == sc]; g3 = e3[e3['сцена'] == sc]
    lo1, hi1 = bmed(g1['reads']); lo3, hi3 = bmed(g3['reads'])
    rows.append({'сцена': sc, 'n_до': len(g1), 'n_дно': len(g3),
                 'reads_до': g1['reads'].median(), 'инд_reads_до': g1['reads'].median() / r1,
                 'reads_дно': g3['reads'].median(), 'инд_reads_дно': g3['reads'].median() / r3,
                 'CI_инд_дно': f"[{lo3/r3:.2f}; {hi3/r3:.2f}]" if len(g3) >= 3 else '-',
                 'shows_до': g1['shows'].median(), 'инд_shows_до': g1['shows'].median() / s1,
                 'shows_дно': g3['shows'].median(), 'инд_shows_дно': g3['shows'].median() / s3,
                 'годно': 'ДА' if (len(g1) >= 10 and len(g3) >= 10) else 'n<10'})
T = pd.DataFrame(rows).sort_values('инд_reads_дно', ascending=False)
print(T.to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print("\n--- То же на ЗАГРЯЗНЁННОЙ смеси (все 623, включая ce=False) — для сопоставления с Фактами 8/9/10 ---")
E1 = m[m['эпоха'] == '1_до_спада']; E3 = m[m['эпоха'] == '3_дно']
R1, R3 = E1['reads'].median(), E3['reads'].median()
rows = []
for sc in sorted(set(m['сцена'])):
    g1 = E1[E1['сцена'] == sc]; g3 = E3[E3['сцена'] == sc]
    rows.append({'сцена': sc, 'n_до': len(g1), 'n_дно': len(g3),
                 'инд_reads_до': g1['reads'].median() / R1, 'инд_reads_дно': g3['reads'].median() / R3,
                 'reads_дно': g3['reads'].median(),
                 'из них ce=False': (g3['ce'] == False).sum()})
print(pd.DataFrame(rows).sort_values('инд_reads_дно', ascending=False).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print("\n" + "=" * 130)
print("ТРЕБОВАНИЕ 4(б). ВНУТРИСЦЕНОВАЯ ДИНАМИКА стол_еда ПО ПОЛУГОДИЯМ, ce=True")
print("=" * 130)
rows = []
for h in ['2023H2', '2024H1', '2024H2', '2025H1', '2025H2', '2026H1']:
    g = ct[(ct['halfX'] == h) & (ct['сцена'] == 'стол_еда')]
    ch = ct[ct['halfX'] == h]
    ga = m[(m['halfX'] == h) & (m['сцена'] == 'стол_еда')]
    lo, hi = bmed(g['reads'])
    rows.append({'полугодие': h, 'n_ce': len(g), 'reads_ce': g['reads'].median(), 'CI': f"[{lo:,.0f}; {hi:,.0f}]" if len(g) >= 3 else '-',
                 'shows_ce': g['shows'].median(), 'ctr_ce': g['ctr'].median(),
                 'канал_ce_reads': ch['reads'].median(), 'индекс_к_каналу': g['reads'].median() / ch['reads'].median(),
                 'n_вся_смесь': len(ga), 'reads_вся_смесь': ga['reads'].median(),
                 'ce=False шт': (ga['ce'] == False).sum(),
                 'годно': 'ДА' if len(g) >= 10 else 'n<10'})
S = pd.DataFrame(rows)
print(S.to_string(index=False, float_format=lambda v: f'{v:,.0f}'))
print("\n   Отношения (стол_еда ce=True):")
d = dict(zip(S['полугодие'], S['reads_ce']))
dn = dict(zip(S['полугодие'], S['n_ce']))
for a, b in [('2025H1', '2026H1'), ('2024H1', '2026H1'), ('2024H2', '2026H1')]:
    if dn[a] >= 10 and dn[b] >= 10:
        aa = ct[(ct['halfX'] == a) & (ct['сцена'] == 'стол_еда')]['reads']
        bb = ct[(ct['halfX'] == b) & (ct['сцена'] == 'стол_еда')]['reads']
        A_ = np.median(rng.choice(np.asarray(aa, float), size=(10000, len(aa)), replace=True), axis=1)
        Bv = np.median(rng.choice(np.asarray(bb, float), size=(10000, len(bb)), replace=True), axis=1)
        q = A_ / Bv
        print(f"     {a}/{b}: {d[a]/d[b]:.2f}x  CI95 [{np.percentile(q,2.5):.2f}; {np.percentile(q,97.5):.2f}]  (n={dn[a]}/{dn[b]})")
    else:
        print(f"     {a}/{b}: n={dn[a]}/{dn[b]} — есть ячейка <10, вывод не формулируется")
print("\n   Канал в целом ce=True для сравнения:")
for a, b in [('2025H1', '2026H1'), ('2024H1', '2026H1')]:
    aa = ct[ct['halfX'] == a]['reads']; bb = ct[ct['halfX'] == b]['reads']
    print(f"     {a}/{b}: {aa.median()/bb.median():.2f}x (n={len(aa)}/{len(bb)})")

print("\n" + "=" * 130)
print("Q. СОСТАВ стол_еда 2026H1 и структура серии ce=False")
print("=" * 130)
se = m[(m['halfX'] == '2026H1') & (m['сцена'] == 'стол_еда')]
print(f"   всего {len(se)}; ce=False {(se['ce']==False).sum()} ({(se['ce']==False).mean():.1%}); ce=True {(se['ce']==True).sum()}")
print(f"   медиана reads: ce=False {se[se['ce']==False]['reads'].median():,.0f} | ce=True {se[se['ce']==True]['reads'].median():,.0f}")
print(f"   медиана shows: ce=False {se[se['ce']==False]['shows'].median():,.0f} | ce=True {se[se['ce']==True]['shows'].median():,.0f}")
print(f"   медиана ctr:   ce=False {se[se['ce']==False]['ctr'].median():.4f} | ce=True {se[se['ce']==True]['ctr'].median():.4f}")
print("\n   Серия ce=False целиком (70 статей): состав по сценам и уровень")
f = m[m['ce'] == False]
print(f.groupby('сцена').agg(n=('oid', 'size'), shows=('shows', 'median'), reads=('reads', 'median'),
                             ctr=('ctr', 'median')).to_string(float_format=lambda v: f'{v:,.4f}'))
print(f"\n   Дни недели серии: {f['dow'].value_counts().to_dict()}")
print(f"   Период серии: {f['date'].min().date()} .. {f['date'].max().date()}")
print(f"   Медиана reads серии {f['reads'].median():,.0f} против ce=True в том же окне: ", end='')
w = ct[(ct['date'] >= f['date'].min()) & (ct['date'] <= f['date'].max())]
print(f"{w['reads'].median():,.0f} (n={len(w)}), отношение {w['reads'].median()/max(f['reads'].median(),1):,.1f}x")

print("\n" + "=" * 130)
print("R. СТАНДАРТИЗАЦИЯ СМЕСИ: доли сцен эпохи 1 как веса, применённые к медианам сцен эпохи 3 (и наоборот)")
print("   Разделяет вклад смены смеси и вклад смены самой раздачи. Только сцены с n>=10 в ОБЕИХ эпохах.")
print("=" * 130)
for lbl, A, Bq in [('ce=True (чистая)', e1, e3), ('вся смесь (623)', E1, E3)]:
    ok = [sc for sc in sorted(set(A['сцена']) | set(Bq['сцена']))
          if (A['сцена'] == sc).sum() >= 10 and (Bq['сцена'] == sc).sum() >= 10]
    print(f"\n--- {lbl} --- сцены, годные по n>=10 в обеих эпохах: {ok}")
    w1 = A['сцена'].value_counts(normalize=True).reindex(ok).fillna(0); w1 = w1 / w1.sum()
    w3 = Bq['сцена'].value_counts(normalize=True).reindex(ok).fillna(0); w3 = w3 / w3.sum()
    m1 = A.groupby('сцена')['reads'].median().reindex(ok)
    m3 = Bq.groupby('сцена')['reads'].median().reindex(ok)
    cov1 = A['сцена'].isin(ok).mean(); cov3 = Bq['сцена'].isin(ok).mean()
    tab = pd.DataFrame({'вес_эпоха1': w1, 'вес_эпоха3': w3, 'мед_reads_эпоха1': m1, 'мед_reads_эпоха3': m3,
                        'п.п. сдвиг веса': (w3 - w1) * 100})
    print(tab.to_string(float_format=lambda v: f'{v:,.4f}'))
    print(f"   покрытие статей: эпоха1 {cov1:.1%}, эпоха3 {cov3:.1%}")
    L11 = float((w1 * m1).sum()); L13 = float((w1 * m3).sum())
    L31 = float((w3 * m1).sum()); L33 = float((w3 * m3).sum())
    g11 = float(np.exp((w1 * np.log(m1)).sum())); g13 = float(np.exp((w1 * np.log(m3)).sum()))
    g31 = float(np.exp((w3 * np.log(m1)).sum())); g33 = float(np.exp((w3 * np.log(m3)).sum()))
    print(f"   Арифм. агрегат: L(вес1,мед1)={L11:,.0f}  L(вес1,мед3)={L13:,.0f}  L(вес3,мед1)={L31:,.0f}  L(вес3,мед3)={L33:,.0f}")
    print(f"   Полное падение L11/L33 = {L11/L33:,.2f}x")
    print(f"     -> вклад смены РАЗДАЧИ (веса эпохи1 зафиксированы): L11/L13 = {L11/L13:,.2f}x")
    print(f"     -> вклад смены СМЕСИ  (медианы эпохи3 зафиксированы): L13/L33 = {L13/L33:,.2f}x")
    print(f"     -> вклад смены СМЕСИ  (медианы эпохи1 зафиксированы): L11/L31 = {L11/L31:,.2f}x")
    print(f"   Геом. агрегат (лог-аддитивное разложение): полное {g11/g33:,.2f}x = раздача {g11/g13:,.2f}x * смесь {g13/g33:,.2f}x")
    print(f"   Доля падения (в логах), объяснённая СМЕСЬЮ: {np.log(g13/g33)/np.log(g11/g33):.1%}; РАЗДАЧЕЙ: {np.log(g11/g13)/np.log(g11/g33):.1%}")

print("\n" + "=" * 130)
print("S. КОНТРПРИМЕРЫ: стол_еда ce=True на дне — крайние случаи")
print("=" * 130)
g = e3[e3['сцена'] == 'стол_еда'][['date', 'title_studio', 'shows', 'opens', 'reads', 'ctr', 'read_rate', 'comments', 'age_days']]
print(g.sort_values('reads', ascending=False).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
print("\n   Застрявшие статьи из Факта 11 досье — какой у них ce?")
for t in ['Организация', 'Десертные приборы', 'китайского столового', 'Аперитив', 'зоны тарелки', 'Передавайте кружки', 'бокалы к праздничному']:
    z = m[m['title_studio'].str.contains(t, na=False)]
    for _, r in z.iterrows():
        print(f"     {r['date'].date()} | ce={r['ce']} | {r['title_studio'][:52]:52s} | shows={r['shows']:>8,.0f} reads={r['reads']:>6,.0f}")
