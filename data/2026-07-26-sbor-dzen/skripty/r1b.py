# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1 — дополнительные диагностики: чем на самом деле является множитель cpr."""
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled'] == True)

print("="*100)
print("Д1. КРИВАЯ НАБОРА КОММЕНТАРИЕВ отдельно по эпохам (только статьи с age_days>=200,")
print("    т.е. окно наблюдения не меньше 200 дней). Комментарии производятся ЧИТАТЕЛЯМИ,")
print("    поэтому их график поступления = график поступления дочитываний с точностью до cpr.")
print("="*100)
c = pd.read_pickle('out/comments_all.pkl')
c['ts_dt'] = pd.to_datetime(c['ts'], unit='ms')
info = m.set_index('oid')[['date','эпоха','age_days','reads','comments']]
c = c.join(info, on='oid')
c = c[c['date'].notna()].copy()
c['age_at'] = (c['ts_dt'] - c['date']).dt.total_seconds()/86400.0
c = c[c['age_at'] >= -0.5]
cm = c[c['age_days'] >= 200]
print(f"\nпокрытие: комментарии выгружены у {c['oid'].nunique()} статей из 623; "
      f"со зрелостью>=200д — {cm['oid'].nunique()}")
print("состав покрытых статей по эпохам:", cm.groupby('эпоха')['oid'].nunique().to_dict())
print("\nдоля комментариев, поступивших к возрасту N дней (по объединённому пулу):")
hdr = "  эпоха            n_ст " + " ".join(f"{d:>6d}д" for d in [7,14,30,45,75,110,150,200])
print(hdr)
for ep in ['1_до_спада','2_склон','3_дно','ВСЕ']:
    s = cm if ep=='ВСЕ' else cm[cm['эпоха']==ep]
    if s['oid'].nunique() < 10:
        print(f"  {ep:16s} n={s['oid'].nunique():3d} — меньше 10 статей, вывод не формулируется"); continue
    vals = " ".join(f"{(s['age_at']<=d).mean():7.3f}" for d in [7,14,30,45,75,110,150,200])
    print(f"  {ep:16s} n={s['oid'].nunique():3d} {vals}")
print("\nмедианная ПО СТАТЬЯМ доля (устойчивее к одной вирусной статье):")
print(hdr)
for ep in ['1_до_спада','2_склон','3_дно','ВСЕ']:
    s = cm if ep=='ВСЕ' else cm[cm['эпоха']==ep]
    if s['oid'].nunique() < 10: continue
    vals = " ".join(f"{s.groupby('oid')['age_at'].agg(lambda x,d=d:(x<=d).mean()).median():7.3f}"
                    for d in [7,14,30,45,75,110,150,200])
    print(f"  {ep:16s} n={s['oid'].nunique():3d} {vals}")

print("\nСЛЕДСТВИЕ: если дочитывания поступают по той же кривой, множитель недосчёта reads")
print("           для когорты возраста N = 1 / доля(N). Считаю по эпохе 3_дно:")
s3 = cm[cm['эпоха']=='3_дно']
if s3['oid'].nunique() >= 10:
    for d in [45,75,110,150,200]:
        sh = s3.groupby('oid')['age_at'].agg(lambda x,d=d:(x<=d).mean()).median()
        print(f"   возраст {d:3d}д: доля набранного {sh:.3f} -> множитель недосчёта reads ~ {1/sh:.2f}x")

print("\n"+"="*100)
print("Д2. КОНФАУНДЕР УРОВНЯ. cpr механически падает с ростом reads. Проверяю на ЗРЕЛЫХ статьях")
print("    эпохи 1 (там возрастного недосчёта заведомо нет): медиана cpr по децилям reads.")
print("="*100)
e1 = m[(m['эпоха']=='1_до_спада') & m['ce'] & (m['age_days']>550)].copy()
e1['q'] = pd.qcut(e1['reads'], 6, labels=False, duplicates='drop')
print(f"  база: эпоха 1, age>550, ce=True, n={len(e1)}")
print("  секстиль reads |  n | медиана reads | медиана cpr | медиана lpr")
for q,g in e1.groupby('q'):
    print(f"       {int(q)+1}         |{len(g):3d} | {g['reads'].median():13.0f} | {g['comments_per_read'].median():11.5f} | {g['likes_per_read'].median():.5f}")
print(f"  Спирмен reads x cpr на этой базе: {e1['reads'].corr(e1['comments_per_read'], method='spearman'):+.3f}")
print(f"  Спирмен reads x lpr на этой базе: {e1['reads'].corr(e1['likes_per_read'], method='spearman'):+.3f}")

print("\n  То же на эпохе 3_дно, ce=True, ТОЛЬКО зрелая часть age>=150 (возраст почти выровнен):")
e3 = m[(m['эпоха']=='3_дно') & m['ce'] & (m['age_days']>=150)].copy()
e3['q'] = pd.qcut(e3['reads'], 4, labels=False, duplicates='drop')
print(f"  база n={len(e3)}")
for q,g in e3.groupby('q'):
    print(f"    квартиль {int(q)+1}: n={len(g):3d} reads_med={g['reads'].median():9.0f} cpr={g['comments_per_read'].median():.5f} lpr={g['likes_per_read'].median():.5f}")
print(f"  Спирмен reads x cpr: {e3['reads'].corr(e3['comments_per_read'], method='spearman'):+.3f}")

print("\n"+"="*100)
print("Д3. СВЕРКА ГРАНИЦ ОКОН с критиком (варианты нарезки), окно 0-45 и 45-75, cpr")
print("="*100)
d3 = m[(m['эпоха']=='3_дно') & m['ce']]
for lbl, lo, hi in [('[0,45) [45,75)',0,45),('[0,46) [46,76)',0,46),('[0,44) ',0,44)]:
    a = d3[(d3['age_days']>=lo)&(d3['age_days']<hi)]
    print(f"  {lbl:16s} n={len(a):3d} cpr={a['comments_per_read'].median():.4f}")
# вариант: возраст считан на 26.07 (+1 день)
d3b = d3.copy(); d3b['age2'] = d3b['age_days']+1
for lo,hi in [(0,45),(45,75)]:
    a = d3b[(d3b['age2']>=lo)&(d3b['age2']<hi)]
    print(f"  age+1 [{lo},{hi})   n={len(a):3d} cpr={a['comments_per_read'].median():.4f}")
