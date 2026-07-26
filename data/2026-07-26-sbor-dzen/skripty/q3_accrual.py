# -*- coding: utf-8 -*-
"""Кривая накопления комментариев как независимые часы. Ломает коллинеарность возраст/календарь."""
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 280); pd.set_option('display.max_columns', 80); pd.set_option('display.max_rows', 400)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
rng = np.random.default_rng(7)

cd = os.path.join(B, 'out', 'comments')
recs = []
for f in os.listdir(cd):
    if not f.endswith('.json'):
        continue
    j = json.load(open(os.path.join(cd, f), encoding='utf-8'))
    for cm in (j.get('comments') or []):
        ts = cm.get('created_ts')
        if ts:
            recs.append((j.get('oid'), ts, cm.get('level')))
c = pd.DataFrame(recs, columns=['oid', 'ts', 'level'])
c['t'] = pd.to_datetime(c['ts'], unit='ms')
c['pub'] = c['oid'].map(m.set_index('oid')['date'])
c = c.dropna(subset=['pub'])
c['dage'] = (c['t'] - c['pub']).dt.total_seconds() / 86400.0
print("комментариев:", len(c), " статей:", c['oid'].nunique())
print("dage<-1:", (c['dage'] < -1).sum(), " min dage:", c['dage'].min())
c = c[c['dage'] >= -0.05].copy()
print("после отсечки отрицательных:", len(c))
print("\nсверка: сумма комментариев по json против колонки comments (Студия)")
tot = c.groupby('oid').size().rename('c_json')
cmp_ = m.set_index('oid')[['comments', 'date', 'эпоха', 'ce', 'reads', 'age_days']].join(tot)
cmp_['c_json'] = cmp_['c_json'].fillna(0)
sub = cmp_[cmp_['comments'] > 20]
print("  n(comments>20):", len(sub), " медиана c_json/comments:", (sub['c_json'] / sub['comments']).median().round(3),
      " p10/p90:", (sub['c_json'] / sub['comments']).quantile([.1, .9]).round(3).tolist())

# ---- A. Форма накопления по КОГОРТАМ ПУБЛИКАЦИИ, нормировка на общий срез T ----
print("\n" + "=" * 100)
print("A. ФОРМА НАКОПЛЕНИЯ КОММЕНТАРИЕВ ПО КОГОРТАМ ПУБЛИКАЦИИ (нормировка на первые T дней)")
print("   g(t|T) = C(t)/C(T). Сравнимо между эпохами: обе когорты наблюдались минимум T дней.")
print("=" * 100)
info = m.set_index('oid')[['date', 'эпоха', 'ce', 'age_days', 'reads', 'comments']]
for T in [110, 200]:
    print(f"\n--- T = {T} дней ---")
    elig = info[(info['age_days'] >= T) & (info['ce'] == True)]
    cc = c[c['oid'].isin(elig.index)]
    cT = cc[cc['dage'] <= T].groupby('oid').size().rename('CT')
    e = elig.join(cT).fillna({'CT': 0})
    e = e[e['CT'] >= 10]                                   # правило n>=10 комментариев
    e['halfX'] = e['date'].dt.year.astype(str) + np.where(e['date'].dt.month <= 6, 'H1', 'H2')
    grp = {'эпоха1 (до 08.2025)': e[e['эпоха'] == '1_до_спада'],
           'эпоха2 склон (08-10.2025)': e[e['эпоха'] == '2_склон'],
           'эпоха3 дно (с 11.2025)': e[e['эпоха'] == '3_дно']}
    ts_ = [3, 7, 14, 21, 30, 45, 60, 75, 110, 150, 200]
    ts_ = [x for x in ts_ if x <= T]
    rows = []
    for nm, g in grp.items():
        if len(g) < 10:
            rows.append({'когорта': nm, 'n': len(g), **{f'g({x})': np.nan for x in ts_}})
            continue
        r = {'когорта': nm, 'n': len(g)}
        for x in ts_:
            w = cc[(cc['oid'].isin(g.index)) & (cc['dage'] <= x)].groupby('oid').size().reindex(g.index).fillna(0)
            r[f'g({x})'] = (w / g['CT']).median()
        rows.append(r)
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

# ---- B. Абсолютная кривая для зрелых: fc(t)=C(t)/C_итог, по когортам публикации ----
print("\n" + "=" * 100)
print("B. fc(t) = C(t)/C_итог, только статьи с age>=550 (успели насытиться), по году-полугодию публикации")
print("=" * 100)
mat = info[(info['age_days'] >= 550) & (info['ce'] == True)].copy()
mat['halfX'] = mat['date'].dt.year.astype(str) + np.where(mat['date'].dt.month <= 6, 'H1', 'H2')
cm = c[c['oid'].isin(mat.index)]
tt = cm.groupby('oid').size().rename('Cf')
mat = mat.join(tt).dropna(subset=['Cf'])
mat = mat[mat['Cf'] >= 10]
rows = []
for h, g in mat.groupby('halfX'):
    if len(g) < 10:
        rows.append({'полугодие': h, 'n': len(g), 'прим': '<10, вывод не формулируется'})
        continue
    r = {'полугодие': h, 'n': len(g)}
    for x in [7, 14, 30, 45, 75, 110, 200, 365]:
        w = cm[(cm['oid'].isin(g.index)) & (cm['dage'] <= x)].groupby('oid').size().reindex(g.index).fillna(0)
        r[f'fc({x})'] = (w / g['Cf']).median()
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

# ---- C. Возрастно-сопоставленный эталон дочитываний ----
print("\n" + "=" * 100)
print("C. ВОЗРАСТНО-СОПОСТАВЛЕННЫЙ ЭТАЛОН. Допущение: внутри жизни статьи комментарии на дочитывание")
print("   постоянны -> R(t) ~ C(t). Тогда R_hat(t) = reads_итог * C(t)/C_итог.")
print("   Сравниваем медиану R_hat(t) зрелых статей эпохи 1 с наблюдаемой медианой reads когорт дна.")
print("=" * 100)
base = info[(info['эпоха'] == '1_до_спада') & (info['age_days'] >= 550) & (info['ce'] == True)].copy()
cb = c[c['oid'].isin(base.index)]
Cf = cb.groupby('oid').size().rename('Cf')
base = base.join(Cf).dropna(subset=['Cf'])
base = base[base['Cf'] >= 10]
print("  база: n =", len(base), " даты", base['date'].min().date(), "..", base['date'].max().date())
d = m[(m['эпоха'] == '3_дно') & (m['ce'] == True)]
wins = [(0, 45, 22), (45, 75, 60), (75, 110, 92), (110, 150, 130), (150, 200, 175), (200, 270, 235)]
rows = []
for a, b, mid in wins:
    g = d[(d['age_days'] >= a) & (d['age_days'] < b)]
    w = cb[cb['dage'] <= mid].groupby('oid').size().reindex(base.index).fillna(0)
    rhat = base['reads'] * (w / base['Cf'])
    rows.append({'окно': f'{a}-{b}', 'mid': mid, 'n_дно': len(g),
                 'reads_дно_медиана': g['reads'].median(),
                 'n_база': len(base), 'R_hat_база_медиана': rhat.median(),
                 'отношение_база/дно': rhat.median() / g['reads'].median() if g['reads'].median() else np.nan,
                 'reads_итог_база': base['reads'].median()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

# ---- D. Сколько реально «доливается» после 270 дней? прямая оценка на комментарной шкале ----
print("\n" + "=" * 100)
print("D. Доля комментариев, пришедших ПОСЛЕ 270 дней, у зрелых статей эпохи 1 (медиана и агрегат)")
print("=" * 100)
w270 = cb[cb['dage'] <= 270].groupby('oid').size().reindex(base.index).fillna(0)
sh = 1 - w270 / base['Cf']
print(f"  медиана доли позднее 270 дн: {sh.median():.3f}; агрегат: {1 - w270.sum() / base['Cf'].sum():.3f}")
print(f"  доля статей, у которых >50% комментариев пришло после 270 дн: {(sh > .5).mean():.3f}  (n={len(sh)})")
print("\n  Разбивка по полугодию публикации (доля комментариев позднее 270 дн, медиана):")
base['halfX'] = base['date'].dt.year.astype(str) + np.where(base['date'].dt.month <= 6, 'H1', 'H2')
r = base.assign(sh=sh).groupby('halfX').agg(n=('reads', 'size'), доля_позже_270=('sh', 'median'))
print(r.to_string(float_format=lambda v: f'{v:,.3f}'))
