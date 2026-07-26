# -*- coding: utf-8 -*-
"""Возрастно-сопоставленный эталон на комментарных часах + докрутка требования 1."""
import pandas as pd, numpy as np, os, json
pd.set_option('display.width', 280); pd.set_option('display.max_columns', 80); pd.set_option('display.max_rows', 400)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['halfX'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
rng = np.random.default_rng(11)

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

info = m.set_index('oid')[['date', 'halfX', 'эпоха', 'ce', 'age_days', 'reads', 'shows', 'comments']]

print("=" * 110)
print("E. ХВОСТ НАКОПЛЕНИЯ: доля комментариев после дня X, по полугодию публикации (только age>=X+60)")
print("=" * 110)
rows = []
for h in ['2023H2', '2024H1', '2024H2', '2025H1']:
    g = info[(info['halfX'] == h) & (info['ce'] == True)]
    cg = c[c['oid'].isin(g.index)]
    Cf = cg.groupby('oid').size().rename('Cf')
    g = g.join(Cf).dropna(subset=['Cf'])
    g = g[g['Cf'] >= 10]
    if len(g) < 10:
        rows.append({'полугодие': h, 'n': len(g), 'прим': 'n<10'})
        continue
    r = {'полугодие': h, 'n': len(g), 'медиана_age': g['age_days'].median()}
    for X in [45, 110, 200, 270, 365]:
        w = cg[cg['dage'] <= X].groupby('oid').size().reindex(g.index).fillna(0)
        r[f'C({X})/Cитог'] = (w / g['Cf']).median()
    rows.append(r)
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

print("\n" + "=" * 110)
print("F. ВОЗРАСТНО-СОПОСТАВЛЕННОЕ СРАВНЕНИЕ ДОЧИТЫВАНИЙ.")
print("   База — пиковая когорта 2025H1 (ce=True, age 390..570). Её собственные комментарные часы")
print("   дают fc(t)=C(t)/C(age). R_hat(t) = reads_наблюд * fc(t)  -- реконструкция уровня на возрасте t.")
print("   Сопоставляем с наблюдаемой медианой reads когорт эпохи «дно» того же возраста.")
print("=" * 110)


def boot_ratio(a, b, n=6000):
    a = np.asarray(pd.Series(a).dropna(), float); b = np.asarray(pd.Series(b).dropna(), float)
    if len(a) < 3 or len(b) < 3:
        return (np.nan, np.nan)
    ra = np.median(rng.choice(a, size=(n, len(a)), replace=True), axis=1)
    rb = np.median(rng.choice(b, size=(n, len(b)), replace=True), axis=1)
    q = ra / np.where(rb == 0, np.nan, rb)
    return (np.nanpercentile(q, 2.5), np.nanpercentile(q, 97.5))


for base_name, mask in [('2025H1 (пик)', (info['halfX'] == '2025H1')),
                        ('2024H2', (info['halfX'] == '2024H2')),
                        ('2024H1', (info['halfX'] == '2024H1'))]:
    base = info[mask & (info['ce'] == True)].copy()
    cb = c[c['oid'].isin(base.index)]
    Cf = cb.groupby('oid').size().rename('Cf')
    base = base.join(Cf).dropna(subset=['Cf'])
    base = base[base['Cf'] >= 10]
    d = m[(m['эпоха'] == '3_дно') & (m['ce'] == True)]
    print(f"\n--- База {base_name}: n={len(base)} (со >=10 комм.), медиана reads_итог={base['reads'].median():,.0f} ---")
    rows = []
    for a, b, mid in [(0, 45, 22), (45, 75, 60), (75, 110, 92), (110, 150, 130), (150, 200, 175), (200, 270, 235)]:
        g = d[(d['age_days'] >= a) & (d['age_days'] < b)]
        w = cb[cb['dage'] <= mid].groupby('oid').size().reindex(base.index).fillna(0)
        rhat = base['reads'] * (w / base['Cf'])
        lo, hi = boot_ratio(rhat, g['reads'])
        rows.append({'окно': f'{a}-{b}', 'mid': mid, 'n_дно': len(g), 'reads_дно': g['reads'].median(),
                     'fc(mid)_база': (w / base['Cf']).median(), 'R_hat_база': rhat.median(),
                     'отн_база/дно': rhat.median() / g['reads'].median(),
                     'CI_lo': lo, 'CI_hi': hi})
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print("\n" + "=" * 110)
print("G. Согласованность: если R(t)~C(t) (комментарии и дочитывания копятся вместе), то cpr обязан")
print("   быть плоским по возрасту. Проверка на эпохе 1 (там возраст велик) и на эпохе дна.")
print("=" * 110)
print("   -> см. лестницу cpr в требовании 1: она НЕ плоская, значит комментарии копятся быстрее reads.")
print("   Оценка «на сколько быстрее»: fr(t) = fc(t) / (cpr_obs/cpr_sat).")
t1 = pd.read_pickle(os.path.join(B, 'q2_t1.pkl'))
# fc для эпохи 3 из её собственных часов, нормировка на 200 дней, с поправкой на хвост от 2025H1
d3 = info[(info['эпоха'] == '3_дно') & (info['ce'] == True) & (info['age_days'] >= 200)]
c3 = c[c['oid'].isin(d3.index)]
C200 = c3[c3['dage'] <= 200].groupby('oid').size().rename('C200')
d3 = d3.join(C200).dropna(subset=['C200']); d3 = d3[d3['C200'] >= 10]
b25 = info[(info['halfX'] == '2025H1') & (info['ce'] == True)]
cb25 = c[c['oid'].isin(b25.index)]
Cf25 = cb25.groupby('oid').size().rename('Cf'); b25 = b25.join(Cf25).dropna(subset=['Cf']); b25 = b25[b25['Cf'] >= 10]
w200 = cb25[cb25['dage'] <= 200].groupby('oid').size().reindex(b25.index).fillna(0)
tail = (w200 / b25['Cf']).median()
print(f"   хвост: C(200)/C_итог у пиковой когорты 2025H1 = {tail:.3f} (n={len(b25)})")
rows = []
for (a, b, mid), (_, r) in zip([(0, 45, 22), (45, 75, 60), (75, 110, 92), (110, 150, 130), (150, 200, 175), (200, 270, 235)], t1.iterrows()):
    w = c3[c3['dage'] <= mid].groupby('oid').size().reindex(d3.index).fillna(0)
    g200 = (w / d3['C200']).median()
    fc_abs = g200 * tail
    rows.append({'окно': f'{a}-{b}', 'mid': mid, 'g(mid|200)_эпоха3': g200, 'fc_абс': fc_abs,
                 'мнж_cpr': r['мнж_cpr'], 'fr=fc/мнж': fc_abs / r['мнж_cpr'],
                 'недосчёт_reads_1/fr': r['мнж_cpr'] / fc_abs})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
print(f"   (n эпоха3 с age>=200 и >=10 комм.: {len(d3)})")
