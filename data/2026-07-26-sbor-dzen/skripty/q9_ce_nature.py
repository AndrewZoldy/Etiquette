# -*- coding: utf-8 -*-
"""Проверка: ce=False — редакционная серия или следствие низкой раздачи? (отбор по исходу?)"""
import pandas as pd, numpy as np, os
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
B = os.path.dirname(os.path.abspath(__file__))
m = pd.read_pickle(os.path.join(B, 'out', 'full.pkl'))
m['ce'] = m['comments_enabled']
m['ymS'] = m['ym'].astype(str)
f = m[m['ce'] == False]; t = m[m['ce'] == True]
W = (m['date'] >= f['date'].min()) & (m['date'] <= f['date'].max())
tw = m[W & (m['ce'] == True)]

print("=" * 120)
print("T1. ce=False НЕ отбор по исходу: в группе есть миллионники")
print("=" * 120)
print(f"   ce=False n={len(f)}: перцентили shows " +
      ", ".join(f"p{int(q*100)}={f['shows'].quantile(q):,.0f}" for q in [.1, .25, .5, .75, .9, .95, 1.0]))
print(f"   доля ce=False со shows>320k: {(f['shows']>320000).mean():.1%} ({(f['shows']>320000).sum()} шт)")
print(f"   доля ce=False со shows>1 млн: {(f['shows']>1e6).mean():.1%} ({(f['shows']>1e6).sum()} шт)")
print(f"   ce=True в том же окне n={len(tw)}: доля shows>320k {(tw['shows']>320000).mean():.1%}, доля shows<3k {(tw['shows']<3000).mean():.1%}")
print(f"   доля ce=False со shows<3k: {(f['shows']<3000).mean():.1%}")
print("\n   ВАЖНО: если бы Дзен/автор отключал комментарии ПОСЛЕ провала раздачи, миллионников в ce=False быть не могло.")

print("\n" + "=" * 120)
print("T2. ce=False — жёсткий недельный график (признак редакционной рубрики)")
print("=" * 120)
print("   dow ce=False:", f['dow'].value_counts().to_dict())
print("   dow ce=True в том же окне:", tw['dow'].value_counts().to_dict())
print("\n   Кросс-таб dow x ce внутри окна серии:")
print(pd.crosstab(m[W]['dow'], m[W]['ce'].astype(str)).to_string())
print("\n   Часы публикации: ce=False медиана", f['hour'].median(), "IQR", f['hour'].quantile([.25,.75]).tolist(),
      "| ce=True окно медиана", tw['hour'].median(), "IQR", tw['hour'].quantile([.25,.75]).tolist())
print("\n   Число публикаций серии по месяцам (регулярность):")
print(f.groupby('ymS').size().to_string())

print("\n" + "=" * 120)
print("T3. Ключевой тест на отбор по исходу: ВНУТРИ ce=False сравнить статьи «вт/чт» с остальными,")
print("    и сравнить ce=True вт/чт против ce=True в другие дни в том же окне")
print("=" * 120)
tw2 = tw.copy(); tw2['вт_чт'] = tw2['dow'].isin(['вт', 'чт'])
print(tw2.groupby('вт_чт').agg(n=('oid', 'size'), shows=('shows', 'median'), reads=('reads', 'median'),
                               ctr=('ctr', 'median')).to_string(float_format=lambda v: f'{v:,.4f}'))
print("   -> если вт/чт сам по себе не «проклят» у ce=True, то дело в самой рубрике, а не в дне.")

print("\n" + "=" * 120)
print("T4. Другие низкораздаваемые серии, которые ОСТАЛИСЬ в ce=True (чистая выборка не идеальна)")
print("=" * 120)
pat = 'Светск|вестник|Вѣстник|вѣстник|Культурн'
z = m[m['title_studio'].str.contains(pat, na=False, regex=True)]
print(f"   найдено по шаблону «{pat}»: {len(z)}")
if len(z):
    print(z[['date', 'ce', 'title_studio', 'shows', 'reads', 'сцена']].sort_values('date').to_string(index=False, float_format=lambda v: f'{v:,.0f}'))
print("\n   Статьи ce=True со shows<3000 (кто ещё «застрял» в чистой выборке):")
z2 = t[t['shows'] < 3000][['date', 'title_studio', 'shows', 'opens', 'reads', 'сцена', 'эпоха']]
print(f"   n={len(z2)}")
print(z2.sort_values('date').to_string(index=False, float_format=lambda v: f'{v:,.0f}'))

print("\n" + "=" * 120)
print("T5. Аномалии данных: read_rate>1")
print("=" * 120)
a = m[m['read_rate'] > 1][['date', 'title_studio', 'shows', 'opens', 'reads', 'read_rate', 'ce']]
print(f"   n={len(a)}")
print(a.to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
print("\n   Медиана read_rate по эпохам, ce=True:", t.groupby('эпоха')['read_rate'].median().round(4).to_dict())

print("\n" + "=" * 120)
print("T6. Что было бы, если бы серии ce=False не было: доля объёма и вклад в Факт 1")
print("=" * 120)
for w0, w1, nm in [('2025-11', '2026-06', 'дно (ноя25-июн26)'), ('2025-09', '2026-05', 'окно серии')]:
    g = m[(m['ymS'] >= w0) & (m['ymS'] <= w1)]
    print(f"   {nm}: всего {len(g)}, ce=False {(g['ce']==False).sum()} ({(g['ce']==False).mean():.1%}); "
          f"медиана reads вся смесь {g['reads'].median():,.0f} -> ce=True {g[g['ce']==True]['reads'].median():,.0f}"
          f" (сдвиг {g[g['ce']==True]['reads'].median()/max(g['reads'].median(),1):,.1f}x)")
