# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load, wmedian, wquantile, std_weights, boot_ratio, ols, dummies
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 100); pd.set_option('display.max_rows', 400)

m = load()
A_HALF, B_HALF = '2025H1', '2026H1'
NB = 4000
fm = lambda v: (f"{v:,.3f}".replace(',', ' ') if isinstance(v, float) else str(v))

print("="*110)
print("ТРЕБОВАНИЕ 1. ЛЕСТНИЦА КОНТРОЛЕЙ НА ПЕРВИЧНОЙ МЕТРИКЕ (reads), 2025H1 -> 2026H1")
print("="*110)
print("Показатель ступени = медиана(reads | 2025H1) / медиана(reads | 2026H1).")
print("Медиана — стандартная интерполированная; взвешенная версия при равных весах совпадает с ней точно.")
print("Бутстрап: 4000 ресемплов, независимая пересборка внутри каждого полугодия, веса пересчитываются")
print("в каждой реплике (неопределённость состава учтена). CI перцентильный 95%.")
print()
print("Проверка совпадения медианы с эталоном pandas:",
      round(wmedian(m[m['half']=='2025H1']['reads'].values),3),
      "vs", round(m[m['half']=='2025H1']['reads'].median(),3))
print()

# ---------------------------------------------------------------- ступени
A1 = m[m['half'] == A_HALF]; B1 = m[m['half'] == B_HALF]
A2 = A1[A1['ce'] == True];   B2 = B1[B1['ce'] == True]
A3 = A2[A2['age_days'] >= 150]; B3 = B2[B2['age_days'] >= 150]

def make_cells(A, B, keys, min_n, target='B'):
    """Схлопывание ячеек с n<min_n в целевом полугодии."""
    A = A.copy(); B = B.copy()
    ka = A[keys].astype(str).agg('|'.join, axis=1)
    kb = B[keys].astype(str).agg('|'.join, axis=1)
    cnt = (kb if target == 'B' else ka).value_counts()
    keep = set(cnt[cnt >= min_n].index)
    A['cell2'] = ka.where(ka.isin(keep), 'ПРОЧЕЕ')
    B['cell2'] = kb.where(kb.isin(keep), 'ПРОЧЕЕ')
    return A, B, len(keep)

def boot_std(A, B, direction='B_to_A', n=NB, seed=7):
    """Бутстрап отношения медиан с ПЕРЕСЧЁТОМ весов в каждой реплике."""
    rng = np.random.default_rng(seed)
    a_r = A['reads'].values.astype(float); b_r = B['reads'].values.astype(float)
    a_c = A['cell2'].values; b_c = B['cell2'].values
    na, nb = len(a_r), len(b_r)
    out = np.empty(n)
    for i in range(n):
        ia = rng.integers(0, na, na); ib = rng.integers(0, nb, nb)
        ar, ac = a_r[ia], a_c[ia]; br, bc = b_r[ib], b_c[ib]
        sa = pd.Series(ac).value_counts(normalize=True)
        sb = pd.Series(bc).value_counts(normalize=True)
        if direction == 'B_to_A':
            wb = np.array([sa.get(c, 0.0) / sb[c] for c in bc])
            out[i] = wmedian(ar) / (wmedian(br, wb) or np.nan)
        else:
            wa = np.array([sb.get(c, 0.0) / sa[c] for c in ac])
            out[i] = wmedian(ar, wa) / (wmedian(br) or np.nan)
    out = out[np.isfinite(out) & (out > 0)]
    return np.percentile(out, 2.5), np.percentile(out, 97.5)

rows = []
def add(name, A, B, wB=None, note='', seed=7, cells=None, direction=None):
    mA = wmedian(A['reads'].values)
    mB = wmedian(B['reads'].values, wB)
    if cells is None:
        lo, hi, _ = boot_ratio(A['reads'].values, B['reads'].values, None, None, n=NB, seed=seed)
    else:
        lo, hi = boot_std(A, B, direction or 'B_to_A', n=NB, seed=seed)
    rows.append(dict(ступень=name, n_25H1=len(A), n_26H1=len(B),
                     мед_reads_25H1=round(mA,1), мед_reads_26H1=round(mB,1),
                     отношение=round(mA/mB,2), CI_lo=round(lo,2), CI_hi=round(hi,2), комментарий=note))

add('1. сырьё', A1, B1, note='все статьи полугодия', seed=101)
add('2. + comments_enabled==True', A2, B2, note='убрана серия ce=False', seed=102)
add('3. + ценз зрелости age_days>=150', A3, B3, note='2026H1 сжато до 01.01-26.02.2026', seed=103)

A4, B4, nk4 = make_cells(A3, B3, ['сцена','функция','порог_входа'], 5, 'B')
w4 = std_weights(B4, A4, 'cell2')
add(f'4. + станд. состава (сцена x функция x порог)', A4, B4, w4,
    note=f'ячеек с n>=5 в 2026H1: {nk4} -> сетка ВЫРОЖДЕНА', seed=104, cells=True)

res = pd.DataFrame(rows)
print("--- ЛЕСТНИЦА КАК ЗАПРОШЕНА КРИТИКОМ ---")
print(res.to_string(index=False))
print()

print("!!! КЛЮЧЕВАЯ ПРОБЛЕМА СТУПЕНИ 3->4:")
print(f"    age_days>=150 при дате отсечки 25.07.2026 = публикации не позже 26.02.2026.")
print(f"    2026H1 ce=True: было 108 статей, осталось {len(B3)} (даты {B3['date'].min().date()}..{B3['date'].max().date()}).")
print(f"    2025H1 ce=True: {len(A3)} из {len(A2)} (возраст {A3['age_days'].min():.0f}-{A3['age_days'].max():.0f} дн.).")
print("    Ценз не выравнивает зрелость (400-570 дн. против 150-205 дн.), а вырезает")
print("    из 2026H1 календарный кусок январь-февраль — самое дно ряда. Это не нейтральный контроль.")
print(f"    На {len(B3)} наблюдениях НИ ОДНА ячейка (сцена x функция x порог) не набирает n>=5,")
print("    поэтому ступень 4 в буквальной формулировке критика тождественна ступени 3.")
print()

# ---- ячейки после ступени 2 (без ценза) — там стандартизация возможна
print("--- Стандартизация состава ТАМ, ГДЕ ОНА ВОЗМОЖНА (ступень 2, без ценза зрелости) ---")
A4b, B4b, nkb = make_cells(A2, B2, ['сцена','функция','порог_входа'], 5, 'B')
w4b = std_weights(B4b, A4b, 'cell2')
tab = pd.DataFrame({'n_25H1': A4b['cell2'].value_counts(), 'n_26H1': B4b['cell2'].value_counts()}).fillna(0).astype(int)
tab['доля_25H1'] = (tab['n_25H1']/tab['n_25H1'].sum()).round(4)
tab['доля_26H1'] = (tab['n_26H1']/tab['n_26H1'].sum()).round(4)
tab['вес_на_26H1'] = (tab['доля_25H1']/tab['доля_26H1'].replace(0,np.nan)).round(3)
tab['мед_reads_25H1'] = A4b.groupby('cell2')['reads'].median()
tab['мед_reads_26H1'] = B4b.groupby('cell2')['reads'].median()
print(tab.sort_values('доля_25H1', ascending=False).to_string())
print(f"\nЯчеек с n>=5 в 2026H1: {nkb}. Доля массы 2026H1 вне 'ПРОЧЕЕ': "
      f"{(B4b['cell2']!='ПРОЧЕЕ').mean():.3f}; в 2025H1: {(A4b['cell2']!='ПРОЧЕЕ').mean():.3f}")
print()

# ---------------------------------------------------------------- варианты ступени 4
print("--- ВАРИАНТЫ СТУПЕНИ 4 (разные сетки ячеек, разные базы) ---")
variants = []
grids = [
    ('сцена', ['сцена']),
    ('сцена x порог', ['сцена','порог_входа']),
    ('функция x порог', ['функция','порог_входа']),
    ('сцена x функция x порог', ['сцена','функция','порог_входа']),
]
for base_name, (Ab, Bb) in [('ступень 2 (ce=True)', (A2,B2)), ('ступень 3 (ce=True, age>=150)', (A3,B3))]:
    for gname, keys in grids:
        Ax, Bx, nk = make_cells(Ab, Bb, keys, 5, 'B')
        wx = std_weights(Bx, Ax, 'cell2')
        mA = wmedian(Ax['reads'].values); mB = wmedian(Bx['reads'].values, wx)
        lo, hi = boot_std(Ax, Bx, 'B_to_A', n=NB, seed=hash(gname) % 1000 + 5)
        cov = (Bx['cell2'] != 'ПРОЧЕЕ').mean()
        variants.append(dict(база=base_name, сетка=gname, ячеек=nk, n_25H1=len(Ax), n_26H1=len(Bx),
                             доля_вне_ПРОЧЕЕ=round(cov,3),
                             взв_мед_26H1=round(mB,1), отношение=round(mA/mB,2),
                             CI_lo=round(lo,2), CI_hi=round(hi,2)))
print(pd.DataFrame(variants).to_string(index=False))
print()

# ---------------------------------------------------------------- Оахака в обратную сторону
print("--- СИММЕТРИЧНАЯ ПРОВЕРКА ОАХАКИ: 2025H1 перевзвешен к составу 2026H1 ---")
oax = []
for base_name, (Ab, Bb) in [('ступень 2 (ce=True)', (A2,B2)), ('ступень 3 (ce=True, age>=150)', (A3,B3))]:
    for gname, keys in grids:
        Ax, Bx, nk = make_cells(Ab, Bb, keys, 5, 'A')   # схлопывание по целевому = 2025H1
        wx = std_weights(Ax, Bx, 'cell2')
        mA = wmedian(Ax['reads'].values, wx); mB = wmedian(Bx['reads'].values)
        lo, hi = boot_std(Ax, Bx, 'A_to_B', n=NB, seed=hash(gname) % 997 + 3)
        oax.append(dict(база=base_name, сетка=gname, ячеек=nk, n_25H1=len(Ax), n_26H1=len(Bx),
                        взв_мед_25H1=round(mA,1), сыр_мед_26H1=round(mB,1),
                        отношение=round(mA/mB,2), CI_lo=round(lo,2), CI_hi=round(hi,2)))
print(pd.DataFrame(oax).to_string(index=False))
print()

# ---------------------------------------------------------------- диагностика хвостов
print("--- Диагностика: квантили reads по полугодиям (ce=True и всё) ---")
q = [0.1,0.25,0.4,0.5,0.6,0.75,0.9]
for lab, sub in [('все', m), ('ce=True', m[m['ce']==True])]:
    g = sub.groupby('half')['reads'].quantile(q).unstack()
    g.insert(0, 'n', sub.groupby('half').size())
    print(f"[{lab}]"); print(g.round(0).to_string()); print()

# ---------------------------------------------------------------- регрессии
print("="*110)
print("РЕГРЕССИИ log10(reads+1) ~ post + контроли  (МНК, SE по HC1)")
print("="*110)

def regtable(d, postcol='post', label=''):
    d = d.copy()
    d['y'] = np.log10(d['reads'] + 1)
    d['logage'] = np.log10(d['age_days'] + 1)
    specs = [('(1) post',[],None), ('(2) +ceF',['ceF'],None),
             ('(3) +log10(age)',['ceF','logage'],None),
             ('(4) +сцена+функция+порог',['ceF','logage'],['сцена','функция','порог_входа'])]
    out=[]
    for tag, ex, cats in specs:
        X = pd.DataFrame({'const':1.0,'post':d[postcol].astype(float)}, index=d.index)
        for c in ex: X[c]=d[c].astype(float)
        if cats:
            for c in cats: X = pd.concat([X, dummies(d,c)], axis=1)
        b,se,sh,r2,n = ols(d['y'].values, X.values, list(X.columns))
        out.append(dict(модель=tag, n=n, b_post=round(b['post'],4), se_hc1=round(sh['post'],4),
                        кратн_post=round(10**(-b['post']),2),
                        b_ceF=(round(b['ceF'],4) if 'ceF' in b else np.nan),
                        кратн_ceF=(round(10**(-b['ceF']),1) if 'ceF' in b else np.nan),
                        R2=round(r2,4)))
    df = pd.DataFrame(out); print(f"[{label}]"); print(df.to_string(index=False)); print()
    return df

d_all = m[m['ce'].notna()].copy()
regtable(d_all, 'post', f'A. Вся выборка статей, post = дата>=2025-11-01 (n={len(d_all)})')

d_2526 = m[m['half'].isin([A_HALF,B_HALF]) & m['ce'].notna()].copy()
d_2526['post'] = (d_2526['half']==B_HALF).astype(int)
regtable(d_2526, 'post', f'B. Только 2025H1+2026H1, post=2026H1 (n={len(d_2526)})')

d_25p = m[(m['date']>=pd.Timestamp('2025-01-01')) & m['ce'].notna()].copy()
regtable(d_25p, 'post', f'C. Статьи с 01.01.2025, post = дата>=2025-11-01 (n={len(d_25p)})')

d_24p = m[(m['date']>=pd.Timestamp('2024-07-01')) & m['ce'].notna()].copy()
regtable(d_24p, 'post', f'D. Статьи с 01.07.2024, post = дата>=2025-11-01 (n={len(d_24p)})')

d_ex = m[m['ce'].notna() & (m['эпоха']!='2_склон')].copy()
regtable(d_ex, 'post', f'E. Без эпохи «склон», post = дата>=2025-11-01 (n={len(d_ex)})')
