# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 3 — окончание: скос, суммы за всю историю, нормировка на базу подписчиков."""
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['ymS'] = m['ym'].astype(str)
base = m[m['ce']]

print("="*118)
print("СКОС mean/median по reads, ce=True (проверка утверждения критика: 23,96 против 7,74)")
print("="*118)
for h in ['2023H1','2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']:
    w = base[base['half']==h]
    if len(w)<10: print(f"  {h}: n={len(w)} — меньше 10, вывод не формулируется"); continue
    print(f"  {h} ce=True n={len(w):3d}: mean={w['reads'].mean():>10,.0f} median={w['reads'].median():>8,.0f} skew={w['reads'].mean()/w['reads'].median():6.2f}".replace(',',' '))
w = base[(base['half']=='2026H1')&(base['age_days']>=110)]
print(f"  2026H1 ЦЕНЗ  n={len(w):3d}: mean={w['reads'].mean():>10,.0f} median={w['reads'].median():>8,.0f} skew={w['reads'].mean()/w['reads'].median():6.2f}".replace(',',' '))
w = m[m['half']=='2026H1']
print(f"  2026H1 ВСЕ   n={len(w):3d}: mean={w['reads'].mean():>10,.0f} median={w['reads'].median():>8,.0f} skew={w['reads'].mean()/w['reads'].median():6.2f}".replace(',',' '))

print("\n"+"="*118)
print("МЕСЯЧНЫЕ СУММЫ ДОЧИТЫВАНИЙ ЗА ВСЮ ИСТОРИЮ (шкала «б», вся выборка статей)")
print("="*118)
g = m.groupby('ymS').agg(n=('reads','size'), sum_reads=('reads','sum'), sum_shows=('shows','sum'))
g['млн_reads']=g['sum_reads']/1e6; g['млн_shows']=g['sum_shows']/1e6
print(g[['n','млн_reads','млн_shows']].to_string(float_format=lambda v: f"{v:,.3f}".replace(',',' ')))
def blk(a,b,label):
    s = g.loc[(g.index>=a)&(g.index<=b),'млн_reads']
    print(f"   {label:24s} ({a}..{b}) мес={len(s):2d}  медиана={s.median():.3f} млн  диапазон {s.min():.3f}-{s.max():.3f}")
    return s.median()
print("\n  Медианы месячных СУММ дочитываний по блокам:")
b1=blk('2023-07','2023-12','2023H2'); b2=blk('2024-01','2024-06','2024H1')
b3=blk('2024-07','2024-12','2024H2'); b4=blk('2025-01','2025-07','пик 2025 янв-июл')
b5=blk('2025-12','2026-06','плато дек25-июн26')
print(f"\n   пик/плато по СУММАМ: x{b4/b5:.2f}   2024H1/плато: x{b2/b5:.2f}   2023H2/плато: x{b1/b5:.2f}   2024H2/плато: x{b3/b5:.2f}")

print("\n"+"="*118)
print("КОНТРОЛЬ РАЗМЕРА КАНАЛА. Оценка базы подписчиков нарастающим итогом (сумма subs по ВСЕМ")
print("публикациям канала: статьи+ролики+посты). Сравнение окон без этого контроля некорректно.")
print("="*118)
parts=[]
for f,lab in [('out/art.pkl','статьи'),('out/rol.pkl','ролики'),('out/pos.pkl','посты')]:
    d = pd.read_pickle(f)
    if 'subs' in d.columns and 'date' in d.columns:
        parts.append(d[['date','subs']].assign(тип=lab))
    else:
        print(f"   {lab}: колонок date/subs нет ({list(d.columns)[:12]})")
allp = pd.concat(parts, ignore_index=True)
allp['ymS'] = allp['date'].dt.to_period('M').astype(str)
mo = allp.groupby('ymS')['subs'].sum().sort_index()
cum = mo.cumsum()
print(f"\n  суммарно подписок за всё время по выгрузке: {mo.sum():,.0f}; факт на июль 2026: 88 465".replace(',',' '))
scale = 88465/cum.iloc[-1]
print(f"  масштабирую нарастающий итог на фактические 88 465 (коэф. {scale:.3f}); стартовая база до 03.2023 не наблюдается")
tab = pd.DataFrame({'подписок_за_мес':mo, 'база_на_конец':cum*scale})
print(tab.loc['2023-07':].to_string(float_format=lambda v: f"{v:,.0f}".replace(',',' ')))
def basemid(a,b):
    s = tab.loc[(tab.index>=a)&(tab.index<=b),'база_на_конец']
    return s.median()
wins = [('2023H2','2023-07','2023-12'),('2024H1','2024-01','2024-06'),('2024H2','2024-07','2024-12'),
        ('2025H1','2025-01','2025-06'),('2026H1','2026-01','2026-06')]
print("\n  Медиана показов на 1000 подписчиков базы (ce=True):")
print(f"  {'окно':8s} {'n':>4s} {'база':>9s} {'мед.shows':>11s} {'shows/1000подп':>15s} {'мед.reads':>10s} {'reads/1000подп':>15s}")
ref=None
for h,a,b in wins:
    w = base[base['half']==h]; bs = basemid(a,b)
    r1 = w['shows'].median()/bs*1000; r2 = w['reads'].median()/bs*1000
    print(f"  {h:8s} {len(w):4d} {bs:9,.0f} {w['shows'].median():11,.0f} {r1:15,.0f} {w['reads'].median():10,.0f} {r2:15,.1f}".replace(',',' '))
