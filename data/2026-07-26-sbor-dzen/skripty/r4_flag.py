# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = load()

W0, W1 = pd.Timestamp('2025-09-16'), pd.Timestamp('2026-05-21 23:59:59')
w = m[(m['date']>=W0)&(m['date']<=W1)].copy()
f = w[w['ce']==False].copy(); t = w[w['ce']==True].copy()

print("="*110)
print("ТРЕБОВАНИЕ 4. ПРИЧИННОСТЬ ФЛАГА comments_enabled (законно ли делить выборку)")
print("="*110)
print(f"Окно 16.09.2025-21.05.2026: всего статей {len(w)}; ce=False {len(f)}; ce=True {len(t)}; ce=NaN {w['ce'].isna().sum()}")
print(f"Вся серия ce=False по датасету: {(m['ce']==False).sum()} — вся внутри окна: {(m['ce']==False).sum()==len(f)}")
print()

# ---------- (а) расписание
print("--- (а1) День недели ---")
dw = pd.crosstab(w['dow'], w['ce'].astype(str))
order = ['пн','вт','ср','чт','пт','сб','вс']
dw = dw.reindex([d for d in order if d in dw.index])
dw['доля_ce=False_в_дне,%'] = (dw.get('False',0)/dw.sum(axis=1)*100).round(1)
print(dw.to_string())
print()
print("Хи-квадрат независимости день-недели x ce (окно):")
obs = pd.crosstab(w['dow'], w['ce'].astype(str)).values
exp = obs.sum(1)[:,None]*obs.sum(0)[None,:]/obs.sum()
chi2 = ((obs-exp)**2/np.maximum(exp,1e-9)).sum()
print(f"  chi2={chi2:.1f}, df={(obs.shape[0]-1)*(obs.shape[1]-1)}  (критич. 0,1% для df=6 ~ 22,5)")
print()

print("--- (а2) Интервалы между СОСЕДНИМИ публикациями серии ce=False (дни) ---")
fs = f.sort_values('date')
iv = fs['date'].diff().dt.total_seconds()/86400
print(iv.dropna().round(1).value_counts().sort_index().to_string())
print(f"\nмедиана интервала {iv.median():.2f} дн.; доля интервалов в [1,5;2,5] или [4,5;5,5]: "
      f"{(((iv>=1.5)&(iv<=2.5))|((iv>=4.5)&(iv<=5.5))).mean()*100:.1f}%")
print()
print("--- (а3) Пропуски расписания: недели окна без пары вт+чт ---")
fs['week'] = fs['date'].dt.to_period('W')
wk = fs.groupby('week').size()
print(f"недель с серией: {len(wk)}; из них по 2 статьи: {(wk==2).sum()}, по 1: {(wk==1).sum()}, по 3+: {(wk>=3).sum()}")
allw = pd.period_range(fs['date'].min().to_period('W'), fs['date'].max().to_period('W'), freq='W')
print(f"всего недель в окне серии: {len(allw)}; недель БЕЗ серии: {len(set(allw)-set(wk.index))}")
print()
print("--- (а4) Часы публикации ---")
print(pd.DataFrame({'ce=False': f['hour'].describe(), 'ce=True(окно)': t['hour'].describe()}).round(2).to_string())
print(f"медиана часа: ce=False {f['hour'].median()}, ce=True(окно) {t['hour'].median()}, ce=True(вся) {m[m['ce']==True]['hour'].median()}")
print()
print("--- (а5) Кто ещё выходит по вт/чт в окне (ce=True) ---")
print(pd.crosstab(w['dow'], w['ce'].astype(str), normalize='columns').round(3).reindex([d for d in order if d in dw.index]).to_string())
print()

# ---------- (б) хвосты исхода
print("--- (б) Доля ce=False в хвостах исхода ВНУТРИ ОКНА ---")
rows=[]
for lab, sub in [('shows>1 000 000', w[w['shows']>1_000_000]),
                 ('shows>500 000',   w[w['shows']>500_000]),
                 ('shows<10 000',    w[w['shows']<10_000]),
                 ('shows<3 000',     w[w['shows']<3_000]),
                 ('всё окно',        w)]:
    rows.append(dict(группа=lab, n=len(sub), n_ceFalse=int((sub['ce']==False).sum()),
                     доля_ceFalse=round((sub['ce']==False).mean()*100,1)))
print(pd.DataFrame(rows).to_string(index=False))
print()
print("Внутри серии ce=False — оба хвоста присутствуют?")
print(f"  n>1 000 000 показов: {(f['shows']>1e6).sum()} шт.  |  n>500 000: {(f['shows']>5e5).sum()} шт.")
print(f"  n<10 000: {(f['shows']<1e4).sum()} шт.  |  медиана серии: {f['shows'].median():,.0f}".replace(',',' '))
print("  Верхний хвост серии:")
print(f.nlargest(6,'shows')[['date','title_studio','shows','reads','ctr','comments']].to_string(index=False))
print()

# ---------- (в) четыре ce=False с comments>0
print("--- (в) Наблюдения ce=False с comments>0 и проверка склейки ---")
z = m[(m['ce']==False)&(m['comments']>0)]
print(z[['_xlrow','oid','pub_id','date','title_studio','shows','opens','reads','comments','comments_public',
         'likes','likes_public','views_public','subs']].to_string(index=False))
print()
print("Соседние строки выгрузки вокруг _xlrow 403 и 405 (проверка сдвига склейки):")
nb = m[m['_xlrow'].between(399,409)][['_xlrow','date','title_studio','shows','opens','reads','comments','comments_public',
                                      'likes','likes_public','views_public','ce']]
print(nb.to_string(index=False))
print()
print("Проверка соответствия Студия<->публичная карточка на этих строках:")
zz = m[m['_xlrow'].between(399,409)].copy()
zz['opens_vs_views'] = (zz['views_public']-zz['opens'])
zz['likes_diff'] = (zz['likes_public']-zz['likes'])
zz['comments_diff'] = (zz['comments_public']-zz['comments'])
print(zz[['_xlrow','title_studio','opens','views_public','opens_vs_views','likes','likes_public','likes_diff',
          'comments','comments_public','comments_diff']].to_string(index=False))
print()
print("Сколько всего статей с |views_public - opens| <= 500 (значит склейка верная построчно):",
      (m['views_public'].sub(m['opens']).abs()<=500).sum(), "из", m['views_public'].notna().sum())
print("Сколько статей с comments==380 во всей выборке:", (m['comments']==380).sum())
print(m[m['comments']==380][['_xlrow','date','title_studio','shows','opens','comments','comments_public','ce']].to_string(index=False))
print()
print("Дубликаты oid / pub_id:", m['oid'].duplicated().sum(), "/", m['pub_id'].duplicated().sum())
print()
print("Все ce=False с comments_public>0:")
print(m[(m['ce']==False)&(m['comments_public'].fillna(0)>0)][['date','title_studio','comments','comments_public']].to_string(index=False))
print(f"Из 70 статей серии comments_public==0 или NaN у {((m['ce']==False)&(m['comments_public'].fillna(0)==0)).sum()}")
print()

# ---------- (г) структурные отличия
print("--- (г) Прочие структурные отличия класса ce=False (в окне) ---")
for col in ['type','item_type','src','cover_tpl','suites','publisher_id','has_caption','серийная_рубрика']:
    if col not in m.columns: continue
    if col == 'cover_tpl':
        a = f[col].isna().sum(); b = t[col].isna().sum()
        print(f"[{col}] пропусков: ce=False {a}/{len(f)}, ce=True {b}/{len(t)}; уникальных значений (не NaN): "
              f"{f[col].nunique()} / {t[col].nunique()} — шаблон уникален у каждой публикации, различий класса нет")
        continue
    va = f[col].astype(str).value_counts(dropna=False)
    vb = t[col].astype(str).value_counts(dropna=False)
    print(f"[{col}] ce=False: {dict(va)}   ||   ce=True(окно): {dict(vb.head(5))}")
print()
print("--- Числовые/контентные отличия класса (медианы, окно) ---")
rows=[]
for c in ['n_words','n_chars','n_paragraphs','n_images','n_headers','n_links','n_quotes','n_list_items',
          'time_to_read_s','brightness','saturation','contrast','warm','aspect','read_rate','ctr','age_days','hour']:
    a,b = f[c].median(), t[c].median()
    rows.append(dict(признак=c, ce_False=round(a,4) if pd.notna(a) else np.nan,
                     ce_True_окно=round(b,4) if pd.notna(b) else np.nan))
print(pd.DataFrame(rows).to_string(index=False))
print()
print("--- publishTime vs modificationTime (признак пост-фактум правки) ---")
for lab, sub in [('ce=False', f), ('ce=True окно', t)]:
    d = (sub['modificationTime']-sub['publishTime'])/1000/86400
    print(f"{lab}: n={d.notna().sum()}, медиана разницы {d.median():.2f} дн., доля с разницей >1 дн. "
          f"{(d>1).mean()*100:.1f}%, макс {d.max():.1f} дн.")
print()
print("--- Заголовки серии по месяцам (проверка на тематический сериал) ---")
fs2 = f.sort_values('date')
print(fs2.groupby([fs2['date'].dt.to_period('M'), fs2['сцена']]).size().to_string())
