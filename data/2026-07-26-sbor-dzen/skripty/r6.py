# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1, финал: множитель с эталоном, СОПОСТАВЛЕННЫМ ПО УРОВНЮ reads."""
import pandas as pd, numpy as np
pd.set_option('display.width', 260)
m = pd.read_pickle('out/full.pkl')
m['ce'] = (m['comments_enabled']==True)

print("="*118)
print("СВЕРКА ОКНА 0-45: перебор разумных вариантов нарезки")
print("="*118)
d3 = m[(m['эпоха']=='3_дно') & m['ce']]
for lab, mask in [
    ("age in [0,45)",  (d3['age_days']>=0)&(d3['age_days']<45)),
    ("age in [1,45)",  (d3['age_days']>=1)&(d3['age_days']<45)),
    ("age in (0,45]",  (d3['age_days']>0)&(d3['age_days']<=45)),
    ("age in [0,45]",  (d3['age_days']>=0)&(d3['age_days']<=45)),
    ("age in [3,45)",  (d3['age_days']>=3)&(d3['age_days']<45)),
    ("age in [7,45)",  (d3['age_days']>=7)&(d3['age_days']<45)),
]:
    s=d3[mask]; print(f"  {lab:16s} n={len(s):3d} cpr={s['comments_per_read'].median():.4f} lpr={s['likes_per_read'].median():.4f}")
print("  цель критика: cpr=0.0683")

print("\n"+"="*118)
print("ЭТАЛОН, СОПОСТАВЛЕННЫЙ ПО УРОВНЮ reads. Для каждого окна возраста эпохи 3 берём зрелые")
print("статьи эпохи 1 (age>550, ce=True) с ТЕМ ЖЕ порядком reads (тот же дециль по log reads)")
print("и считаем множитель как отношение cpr окна к cpr сопоставленного эталона.")
print("="*118)
sat = m[(m['эпоха']=='1_до_спада') & (m['age_days']>550) & m['ce']].copy()
cpr_sat_plain = sat['comments_per_read'].median()
wins=[(0,45),(45,75),(75,110),(110,150),(150,200),(200,270)]
print(f"  {'окно':9s} {'n':>4s} {'мед.reads':>10s} {'cpr набл.':>10s} {'cpr эталон':>11s} {'n эт.':>6s} {'множ. сырой':>12s} {'множ. по уровню':>16s}")
for a,b in wins:
    s = d3[(d3['age_days']>=a)&(d3['age_days']<b)]
    lo, hi = s['reads'].quantile(.25), s['reads'].quantile(.75)
    ref = sat[(sat['reads']>=lo*0.5)&(sat['reads']<=hi*2)]
    if len(ref)<10:
        ref = sat.reindex((sat['reads']-s['reads'].median()).abs().sort_values().index[:30])
    print(f"  {f'{a}-{b}':9s} {len(s):4d} {s['reads'].median():10,.0f} {s['comments_per_read'].median():10.4f}"
          f" {ref['comments_per_read'].median():11.4f} {len(ref):6d} {s['comments_per_read'].median()/cpr_sat_plain:12.2f}"
          f" {s['comments_per_read'].median()/ref['comments_per_read'].median():16.2f}".replace(',',' '))

print("\n"+"="*118)
print("СВОДКА ЧЕТЫРЁХ НЕЗАВИСИМЫХ ОЦЕНОК МНОЖИТЕЛЯ НЕДОСЧЁТА reads")
print("="*118)
curve = {45:0.822, 75:0.875, 110:0.923, 150:0.957, 200:0.994, 270:1.0}
print(f"  {'окно':9s} {'(1) по cpr':>11s} {'(2) по lpr':>11s} {'(3) по subs_per_read':>21s} {'(4) по таймстемпам':>19s}")
lpr_sat = sat['likes_per_read'].median(); spr_sat = sat['subs_per_read'].median()
for (a,b) in wins:
    s = d3[(d3['age_days']>=a)&(d3['age_days']<b)]
    k = curve[b]
    print(f"  {f'{a}-{b}':9s} {s['comments_per_read'].median()/cpr_sat_plain:11.2f}"
          f" {s['likes_per_read'].median()/lpr_sat:11.2f}"
          f" {s['subs_per_read'].median()/spr_sat:21.2f} {1/k:19.2f}")
