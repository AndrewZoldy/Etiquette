# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1: верхняя граница возрастного недосчёта дочитываний."""
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 400)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
rng = np.random.default_rng(20260726)


def boot_med(x, n=10000):
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    if len(x) < 3:
        return (np.nan, np.nan)
    s = rng.choice(x, size=(n, len(x)), replace=True)
    md = np.median(s, axis=1)
    return (np.percentile(md, 2.5), np.percentile(md, 97.5))


print("=" * 100)
print("ТРЕБОВАНИЕ 1. ВОЗРАСТНОЙ НЕДОСЧЁТ")
print("=" * 100)

# ---------- 0. Насыщенный уровень: эпоха 1, age>550 ----------
sat = m[(m['эпоха'] == '1_до_спада') & (m['age_days'] > 550) & (m['ce'] == True)]
print(f"\n[0] Насыщенный эталон: эпоха 1_до_спада, age_days>550, ce=True. n={len(sat)}")
print(f"    даты: {sat['date'].min().date()} .. {sat['date'].max().date()}")
for col in ['comments_per_read', 'likes_per_read', 'subs_per_read', 'read_rate', 'ctr']:
    lo, hi = boot_med(sat[col])
    print(f"    медиана {col:20s} = {sat[col].median():.6f}   CI95 [{lo:.6f}; {hi:.6f}]")

print("\n[0b] Устойчивость эталона: медиана cpr/lpr по подполосам возраста внутри эпохи 1 (ce=True)")
bands1 = [(300, 400), (400, 550), (550, 700), (700, 900), (900, 1250)]
rows = []
e1 = m[(m['эпоха'] == '1_до_спада') & (m['ce'] == True)]
for a, b in bands1:
    g = e1[(e1['age_days'] >= a) & (e1['age_days'] < b)]
    if len(g) == 0:
        continue
    rows.append({'полоса': f'{a}-{b}', 'n': len(g),
                 'даты': f"{g['date'].min().date()}..{g['date'].max().date()}",
                 'cpr': g['comments_per_read'].median(),
                 'lpr': g['likes_per_read'].median(),
                 'spr': g['subs_per_read'].median(),
                 'read_rate': g['read_rate'].median(),
                 'ctr': g['ctr'].median(),
                 'reads': g['reads'].median()})
print(pd.DataFrame(rows).to_string(index=False))

# ---------- 1. Лестница внутри эпохи «дно», ce=True ----------
d = m[(m['эпоха'] == '3_дно') & (m['ce'] == True)].copy()
print(f"\n[1] Эпоха 3_дно, ce=True: n={len(d)}, age_days {d['age_days'].min()}..{d['age_days'].max()}")
wins = [(0, 45), (45, 75), (75, 110), (110, 150), (150, 200), (200, 270)]
cpr_sat = sat['comments_per_read'].median()
lpr_sat = sat['likes_per_read'].median()
spr_sat = sat['subs_per_read'].median()
rows = []
for a, b in wins:
    g = d[(d['age_days'] >= a) & (d['age_days'] < b)]
    lo_c, hi_c = boot_med(g['comments_per_read'])
    rows.append({
        'окно_age': f'{a}-{b}', 'n': len(g),
        'даты': f"{g['date'].min().date()}..{g['date'].max().date()}" if len(g) else '-',
        'cpr': g['comments_per_read'].median(),
        'cpr_CI_lo': lo_c, 'cpr_CI_hi': hi_c,
        'мнж_cpr': g['comments_per_read'].median() / cpr_sat,
        'мнж_CI_lo': lo_c / cpr_sat, 'мнж_CI_hi': hi_c / cpr_sat,
        'lpr': g['likes_per_read'].median(),
        'мнж_lpr': g['likes_per_read'].median() / lpr_sat,
        'spr': g['subs_per_read'].median(),
        'мнж_spr': (g['subs_per_read'].median() / spr_sat) if spr_sat else np.nan,
        'reads_med': g['reads'].median(), 'shows_med': g['shows'].median(),
        'read_rate': g['read_rate'].median(), 'ctr': g['ctr'].median(),
        'min_per_read': g['min_per_read'].median(),
    })
t1 = pd.DataFrame(rows)
print("\n--- Лестница cpr / lpr и множители недосчёта (эталон cpr=%.6f, lpr=%.6f, spr=%.6f) ---" % (cpr_sat, lpr_sat, spr_sat))
print(t1[['окно_age', 'n', 'даты', 'cpr', 'cpr_CI_lo', 'cpr_CI_hi', 'мнж_cpr', 'мнж_CI_lo', 'мнж_CI_hi']].to_string(index=False, float_format=lambda v: f'{v:,.4f}'))
print()
print(t1[['окно_age', 'n', 'lpr', 'мнж_lpr', 'spr', 'мнж_spr', 'reads_med', 'shows_med', 'read_rate', 'ctr', 'min_per_read']].to_string(index=False, float_format=lambda v: f'{v:,.4f}'))

# ---------- 2. КРИТИЧЕСКИЙ ТЕСТ: плоскость read_rate и ctr по возрасту ----------
print("\n[2] Если reads лагируют, а opens/shows нет -> read_rate должен расти с возрастом.")
print("    Бутстрап-CI медианы read_rate и ctr по тем же окнам (эпоха дно, ce=True):")
rows = []
for a, b in wins:
    g = d[(d['age_days'] >= a) & (d['age_days'] < b)]
    rlo, rhi = boot_med(g['read_rate'])
    clo, chi = boot_med(g['ctr'])
    rows.append({'окно': f'{a}-{b}', 'n': len(g),
                 'read_rate': g['read_rate'].median(), 'rr_lo': rlo, 'rr_hi': rhi,
                 'rr_инд_к_эталону': g['read_rate'].median() / sat['read_rate'].median(),
                 'ctr': g['ctr'].median(), 'ctr_lo': clo, 'ctr_hi': chi,
                 'ctr_инд': g['ctr'].median() / sat['ctr'].median()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.4f}'))

# ---------- 3. Воспроизведение Факта 2 на ce=True ----------
print("\n[3] Факт 2 досье, воспроизведение на ce=True и на всей смеси:")
coh = [(0, 60), (150, 220), (300, 400), (400, 550)]
rows = []
for a, b in coh:
    ga = m[(m['age_days'] >= a) & (m['age_days'] < b)]
    gc = ga[ga['ce'] == True]
    rows.append({'возраст': f'{a}-{b}', 'n_все': len(ga), 'shows_все': ga['shows'].median(), 'reads_все': ga['reads'].median(),
                 'n_ce': len(gc), 'shows_ce': gc['shows'].median(), 'reads_ce': gc['reads'].median(),
                 'даты': f"{ga['date'].min().date()}..{ga['date'].max().date()}"})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.0f}'))

# ---------- 4. Кривая накопления комментариев (независимая шкала) ----------
print("\n[4] НЕЗАВИСИМАЯ ПРОВЕРКА: кривая накопления комментариев по created_ts.")
cd = os.path.join(B, 'out', 'comments')
recs = []
for f in os.listdir(cd):
    if not f.endswith('.json'):
        continue
    try:
        j = json.load(open(os.path.join(cd, f), encoding='utf-8'))
    except Exception:
        continue
    oid = j.get('oid')
    cs = j.get('comments') or []
    for cm in cs:
        ts = cm.get('created_ts')
        if ts:
            recs.append((oid, ts))
cdf = pd.DataFrame(recs, columns=['oid', 'ts'])
print("   комментариев с ts:", len(cdf), " статей:", cdf['oid'].nunique())
# нормализуем ts
mx = cdf['ts'].max()
unit = 'ms' if mx > 1e12 else 's'
cdf['t'] = pd.to_datetime(cdf['ts'], unit=unit)
print("   диапазон дат комментариев:", cdf['t'].min(), "..", cdf['t'].max(), f"(unit={unit})")
pub = m.set_index('oid')['date']
cdf['pub'] = cdf['oid'].map(pub)
cdf = cdf.dropna(subset=['pub'])
cdf['dage'] = (cdf['t'] - cdf['pub']).dt.total_seconds() / 86400.0
print("   отрицательных dage:", (cdf['dage'] < -0.05).sum(), " медиана dage:", cdf['dage'].median())
# для зрелых статей эпохи 1 (age>550): доля комментариев, пришедших в первые N дней
mature_oids = set(sat['oid'])
cm_mat = cdf[cdf['oid'].isin(mature_oids) & (cdf['dage'] >= -0.05)]
print(f"\n   Зрелые статьи (эпоха1, age>550, ce=True) с комментариями: {cm_mat['oid'].nunique()} шт, {len(cm_mat)} комментариев")
tot = cm_mat.groupby('oid').size()
use = tot[tot >= 10].index          # правило: группа <10 - вывод не формулируется
cmu = cm_mat[cm_mat['oid'].isin(use)]
print(f"   из них с >=10 комментариями: {len(use)} статей, {len(cmu)} комментариев")
print("\n   fc(N) = доля комментариев статьи, пришедших в первые N дней (медиана по статьям, и агрегат):")
rows = []
g_tot = cmu.groupby('oid').size()
for N in [7, 14, 30, 45, 60, 75, 110, 150, 200, 270, 365]:
    within = cmu[cmu['dage'] <= N].groupby('oid').size().reindex(g_tot.index).fillna(0)
    fr = within / g_tot
    rows.append({'N_дней': N, 'fc_медиана': fr.median(), 'fc_агрегат': within.sum() / g_tot.sum(),
                 'fc_p25': fr.quantile(.25), 'fc_p75': fr.quantile(.75)})
fc = pd.DataFrame(rows)
print(fc.to_string(index=False, float_format=lambda v: f'{v:,.4f}'))

# скорректированный множитель: 1/fr(t) = (cpr_obs/cpr_sat)/fc(t)
print("\n[5] Скорректированный множитель недосчёта reads: 1/fr = (cpr_obs/cpr_sat) / fc(середина окна)")
fcmap = dict(zip(fc['N_дней'], fc['fc_агрегат']))
mid = {'0-45': 22, '45-75': 60, '75-110': 92, '110-150': 130, '150-200': 175, '200-270': 235}
def fc_at(x):
    xs = sorted(fcmap); import numpy as _np
    return float(_np.interp(x, xs, [fcmap[k] for k in xs]))
rows = []
for _, r in t1.iterrows():
    w = r['окно_age']; mm_ = mid[w]; f_ = fc_at(mm_)
    rows.append({'окно': w, 'n': int(r['n']), 'мнж_сырой_cpr': r['мнж_cpr'], 'fc(mid)': f_,
                 'мнж_скорр': r['мнж_cpr'] / f_, 'мнж_lpr_сырой': r['мнж_lpr']})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

# ---------- 6. Месячные медианы reads ce=True для апр-июл 2026 ----------
print("\n[6] Последние месяцы выборки (ce=True):")
mm2 = m[m['ce'] == True].copy(); mm2['ymS'] = mm2['ym'].astype(str)
g = mm2[mm2['ymS'] >= '2026-03'].groupby('ymS').agg(n=('oid', 'size'), reads=('reads', 'median'),
                                                    shows=('shows', 'median'), cpr=('comments_per_read', 'median'),
                                                    age=('age_days', 'median'))
print(g.to_string(float_format=lambda v: f'{v:,.4f}'))
t1.to_pickle(os.path.join(B, 'q2_t1.pkl'))
fc.to_pickle(os.path.join(B, 'q2_fc.pkl'))
