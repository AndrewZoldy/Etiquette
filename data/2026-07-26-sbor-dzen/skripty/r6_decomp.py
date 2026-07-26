# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load, wmedian, std_weights
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = load()
W0, W1 = pd.Timestamp('2025-09-16'), pd.Timestamp('2026-05-21 23:59:59')
w = m[(m['date']>=W0)&(m['date']<=W1)]

print("="*110)
print("РАЗЛОЖЕНИЕ ЭФФЕКТА В log10-ШКАЛЕ (база для пересчёта share_of_effect)")
print("="*110)
A1 = m[m['half']=='2025H1']; B1 = m[m['half']=='2026H1']
A2 = A1[A1['ce']==True];     B2 = B1[B1['ce']==True]
A3 = A2[A2['age_days']>=150];B3 = B2[B2['age_days']>=150]

# ступень 4 — сцена (наиболее устойчивый вариант, покрытие 93,5%)
ka = A2['сцена']; kb = B2['сцена']
cnt = kb.value_counts(); keep = set(cnt[cnt>=5].index)
Ax = A2.copy(); Bx = B2.copy()
Ax['cell2']=ka.where(ka.isin(keep),'ПРОЧЕЕ'); Bx['cell2']=kb.where(kb.isin(keep),'ПРОЧЕЕ')
wB = std_weights(Bx,Ax,'cell2')
r_std = wmedian(Ax['reads'].values)/wmedian(Bx['reads'].values,wB)

steps = [('сырой разрыв 2025H1->2026H1', A1['reads'].median()/B1['reads'].median()),
         ('после удаления серии ce=False', A2['reads'].median()/B2['reads'].median()),
         ('+ стандартизация состава (сцена)', r_std),
         ('+ ценз зрелости age>=150 (сцена, n26=26)', 3.90)]
tot = np.log10(steps[0][1])
prev = tot; rows=[]
for i,(lab,r) in enumerate(steps):
    lg = np.log10(r)
    rows.append(dict(шаг=lab, отношение=round(r,2), log10=round(lg,4),
                     съедено_на_шаге_lg=round(prev-lg,4) if i>0 else 0.0,
                     доля_общего_разрыва_снята=round((prev-lg)/tot*100,1) if i>0 else 0.0,
                     остаток_от_общего=round(lg/tot*100,1)))
    prev = lg
print(pd.DataFrame(rows).to_string(index=False))
print(f"\nОбщий разрыв в log10 = {tot:.4f} (это и есть 100%).")
print("Чтение: 'серия ce=False' и 'состав' — это ДВА РАЗНЫХ вклада, серия снимает больше.")
print()

print("--- Тот же расчёт для ПОКАЗОВ (вторичная метрика, для сверки с Фактом 1) ---")
r0 = A1['shows'].median()/B1['shows'].median(); r1 = A2['shows'].median()/B2['shows'].median()
kb2 = B2['сцена']; cnt2=kb2.value_counts(); keep2=set(cnt2[cnt2>=5].index)
Ay=A2.copy(); By=B2.copy()
Ay['cell2']=A2['сцена'].where(A2['сцена'].isin(keep2),'ПРОЧЕЕ'); By['cell2']=kb2.where(kb2.isin(keep2),'ПРОЧЕЕ')
r2 = wmedian(Ay['shows'].values)/wmedian(By['shows'].values, std_weights(By,Ay,'cell2'))
print(f"сырьё {r0:.2f}x -> ce=True {r1:.2f}x -> +состав {r2:.2f}x   "
      f"(снято серией {(np.log10(r0)-np.log10(r1))/np.log10(r0)*100:.1f}%, составом {(np.log10(r1)-np.log10(r2))/np.log10(r0)*100:.1f}%)")
print()

print("="*110)
print("НЕОДНОРОДНОСТЬ ВНУТРИ СЕРИИ ce=False (контрпримеры к трактовке 'режим публикации')")
print("="*110)
f = m[m['ce']==False].copy()
for col in ['вопрос','цифра_в_заголовке','негативная_рамка','спорность','конкретный_якорь','обращение_вы','фокус','объект_осуждения']:
    if col not in m.columns: continue
    g = f.groupby(f[col].astype(str)).agg(n=('shows','size'), мед_показов=('shows','median'), мед_дочит=('reads','median'))
    g['вывод'] = np.where(g['n']>=10,'','группа <10 — вывод не формулируется')
    print(f"[{col}] внутри серии ce=False"); print(g.to_string()); print()

print("--- Доля признаков разметки: серия vs ce=True в окне ---")
rows=[]
for col in ['вопрос','цифра_в_заголовке','негативная_рамка','спорность','конкретный_якорь','обращение_вы']:
    if col not in m.columns: continue
    a = pd.to_numeric(f[col], errors='coerce'); b = pd.to_numeric(w[w['ce']==True][col], errors='coerce')
    rows.append(dict(признак=col, доля_серия=round(a.mean(),3), доля_ceTrue_окно=round(b.mean(),3)))
print(pd.DataFrame(rows).to_string(index=False))
print()

print("--- 6 успешных статей серии (>500k показов) против 10 худших ---")
top = f.nlargest(6,'shows'); bot = f.nsmallest(10,'shows')
cols=['date','title_studio','shows','reads','ctr','вопрос','спорность','порог_входа','функция','n_words']
print("[ТОП-6]"); print(top[cols].to_string(index=False))
print("\n[ХУДШИЕ-10]"); print(bot[cols].to_string(index=False))
print()

print("--- Внутри серии: связь CTR с показами (Спирмен) и распределение показов ---")
print(f"Спирмен CTR-показы внутри серии: {f['ctr'].corr(f['shows'],method='spearman'):+.3f} (n={len(f)})")
print("Перцентили показов серии:", {p: int(np.percentile(f['shows'],p)) for p in [10,25,50,75,90,95]})
print(f"Доля серии с показами >100 000: {(f['shows']>1e5).mean()*100:.1f}%  ({(f['shows']>1e5).sum()} шт.)")
print(f"Доля серии с показами <10 000:  {(f['shows']<1e4).mean()*100:.1f}%  ({(f['shows']<1e4).sum()} шт.)")
print()

print("--- Хронология внутри серии: помесячная медиана показов ---")
print(f.groupby(f['date'].dt.to_period('M')).agg(n=('shows','size'), мед_показов=('shows','median'),
                                                 мед_дочит=('reads','median'), мед_CTR=('ctr','median')).round(4).to_string())
