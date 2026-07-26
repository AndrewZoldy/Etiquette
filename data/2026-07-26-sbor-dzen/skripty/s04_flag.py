# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 4: законность деления по comments_enabled."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 200)
pd.set_option('display.max_rows', 400)

m = load()

print("="*100)
print("ТРЕБОВАНИЕ 4. Проверка причинности флага comments_enabled")
print("="*100)

f = m[m['ceF']].sort_values('date')
print(f"\nВсего ce=False: {len(f)}   ce=True: {m['ceT'].sum()}   NaN: {m['ce'].isna().sum()}")
print(f"Окно ce=False фактическое: {f['date'].min()}  ...  {f['date'].max()}")

W0, W1 = pd.Timestamp('2025-09-16'), pd.Timestamp('2025-05-21')
W1 = pd.Timestamp('2026-05-21 23:59:59')
win = m[(m['date'] >= W0) & (m['date'] <= W1)].copy()
print(f"\nОкно критика 16.09.2025-21.05.2026: всего статей {len(win)}, из них ce=False {win['ceF'].sum()}, ce=True {win['ceT'].sum()}, NaN {win['ce'].isna().sum()}")
print(f"Все 70 ce=False попадают в окно? {int(f['date'].between(W0,W1).sum())} из {len(f)}")

# ---------- (а) день недели ----------
print("\n" + "-"*100)
print("(а1) ce=False по дням недели (фактический день публикации)")
print("-"*100)
order = ['пн','вт','ср','чт','пт','сб','вс']
tab = pd.crosstab(m.loc[m['date'].between(W0,W1),'dow'], m.loc[m['date'].between(W0,W1),'ce'].astype(str))
tab = tab.reindex(order).fillna(0).astype(int)
tab['всего'] = tab.sum(axis=1)
tab['доля ce=False'] = (tab.get('False',0)/tab['всего']*100).round(1)
print(tab)

print("\nПроверка цифр критика (34 вторника, 35 четвергов, 1 понедельник):")
print(f.groupby('dow', observed=True).size().reindex(order).fillna(0).astype(int))

print("\n(а2) Интервалы между последовательными публикациями ce=False (в днях, по календарной дате)")
d = f['date'].dt.normalize()
gaps = d.diff().dt.days.dropna().astype(int)
print(gaps.value_counts().sort_index().to_string())
print(f"медиана интервала = {gaps.median()}, доля интервалов ровно 2 или 5 дней = "
      f"{(gaps.isin([2,5]).sum()/len(gaps)*100):.1f}% ({gaps.isin([2,5]).sum()}/{len(gaps)})")

print("\n(а3) Полный список ce=False: дата, день недели, час, показы, дочит., комменты, сцена")
show = f[['date','dow','hour','shows','opens','reads','comments','comments_public','сцена','функция','порог_входа','title_studio']].copy()
show['date'] = show['date'].dt.strftime('%Y-%m-%d')
show['title_studio'] = show['title_studio'].str.slice(0,42)
print(show.to_string(index=False))

# непрерывность серии: сколько вторников/четвергов в окне НЕ покрыты серией
print("\n(а4) Покрытие расписания: вторники и четверги в окне серии (первая-последняя дата ce=False)")
s0, s1 = d.min(), d.max()
all_days = pd.date_range(s0, s1, freq='D')
tue_thu = all_days[all_days.dayofweek.isin([1,3])]
covered = set(d.unique())
miss = [x for x in tue_thu if x not in covered]
print(f"Диапазон серии {s0.date()}..{s1.date()}: вторников+четвергов всего {len(tue_thu)}, покрыто серией {len(tue_thu)-len(miss)}, пропущено {len(miss)}")
print("Пропущенные (первые 30):", [str(x.date()) for x in miss[:30]])
# сколько ce=True статей вышло по вторникам/четвергам в том же диапазоне
tt = m[(m['date'].dt.normalize().isin(tue_thu)) & m['ceT']]
print(f"ce=True статей по вт/чт в этом же диапазоне: {len(tt)}")

# ---------- (б) хвосты исхода ----------
print("\n" + "-"*100)
print("(б) Доля ce=False в хвостах исхода ВНУТРИ окна 16.09.2025-21.05.2026")
print("-"*100)
for lbl, sub in [('shows > 1 000 000', win[win['shows'] > 1_000_000]),
                 ('shows 100k-1M',     win[(win['shows'] >= 100_000) & (win['shows'] <= 1_000_000)]),
                 ('shows 10k-100k',    win[(win['shows'] >= 10_000) & (win['shows'] < 100_000)]),
                 ('shows < 10 000',    win[win['shows'] < 10_000]),
                 ('shows < 3 000',     win[win['shows'] < 3_000])]:
    n = len(sub); nf = int(sub['ceF'].sum())
    print(f"{lbl:22s} n={n:4d}  ce=False={nf:3d}  доля={nf/n*100 if n else float('nan'):5.1f}%")

print("\nХвосты внутри самой серии ce=False:")
print(f"  медиана shows серии = {f['shows'].median():,.0f}")
print(f"  max/топ-6 shows серии:")
top = f.nlargest(6,'shows')[['date','shows','reads','ctr','comments','title_studio']].copy()
top['date']=top['date'].dt.strftime('%Y-%m-%d'); top['title_studio']=top['title_studio'].str.slice(0,45)
print(top.to_string(index=False))
print(f"  статей серии с shows>1M: {int((f['shows']>1_000_000).sum())}; >500k: {int((f['shows']>500_000).sum())}; >100k: {int((f['shows']>100_000).sum())}")
print(f"  статей серии с shows<10k: {int((f['shows']<10_000).sum())} ({(f['shows']<10_000).mean()*100:.1f}%)")
print(f"  перцентили shows серии: p10={f['shows'].quantile(.10):,.0f} p50={f['shows'].median():,.0f} p90={f['shows'].quantile(.90):,.0f} max={f['shows'].max():,.0f}")

# ---------- (в) четыре ce=False с comments>0 ----------
print("\n" + "-"*100)
print("(в) Наблюдения ce=False с comments>0 — проверка склейки")
print("-"*100)
anom = f[(f['comments'] > 0) | (f['comments_public'] > 0)]
cols = ['_xlrow','oid','pub_id','date','title_studio','shows','opens','reads','likes','comments','comments_public','likes_public','views_public','minutes','subs']
aa = anom[cols].copy(); aa['date']=aa['date'].dt.strftime('%Y-%m-%d %H:%M'); aa['title_studio']=aa['title_studio'].str.slice(0,40)
print(aa.to_string(index=False))
print(f"\nВсего ce=False с comments>0: {len(anom)}")
print("Уникальность oid во всей таблице:", m['oid'].is_unique, " уникальность _xlrow:", m['_xlrow'].is_unique, " уникальность pub_id:", m['pub_id'].dropna().is_unique)
# ищем дубли значений comments=380 по ВСЕЙ выборке
print("\nВсе статьи выборки с comments==380:")
d380 = m[m['comments']==380][['_xlrow','oid','date','title_studio','shows','opens','reads','likes','comments','comments_public','ce']].copy()
d380['date']=d380['date'].dt.strftime('%Y-%m-%d'); d380['title_studio']=d380['title_studio'].str.slice(0,40)
print(d380.to_string(index=False))
print("\nСовпадают ли у этих двух прочие метрики (признак склейки)?")
if len(d380)>=2:
    sub=d380.drop(columns=['_xlrow','oid','date','title_studio'])
    print(sub.to_string(index=False))
    print("Полностью идентичные строки по shows/opens/reads:", d380.duplicated(subset=['shows','opens','reads']).sum())
# сколько дубликатов значения comments в целом (базовая частота совпадений)
vc = m['comments'].value_counts()
print(f"\nБазовая частота повторов значения comments по всей выборке: значений с >=2 статьями: {(vc>=2).sum()} из {len(vc)} уникальных")
print("Топ повторов:", vc[vc>=2].head(8).to_dict())

# ---------- (г) структурные отличия ----------
print("\n" + "-"*100)
print("(г) Структурные отличия класса ce=False (сравнение с ce=True ВНУТРИ окна)")
print("-"*100)
wt = win[win['ceT']]
print(f"n(ce=False)={len(win[win['ceF']])}, n(ce=True в окне)={len(wt)}")
for c in ['type','item_type','src','cover_tpl']:
    a = win.loc[win['ceF'], c].astype(str).nunique(); b = wt[c].astype(str).nunique()
    print(f"  {c:12s}: ce=False уник.знач.={a}, ce=True уник.знач.={b}, "
          f"значения ce=False: {list(win.loc[win['ceF'],c].astype(str).value_counts().head(3).index)[:3] if c!='cover_tpl' else '(уникальны у каждой)'}")
print("  suites: ce=False", win.loc[win['ceF'],'suites'].astype(str).value_counts().to_dict(),
      "| ce=True", wt['suites'].astype(str).value_counts().to_dict())

print("\nЧас публикации:")
print(f"  ce=False: медиана {win.loc[win['ceF'],'hour'].median():.0f}, распределение {win.loc[win['ceF'],'hour'].value_counts().sort_index().to_dict()}")
print(f"  ce=True : медиана {wt['hour'].median():.0f}, распределение {wt['hour'].value_counts().sort_index().to_dict()}")

print("\nСцены (доля внутри класса, %):")
sc = pd.DataFrame({'ce=False': win.loc[win['ceF'],'сцена'].value_counts(normalize=True)*100,
                   'ce=True':  wt['сцена'].value_counts(normalize=True)*100}).fillna(0).round(1)
sc['разница п.п.'] = (sc['ce=False']-sc['ce=True']).round(1)
print(sc.sort_values('разница п.п.', ascending=False))

print("\nФункция / порог входа (доля внутри класса, %):")
for c in ['функция','порог_входа','серийная_рубрика','уверенность_разметки']:
    t = pd.DataFrame({'ce=False': win.loc[win['ceF'],c].astype(str).value_counts(normalize=True)*100,
                      'ce=True':  wt[c].astype(str).value_counts(normalize=True)*100}).fillna(0).round(1)
    print(f"\n[{c}]"); print(t)

print("\nМедианы структурных характеристик текста:")
rows=[]
for c in ['n_words','n_paragraphs','n_links','n_images','n_headers','n_quotes','n_list_items','time_to_read_s','age_days','ctr','read_rate']:
    rows.append({'признак':c,
                 'ce=False': round(float(win.loc[win['ceF'],c].median()),4),
                 'ce=True(окно)': round(float(wt[c].median()),4)})
print(pd.DataFrame(rows).to_string(index=False))

# временнáя структура: были ли ce=False до 16.09.2025 вообще
print("\nПервая/последняя ce=False по месяцам:")
print(f.groupby(f['date'].dt.to_period('M')).size().to_string())
print("\nВсего статей по месяцам в том же диапазоне (для сравнения):")
print(m[m['date'].between(f['date'].min().normalize(), f['date'].max())].groupby(lambda i: m.loc[i,'date'].to_period('M')).size().to_string())
