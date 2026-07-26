# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
D = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/'
m = pd.read_pickle(D + 'full.pkl')
m['date'] = pd.to_datetime(m['date'])
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['ceT'] = (m['comments_enabled'] == True)
m['svet'] = m['title_studio'].astype(str).str.startswith('Светская жизнь Петербурга')
m['clean2'] = m['ceT'] & (~m['svet'])
rng = np.random.default_rng(20260726)

def ratio_ci(a, b, n=4000):
    a = np.asarray(a, float); b = np.asarray(b, float); r = np.empty(n)
    for i in range(n):
        r[i] = np.median(rng.choice(a, len(a), True)) / max(np.median(rng.choice(b, len(b), True)), 1e-9)
    return np.percentile(r, [2.5, 97.5])

print('=== F. Поиск ДРУГИХ производственных потоков (регулярные слоты / шаблоны заголовков) ===')
# префиксы заголовков до двоеточия
pref = m['title_studio'].astype(str).str.split(':').str[0].str.strip()
vc = pref.value_counts()
print('повторяющиеся префиксы (>=4):')
for p, c in vc[vc >= 4].items():
    sub = m[pref == p]
    print(f'  {c:3d}  "{p[:55]}"  окно {sub["date"].min().date()}..{sub["date"].max().date()}  '
          f'мед_shows={sub["shows"].median():.0f} мед_reads={sub["reads"].median():.0f} ceF={(~sub["ceT"]).sum()}')
print()
print('серийная_рубрика==1 всего:', (m['серийная_рубрика'] == 1).sum())
s1 = m[m['серийная_рубрика'] == 1]
print('  по полугодиям:', s1['half'].value_counts().sort_index().to_dict())
print('  мед reads', s1['reads'].median(), ' ceF', (~s1['ceT']).sum())

print()
print('=== G. Два потока: их вес в эпохе дно и в 2026H1 ===')
for lab, sub in [('эпоха дно', m[m['эпоха'] == '3_дно']), ('2026H1', m[m['half'] == '2026H1']),
                 ('2026 май-июль', m[(m['date'] >= '2026-05-01')])]:
    tot_r = sub['reads'].sum(); tot_s = sub['shows'].sum()
    for nm, msk in [('ceF серия', ~sub['ceT'] & sub['comments_enabled'].eq(False)), ('Светская жизнь', sub['svet'])]:
        q = sub[msk]
        if len(q) == 0: continue
        print(f'{lab:14s} {nm:15s} n={len(q):3d} ({len(q)/len(sub)*100:4.1f}% статей)  '
              f'доля reads={q["reads"].sum()/tot_r*100:5.2f}%  доля shows={q["shows"].sum()/tot_s*100:5.2f}%  мед_reads={q["reads"].median():.0f}')
    print(f'{lab:14s} {"итого n":15s} n={len(sub)}  мед_reads(сырьё)={sub["reads"].median():.0f}  '
          f'мед_reads(ce=T)={sub[sub["ceT"]]["reads"].median():.0f}  мед_reads(двойн.чистка)={sub[sub["ceT"] & ~sub["svet"]]["reads"].median():.0f}')

print()
print('=== H. Возраст: пересечение носителей по эпохам (ce=True) ===')
for ep in ['1_до_спада', '2_склон', '3_дно']:
    s = m[(m['эпоха'] == ep) & m['ceT']]['age_days']
    print(f'{ep:12s} n={len(s):3d} age min={s.min():.0f} p50={s.median():.0f} max={s.max():.0f}')
a0 = m[m['ceT'] & (m['эпоха'] == '1_до_спада')]['age_days']; a1 = m[m['ceT'] & (m['эпоха'] == '3_дно')]['age_days']
print('пересечение диапазонов:', max(a0.min(), a1.min()), '..', min(a0.max(), a1.max()), '-> статей post=0 в диапазоне post=1:', ((a0 >= a1.min()) & (a0 <= a1.max())).sum())

print()
print('=== I. Контентный сдвиг 2024H2 -> 2025H1 (ce=True), моя старая претензия к Г1 ===')
for col in ['сцена', 'функция', 'порог_входа']:
    t = pd.crosstab(m[m['ceT'] & m['half'].isin(['2024H2', '2025H1'])]['half'],
                    m[m['ceT'] & m['half'].isin(['2024H2', '2025H1'])][col], normalize='index') * 100
    print(col); print(t.round(1).to_string())
sub = m[m['ceT'] & m['half'].isin(['2024H2', '2025H1'])]
print('n_words медиана:', sub.groupby('half')['n_words'].median().to_dict())

print()
print('=== J. Кумулятивные ВАЛОВЫЕ подписки как верхняя граница базы (правило 1: односторонняя граница) ===')
tot = m[['date', 'subs']].copy()
for f in ['rol.pkl', 'pos.pkl']:
    try:
        x = pd.read_pickle(D + f)
        x['date'] = pd.to_datetime(x['date'])
        tot = pd.concat([tot, x[['date', 'subs']]], ignore_index=True)
    except Exception as e:
        print('  нет', f, e)
tot = tot.dropna().sort_values('date')
tot['cum'] = tot['subs'].cumsum()
print('всего валовых подписок за всё время:', int(tot['subs'].sum()))
for d in ['2023-12-31', '2024-06-30', '2024-12-31', '2025-06-30', '2025-10-31', '2026-07-25']:
    print(f'  накоплено к {d}: {int(tot.loc[tot["date"] <= d, "subs"].sum()):,}'.replace(',', ' '))
print('текущая заявленная база (июль 2026): 88 465')
ub_2024H1 = tot.loc[tot['date'] <= '2024-06-30', 'subs'].sum()
print(f'ВЕРХНЯЯ граница базы на конец 2024H1 = {int(ub_2024H1)} -> база выросла НЕ МЕНЬШЕ чем в {88465/ub_2024H1:.2f}x')
ub_2025H1 = tot.loc[tot['date'] <= '2025-06-30', 'subs'].sum()
print(f'ВЕРХНЯЯ граница базы на конец 2025H1 = {int(ub_2025H1)} -> рост к июлю 2026 НЕ МЕНЬШЕ {88465/ub_2025H1:.2f}x')
