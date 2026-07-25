# -*- coding: utf-8 -*-
"""АУДИТ САМОГО ФИЛЬТРА ce=True: он отбирает разную долю выпуска в разные месяцы."""
import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
rng = np.random.default_rng(20260726)
m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month<=6,'H1','H2')
m['ymS'] = m['ym'].astype(str)

print("="*120)
print("А. ДОЛЯ ВЫПУСКА, КОТОРУЮ ОТБРАСЫВАЕТ ФИЛЬТР ce=True, ПО МЕСЯЦАМ")
print("   фильтр применяется неравномерно во времени -> он сам создаёт динамику медианы")
print("="*120)
g = m.groupby('ymS').agg(n=('ce','size'), n_ce=('ce','sum'))
g['отброшено'] = g['n']-g['n_ce']; g['доля_отброшена'] = g['отброшено']/g['n']
print(g.loc['2025-05':].to_string(float_format=lambda v: f"{v:.3f}"))
print(f"\n  до сентября 2025 фильтр не отбрасывает ничего (ce=False впервые {m[~m['ce']]['date'].min():%d.%m.%Y})")
print(f"  в июне-июле 2026 фильтр тоже не отбрасывает ничего")
print("  СЛЕДСТВИЕ: медиана ce=True за дек25-май26 считается по ЛУЧШИМ ~67% выпуска,")
print("             а за июнь-июль 2026 и за все доспадовые месяцы — по 100% выпуска.")

print("\n"+"="*120)
print("Б. ИСПРАВЛЕНИЕ: ЕДИНАЯ СТАВКА ОТСЕЧЕНИЯ. В каждом месяце отбрасываем нижние 27% по shows")
print("   (27% = средняя доля ce=False в период сен2025-май2026). Тогда все месяцы сопоставимы.")
print("="*120)
K = 0.27
months = [x for x in sorted(g.index) if '2025-05' <= x <= '2026-07']
rows=[]
for mo in months:
    s = m[m['ymS']==mo]
    thr = s['shows'].quantile(K)
    trimmed = s[s['shows']>=thr]
    ce = s[s['ce']]
    rows.append(dict(месяц=mo, n=len(s),
                     мед_ВСЕ=s['reads'].median(),
                     n_ce=len(ce), мед_ce=ce['reads'].median(),
                     n_trim=len(trimmed), мед_trim27=trimmed['reads'].median(),
                     shows_ВСЕ=s['shows'].median(), shows_ce=ce['shows'].median(), shows_trim27=trimmed['shows'].median()))
t = pd.DataFrame(rows)
print(t.to_string(index=False, float_format=lambda v: f"{v:,.0f}".replace(',',' ')))

print("\n"+"="*120)
print("В. ТРИ ШКАЛЫ РЯДОМ, блоками. Какая из них показывает продолжающееся падение после марта 2026?")
print("="*120)
blocks = [('май-июл 2025', ['2025-05','2025-06','2025-07']),
          ('авг-сен 2025', ['2025-08','2025-09']),
          ('окт-дек 2025', ['2025-10','2025-11','2025-12']),
          ('янв-мар 2026', ['2026-01','2026-02','2026-03']),
          ('апр-июл 2026', ['2026-04','2026-05','2026-06','2026-07'])]
print(f"  {'блок':14s} {'n':>4s} {'мед.reads ВСЕ':>14s} {'мед.reads ce':>13s} {'мед.reads trim27':>17s} {'сумма reads, млн':>17s}")
prev=None
for name,mos in blocks:
    s = m[m['ymS'].isin(mos)]
    thr = s.groupby('ymS')['shows'].transform(lambda x: x.quantile(K))
    tr = s[s['shows']>=thr]
    print(f"  {name:14s} {len(s):4d} {s['reads'].median():14,.0f} {s[s['ce']]['reads'].median():13,.0f} {tr['reads'].median():17,.0f} {s['reads'].sum()/1e6:17.3f}".replace(',',' '))
print("\n  Отношения соседних блоков (во сколько раз падает):")
vals={}
for name,mos in blocks:
    s = m[m['ymS'].isin(mos)]
    thr = s.groupby('ymS')['shows'].transform(lambda x: x.quantile(K))
    vals[name]=(s['reads'].median(), s[s['ce']]['reads'].median(), s[s['shows']>=thr]['reads'].median(), s['reads'].sum()/1e6)
names=[b[0] for b in blocks]
print(f"  {'переход':32s} {'ВСЕ':>8s} {'ce=True':>9s} {'trim27':>8s} {'суммы':>8s}")
for i in range(len(names)-1):
    a,b = names[i], names[i+1]
    print(f"  {a+' -> '+b:32s} " + " ".join(f"{vals[a][k]/vals[b][k]:8.2f}" for k in range(4)))

print("\n"+"="*120)
print("Г. ТРЕБОВАНИЕ 3 С ЕДИНОЙ СТАВКОЙ ОТСЕЧЕНИЯ (честное сравнение окон)")
print("   в КАЖДОМ окне отбрасываем нижние 27% по shows, затем сравниваем медианы")
print("="*120)
def trim(w, k=K):
    return w[w['shows'] >= w['shows'].quantile(k)]
def bootr(a,b,B=5000):
    a=np.asarray(a,float); b=np.asarray(b,float)
    ra=np.median(a[rng.integers(0,len(a),size=(B,len(a)))],axis=1)
    rb=np.median(b[rng.integers(0,len(b),size=(B,len(b)))],axis=1)
    r=ra/rb; r=r[np.isfinite(r)]
    return np.median(a)/np.median(b), np.percentile(r,2.5), np.percentile(r,97.5)
T = trim(m[m['half']=='2026H1'])
print(f"  целевое окно 2026H1, единая ставка отсечения 27%: n={len(T)} (для сравнения ce=True давало n=108)")
print(f"  {'окно':8s} {'n_trim':>7s} | {'shows':>34s} | {'opens':>34s} | {'reads':>34s}")
for h in ['2023H2','2024H1','2024H2','2025H1']:
    W = trim(m[m['half']==h]); cells=[]
    for col in ['shows','opens','reads']:
        p,lo,hi = bootr(W[col], T[col])
        cells.append(f"{W[col].median():>9,.0f}/{T[col].median():>7,.0f} x{p:5.2f}[{lo:4.2f};{hi:5.2f}]".replace(',',' '))
    print(f"  {h:8s} {len(W):7d} | " + " | ".join(cells))
print("\n  То же, но целевое окно ещё и с цензом зрелости age>=110:")
T2 = trim(m[(m['half']=='2026H1')&(m['age_days']>=110)])
print(f"  n={len(T2)}")
for h in ['2023H2','2024H1','2024H2','2025H1']:
    W = trim(m[m['half']==h]); cells=[]
    for col in ['shows','opens','reads']:
        p,lo,hi = bootr(W[col], T2[col])
        cells.append(f"{W[col].median():>9,.0f}/{T2[col].median():>7,.0f} x{p:5.2f}[{lo:4.2f};{hi:5.2f}]".replace(',',' '))
    print(f"  {h:8s} {len(W):7d} | " + " | ".join(cells))
