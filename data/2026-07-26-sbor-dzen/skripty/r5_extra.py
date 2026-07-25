# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load, wmedian, std_weights, boot_ratio
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = load()
rng = np.random.default_rng(9)
W0, W1 = pd.Timestamp('2025-09-16'), pd.Timestamp('2026-05-21 23:59:59')

print("="*110)
print("ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ (устойчивость и контрпримеры по правилам 3-6 проекта)")
print("="*110)

# ---- 1. Проблема переиспользования контролей
print("--- 1. Размер пула контроля по ячейкам в окне серии ---")
w = m[(m['date']>=W0)&(m['date']<=W1)]
piv = pd.crosstab([w['сцена'],w['функция'],w['порог_входа']], w['ce'].astype(str))
piv = piv[(piv.sum(axis=1)>0)]
print(piv.to_string())
print()

# ---- 2. Прямое сравнение внутри сцены стол_еда в окне
print("--- 2. Сцена 'стол_еда' в окне 16.09.2025-21.05.2026: ce=False vs ce=True ---")
se = w[w['сцена']=='стол_еда']
g = se.groupby(se['ce'].astype(str)).agg(n=('shows','size'), мед_показов=('shows','median'),
                                         мед_открытий=('opens','median'), мед_дочит=('reads','median'),
                                         мед_CTR=('ctr','median'), мед_дочитываемость=('read_rate','median'),
                                         p25_показов=('shows',lambda s: np.percentile(s,25)),
                                         p75_показов=('shows',lambda s: np.percentile(s,75)))
print(g.round(4).to_string())
a = se[se['ce']==True]['reads'].median(); b = se[se['ce']==False]['reads'].median()
print(f"отношение медиан дочитываний ce=True / ce=False внутри стол_еда = {a/b:.1f}x  (n {(se['ce']==True).sum()} vs {(se['ce']==False).sum()})")
print()
print("--- то же для сцены 'гости_праздники' в окне ---")
gp = w[w['сцена']=='гости_праздники']
print(gp.groupby(gp['ce'].astype(str)).agg(n=('shows','size'), мед_показов=('shows','median'),
                                           мед_дочит=('reads','median'), мед_CTR=('ctr','median')).round(4).to_string())
print()

# ---- 3. ПЛАЦЕБО: были ли вторник/четверг особыми ДО начала серии
print("--- 3. ПЛАЦЕБО: вт/чт против остальных дней ДО начала серии (до 16.09.2025) ---")
pre = m[m['date']<W0].copy()
pre['слот'] = np.where(pre['dow'].isin(['вт','чт']), 'вт/чт', 'прочие дни')
print(pre.groupby('слот').agg(n=('shows','size'), мед_показов=('shows','median'), мед_дочит=('reads','median'),
                              мед_CTR=('ctr','median')).round(4).to_string())
for ep in ['1_до_спада']:
    p2 = pre[pre['эпоха']==ep]
    print(f"\n[только эпоха {ep}]")
    print(p2.groupby('слот').agg(n=('shows','size'), мед_показов=('shows','median'), мед_дочит=('reads','median')).round(0).to_string())
print("\n[2025H1]")
p3 = pre[pre['half']=='2025H1']
print(p3.groupby('слот').agg(n=('shows','size'), мед_показов=('shows','median'), мед_дочит=('reads','median')).round(0).to_string())
print("\n[сцена стол_еда до 16.09.2025]")
p4 = pre[pre['сцена']=='стол_еда']
print(p4.groupby('слот').agg(n=('shows','size'), мед_показов=('shows','median'), мед_дочит=('reads','median')).round(0).to_string())
print()

# ---- 4. ВОЗВРАТ: что стало после окончания серии (22.05.2026 - 24.07.2026)
print("--- 4. ПОСЛЕ окончания серии (22.05.2026-24.07.2026): все ce=True ---")
post = m[m['date']>W1].copy()
print(f"n={len(post)}; ce=False среди них: {(post['ce']==False).sum()}; "
      f"даты {post['date'].min().date()}..{post['date'].max().date()}")
print(post.groupby(post['dow']).agg(n=('shows','size'), мед_показов=('shows','median'), мед_дочит=('reads','median')).to_string())
print("\nСцена стол_еда по периодам (ce отдельно):")
rows=[]
for lab, sub in [('до серии (до 16.09.25)', m[m['date']<W0]),
                 ('окно серии, ce=False', w[w['ce']==False]),
                 ('окно серии, ce=True', w[w['ce']==True]),
                 ('после серии (с 22.05.26)', post)]:
    s = sub[sub['сцена']=='стол_еда']
    rows.append(dict(период=lab, n=len(s), мед_показов=round(s['shows'].median()) if len(s) else np.nan,
                     мед_дочит=round(s['reads'].median()) if len(s) else np.nan,
                     мед_CTR=round(s['ctr'].median(),4) if len(s) else np.nan,
                     вывод=('OK' if len(s)>=10 else 'группа <10 — вывод не формулируется')))
print(pd.DataFrame(rows).to_string(index=False))
print("\nВсе статьи стол_еда после 22.05.2026:")
ps = post[post['сцена']=='стол_еда'][['date','title_studio','shows','opens','reads','ctr','ce','dow']]
print(ps.sort_values('date').to_string(index=False))
print()

# ---- 5. Частота публикаций по слотам: не заменил ли ce=False обычные вт/чт
print("--- 5. Объём публикаций по слотам, помесячно ---")
mm = m[m['date']>=pd.Timestamp('2025-01-01')].copy()
mm['слот'] = np.where(mm['ce']==False,'ce=False (вт/чт)','ce=True')
print(pd.crosstab(mm['date'].dt.to_period('M'), mm['слот']).to_string())
print()

# ---- 6. ce=True статьи с нулём комментариев (проверка смысла флага)
print("--- 6. Смысл флага: доля публикаций с comments==0 ---")
for lab, sub in [('ce=False', m[m['ce']==False]), ('ce=True (окно)', w[w['ce']==True]), ('ce=True (вся)', m[m['ce']==True])]:
    print(f"{lab:16s} n={len(sub):3d}  доля comments==0: {(sub['comments']==0).mean()*100:5.1f}%  "
          f"медиана comments: {sub['comments'].median():.0f}")
print()
print("ce=True с comments==0 (список):")
print(m[(m['ce']==True)&(m['comments']==0)][['date','title_studio','shows','opens','reads','comments_public']].to_string(index=False))
print()
print("--- Дубликаты pub_id ---")
dup = m[m['pub_id'].duplicated(keep=False)][['_xlrow','oid','pub_id','date','title_studio','shows','ce']]
print(dup.sort_values('pub_id').to_string(index=False))
print()

# ---- 7. Ступень 4 лестницы: вариант со схлопыванием по 2025H1
print("--- 7. Лестница, ступень 4: схлопывание ячеек по счётчикам 2025H1 (альтернативная трактовка) ---")
A2 = m[(m['half']=='2025H1')&(m['ce']==True)]; B2 = m[(m['half']=='2026H1')&(m['ce']==True)]
A3 = A2[A2['age_days']>=150]; B3 = B2[B2['age_days']>=150]
for base_lab,(A,B) in [('ступень 2',(A2,B2)),('ступень 3',(A3,B3))]:
    for gname, keys in [('сцена',['сцена']),('сцена x функция x порог',['сцена','функция','порог_входа'])]:
        ka = A[keys].astype(str).agg('|'.join,axis=1); kb = B[keys].astype(str).agg('|'.join,axis=1)
        cnt = ka.value_counts(); keep = set(cnt[cnt>=5].index)
        Ax = A.copy(); Bx = B.copy()
        Ax['cell2'] = ka.where(ka.isin(keep),'ПРОЧЕЕ'); Bx['cell2'] = kb.where(kb.isin(keep),'ПРОЧЕЕ')
        wB = std_weights(Bx, Ax, 'cell2')
        print(f"{base_lab:10s} {gname:24s} ячеек={len(keep)}  отношение={wmedian(Ax['reads'].values)/wmedian(Bx['reads'].values,wB):.2f}x")
print()

# ---- 8. Лестница на ДОЧИТЫВАНИЯХ с исключением сцены стол_еда (контрпример-проверка)
print("--- 8. Лестница 2025H1->2026H1 БЕЗ сцены 'стол_еда' и БЕЗ 'история_высший_свет' ---")
for lab, flt in [('все сцены', lambda d: d),
                 ('без стол_еда', lambda d: d[d['сцена']!='стол_еда']),
                 ('без стол_еда и история_высший_свет', lambda d: d[~d['сцена'].isin(['стол_еда','история_высший_свет'])])]:
    A = flt(m[m['half']=='2025H1']); B = flt(m[m['half']=='2026H1'])
    At = A[A['ce']==True]; Bt = B[B['ce']==True]
    print(f"{lab:36s} сырьё: {A['reads'].median()/B['reads'].median():6.2f}x (n {len(A)}/{len(B)})   "
          f"ce=True: {At['reads'].median()/Bt['reads'].median():6.2f}x (n {len(At)}/{len(Bt)})")
