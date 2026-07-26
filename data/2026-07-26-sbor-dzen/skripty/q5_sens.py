# -*- coding: utf-8 -*-
"""Чувствительность множителя к выбору эталона + попытка воспроизвести цифры критика + чистая панель F."""
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 280); pd.set_option('display.max_columns', 80); pd.set_option('display.max_rows', 400)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['halfX'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
rng = np.random.default_rng(3)

print("=" * 110)
print("H. ЧУВСТВИТЕЛЬНОСТЬ: медиана cpr «зрелых» статей зависит от когорты публикации")
print("=" * 110)
rows = []
for h in ['2023H2', '2024H1', '2024H2', '2025H1']:
    g = m[(m['halfX'] == h) & (m['ce'] == True)]
    rows.append({'полугодие_публикации': h, 'n': len(g), 'медиана_age': g['age_days'].median(),
                 'cpr': g['comments_per_read'].median(), 'lpr': g['likes_per_read'].median(),
                 'spr': g['subs_per_read'].median(), 'reads': g['reads'].median()})
sens = pd.DataFrame(rows)
print(sens.to_string(index=False, float_format=lambda v: f'{v:,.5f}'))
cpr_obs_045 = 0.079200
print("\n   Множитель для окна 0-45 дней (cpr_obs=%.4f) при разных эталонах:" % cpr_obs_045)
d = m[(m['эпоха'] == '3_дно') & (m['ce'] == True)]
obs = {}
for a, b in [(0, 45), (45, 75), (75, 110), (110, 150), (150, 200), (200, 270)]:
    obs[f'{a}-{b}'] = d[(d['age_days'] >= a) & (d['age_days'] < b)]['comments_per_read'].median()
refs = {'эпоха1 age>550 (эталон критика)': m[(m['эпоха'] == '1_до_спада') & (m['age_days'] > 550) & (m['ce'] == True)]['comments_per_read'].median()}
for h in ['2023H2', '2024H1', '2024H2', '2025H1']:
    refs[f'публикации {h}'] = m[(m['halfX'] == h) & (m['ce'] == True)]['comments_per_read'].median()
refs['вся эпоха1'] = m[(m['эпоха'] == '1_до_спада') & (m['ce'] == True)]['comments_per_read'].median()
tab = pd.DataFrame({k: {w: obs[w] / v for w in obs} for k, v in refs.items()})
tab.loc['ЭТАЛОН cpr'] = pd.Series(refs)
print(tab.to_string(float_format=lambda v: f'{v:,.3f}'))

print("\n" + "=" * 110)
print("I. ПОПЫТКА ВОСПРОИЗВЕСТИ ЦИФРЫ КРИТИКА по Факту 2 (54720/222407/78398/129989)")
print("=" * 110)
for nm, sub in [('ВСЕ 623', m), ('ce=True', m[m['ce'] == True]), ('ce!=False', m[m['ce'] != False])]:
    r = []
    for a, b in [(0, 60), (150, 220), (300, 400), (400, 550)]:
        g = sub[(sub['age_days'] >= a) & (sub['age_days'] < b)]
        r.append(f"{a}-{b}: n={len(g)} shows={g['shows'].median():,.0f} reads={g['reads'].median():,.0f}")
    print(f"  {nm:10s} " + " | ".join(r))
print("\n  Плотная лестница по возрасту, ce=True (n>=10 в окне):")
edges = [0, 30, 60, 90, 120, 150, 180, 220, 260, 300, 350, 400, 450, 500, 550, 650, 800, 1000, 1250]
rows = []
ct = m[m['ce'] == True]
for a, b in zip(edges[:-1], edges[1:]):
    g = ct[(ct['age_days'] >= a) & (ct['age_days'] < b)]
    if len(g) == 0:
        continue
    rows.append({'age': f'{a}-{b}', 'n': len(g), 'даты': f"{g['date'].min().date()}..{g['date'].max().date()}",
                 'shows': g['shows'].median(), 'reads': g['reads'].median(),
                 'вывод' : '' if len(g) >= 10 else 'n<10, не формулируется'})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.0f}'))

print("\n" + "=" * 110)
print("J. ЧИСТАЯ ПАНЕЛЬ F: уровень reads берём с ПОЛНОЙ когорты (без отбора по комментариям),")
print("   форму накопления fc(t) — с подвыборки >=10 комментариев той же когорты.")
print("=" * 110)
cd = os.path.join(B, 'out', 'comments')
recs = []
for f in os.listdir(cd):
    if not f.endswith('.json'):
        continue
    j = json.load(open(os.path.join(cd, f), encoding='utf-8'))
    for cm in (j.get('comments') or []):
        if cm.get('created_ts'):
            recs.append((j.get('oid'), cm['created_ts']))
c = pd.DataFrame(recs, columns=['oid', 'ts'])
c['t'] = pd.to_datetime(c['ts'], unit='ms')
c['pub'] = c['oid'].map(m.set_index('oid')['date'])
c = c.dropna(subset=['pub'])
c['dage'] = (c['t'] - c['pub']).dt.total_seconds() / 86400.0
c = c[c['dage'] >= -0.05]
info = m.set_index('oid')[['date', 'halfX', 'эпоха', 'ce', 'age_days', 'reads']]
wins = [(0, 45, 22), (45, 75, 60), (75, 110, 92), (110, 150, 130), (150, 200, 175), (200, 270, 235)]
out = {}
for h in ['2024H1', '2024H2', '2025H1']:
    full = m[(m['halfX'] == h) & (m['ce'] == True)]
    elig = info[(info['halfX'] == h) & (info['ce'] == True)]
    cg = c[c['oid'].isin(elig.index)]
    Cf = cg.groupby('oid').size().rename('Cf')
    elig = elig.join(Cf).dropna(subset=['Cf']); elig = elig[elig['Cf'] >= 10]
    lvl = full['reads'].median()
    col = {}
    for a, b, mid in wins:
        w = cg[cg['dage'] <= mid].groupby('oid').size().reindex(elig.index).fillna(0)
        fc = (w / elig['Cf']).median()
        col[f'{a}-{b}'] = lvl * fc
    out[h] = col
    print(f"  {h}: n_полная={len(full)} медиана reads_итог={lvl:,.0f}; n для формы={len(elig)}")
res = pd.DataFrame(out)
dno = {f'{a}-{b}': m[(m['эпоха'] == '3_дно') & (m['ce'] == True) & (m['age_days'] >= a) & (m['age_days'] < b)]['reads'].median() for a, b, _ in wins}
res['дно_наблюд'] = pd.Series(dno)
for h in ['2024H1', '2024H2', '2025H1']:
    res[f'отн_{h}/дно'] = res[h] / res['дно_наблюд']
print()
print(res.to_string(float_format=lambda v: f'{v:,.2f}'))
