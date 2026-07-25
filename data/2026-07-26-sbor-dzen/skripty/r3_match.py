# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from lib import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = load()
rng = np.random.default_rng(3)

print("="*110)
print("ТРЕБОВАНИЕ 3. МАТЧИНГ СЕРИИ ce=False С КОНТРОЛЕМ ce=True")
print("="*110)
trt = m[m['ce']==False].copy()
pool = m[m['ce']==True].copy()
print(f"Серия ce=False: n={len(trt)}, даты {trt['date'].min().date()}..{trt['date'].max().date()}")
print(f"Пул контроля ce=True: n={len(pool)}")
print("Правило: тот же канал, точное совпадение (сцена, функция, порог_входа), |Δдата| <= 45 дней,")
print("до 3 ближайших по дате контролей на каждую статью серии.")
print()

pairs = []          # строки: treated + один контроль
matched_t = []      # treated с >=1 контролем
unmatched = []
for _, r in trt.iterrows():
    c = pool[(pool['сцена']==r['сцена']) & (pool['функция']==r['функция']) &
             (pool['порог_входа']==r['порог_входа'])].copy()
    c['dd'] = (c['date']-r['date']).dt.total_seconds().abs()/86400
    c = c[c['dd']<=45].nsmallest(3,'dd')
    if len(c)==0:
        unmatched.append(r); continue
    matched_t.append(dict(oid=r['oid'], date=r['date'], title=r['title_studio'], сцена=r['сцена'],
                          функция=r['функция'], порог=r['порог_входа'],
                          shows=r['shows'], opens=r['opens'], reads=r['reads'], ctr=r['ctr'],
                          n_words=r['n_words'], n_paragraphs=r['n_paragraphs'], n_links=r['n_links'],
                          ttr=r['time_to_read_s'], n_ctrl=len(c),
                          c_shows=c['shows'].median(), c_opens=c['opens'].median(),
                          c_reads=c['reads'].median(), c_ctr=c['ctr'].median(),
                          c_words=c['n_words'].median(), c_par=c['n_paragraphs'].median(),
                          c_links=c['n_links'].median(), c_ttr=c['time_to_read_s'].median(),
                          dd_max=c['dd'].max()))
    for _, cc in c.iterrows():
        pairs.append(dict(t_oid=r['oid'], c_oid=cc['oid'], dd=cc['dd'],
                          сцена=r['сцена'], функция=r['функция'], порог=r['порог_входа'],
                          t_shows=r['shows'], c_shows=cc['shows'], t_opens=r['opens'], c_opens=cc['opens'],
                          t_reads=r['reads'], c_reads=cc['reads'], t_ctr=r['ctr'], c_ctr=cc['ctr']))
M = pd.DataFrame(matched_t); P = pd.DataFrame(pairs)
print(f"Матчировано статей серии: {len(M)} из {len(trt)}  (без пары: {len(unmatched)})")
print(f"Всего пар treated-control: {len(P)}; уникальных контролей: {P['c_oid'].nunique()}")
print(f"Медиана |Δдата| в парах: {P['dd'].median():.1f} дн.; макс {P['dd'].max():.1f} дн.")
print()

if len(M) >= 10:
    print("--- Медианы в матчированной выборке (серия vs её контроли) ---")
    rows=[]
    for lab, tcol, ccol in [('показы','shows','c_shows'), ('открытия','opens','c_opens'),
                            ('дочитывания','reads','c_reads'), ('CTR','ctr','c_ctr'),
                            ('n_words','n_words','c_words'), ('n_paragraphs','n_paragraphs','c_par'),
                            ('n_links','n_links','c_links'), ('time_to_read_s','ttr','c_ttr')]:
        a = M[tcol].median(); b = M[ccol].median()
        rows.append(dict(показатель=lab, медиана_серия=round(a,4), медиана_контроль=round(b,4),
                         отношение_контроль_к_серии=round(b/a,2) if a not in (0,) and pd.notna(a) and a>0 else np.nan))
    print(pd.DataFrame(rows).to_string(index=False))
    print()

    print("--- Распределение ВНУТРИПАРНЫХ отношений (контроль / серия), по матчированным статьям ---")
    rows=[]
    for lab, tcol, ccol in [('показы','shows','c_shows'), ('открытия','opens','c_opens'),
                            ('дочитывания','reads','c_reads'), ('CTR','ctr','c_ctr')]:
        r = M[ccol]/M[tcol].replace(0,np.nan)
        r = r.replace([np.inf,-np.inf],np.nan).dropna()
        bs = np.array([np.median(r.values[rng.integers(0,len(r),len(r))]) for _ in range(4000)])
        rows.append(dict(показатель=lab, n=len(r), p10=round(np.percentile(r,10),2), p25=round(np.percentile(r,25),2),
                         медиана=round(r.median(),2), p75=round(np.percentile(r,75),2), p90=round(np.percentile(r,90),2),
                         CI_lo=round(np.percentile(bs,2.5),2), CI_hi=round(np.percentile(bs,97.5),2),
                         доля_отношений_gt1=round((r>1).mean()*100,1)))
    print(pd.DataFrame(rows).to_string(index=False))
    print()

    print("--- То же на уровне ОТДЕЛЬНЫХ ПАР (n пар) ---")
    rows=[]
    for lab,a,b in [('показы','t_shows','c_shows'),('открытия','t_opens','c_opens'),
                    ('дочитывания','t_reads','c_reads'),('CTR','t_ctr','c_ctr')]:
        r = (P[b]/P[a].replace(0,np.nan)).replace([np.inf,-np.inf],np.nan).dropna()
        rows.append(dict(показатель=lab, n_пар=len(r), медиана_отношения=round(r.median(),2),
                         мед_серия=round(P[a].median(),4), мед_контроль=round(P[b].median(),4),
                         отношение_медиан=round(P[b].median()/P[a].median(),2) if P[a].median()>0 else np.nan))
    print(pd.DataFrame(rows).to_string(index=False))
    print()
else:
    print("!!! Матчированных статей <10 — вывод не формулируется.")

# --- бутстрап отношения медиан дочитываний
if len(M)>=10:
    t = M['reads'].values.astype(float); c = M['c_reads'].values.astype(float)
    bs = np.array([np.median(c[i])/max(np.median(t[i]),1e-9) for i in (rng.integers(0,len(t),(4000,len(t))))])
    print(f"Отношение медиан ДОЧИТЫВАНИЙ (контроль/серия) = {np.median(c)/np.median(t):.2f}x  "
          f"CI95=[{np.percentile(bs,2.5):.2f}; {np.percentile(bs,97.5):.2f}]")
    ts = M['shows'].values.astype(float); cs = M['c_shows'].values.astype(float)
    bss = np.array([np.median(cs[i])/max(np.median(ts[i]),1e-9) for i in (rng.integers(0,len(ts),(4000,len(ts))))])
    print(f"Отношение медиан ПОКАЗОВ (контроль/серия) = {np.median(cs)/np.median(ts):.2f}x  "
          f"CI95=[{np.percentile(bss,2.5):.2f}; {np.percentile(bss,97.5):.2f}]")
print()

print("--- Состав по сценам: серия (все 70) vs матчированный контроль vs весь пул ce=True в окне ---")
win = pool[(pool['date']>=trt['date'].min())&(pool['date']<=trt['date'].max())]
ctrl_ids = set(P['c_oid'])
ctrl = pool[pool['oid'].isin(ctrl_ids)]
comp = pd.DataFrame({
    'серия_%': trt['сцена'].value_counts(normalize=True)*100,
    'матч_контроль_%': ctrl['сцена'].value_counts(normalize=True)*100,
    'весь_ce=True_в_окне_%': win['сцена'].value_counts(normalize=True)*100,
}).fillna(0).round(1)
comp['n_серия']=trt['сцена'].value_counts(); comp['n_контроль']=ctrl['сцена'].value_counts()
comp = comp.fillna(0).sort_values('серия_%',ascending=False)
print(comp.to_string()); print()

print("--- Состав по функции и порогу ---")
for col in ['функция','порог_входа']:
    c2 = pd.DataFrame({'серия_%': trt[col].value_counts(normalize=True)*100,
                       'матч_контроль_%': ctrl[col].value_counts(normalize=True)*100,
                       'ce=True_в_окне_%': win[col].value_counts(normalize=True)*100}).fillna(0).round(1)
    print(f"[{col}]"); print(c2.to_string()); print()

print("--- Текстовые характеристики: серия (все 70) vs весь ce=True в окне ---")
rows=[]
for c in ['n_words','n_chars','n_paragraphs','n_images','n_headers','n_links','n_quotes','n_list_items','time_to_read_s','read_rate','ctr']:
    rows.append(dict(признак=c, мед_серия=round(trt[c].median(),4), мед_ce_True_окно=round(win[c].median(),4),
                     отношение=round(win[c].median()/trt[c].median(),2) if trt[c].median() not in (0,) and pd.notna(trt[c].median()) and trt[c].median()>0 else np.nan))
print(pd.DataFrame(rows).to_string(index=False)); print()

print("--- Матчированные наблюдения поштучно (серия) ---")
show = M[['date','title','сцена','функция','порог','n_ctrl','shows','c_shows','reads','c_reads','ctr','c_ctr']].copy()
show['date']=show['date'].dt.date
show['отн_reads']=(show['c_reads']/show['reads'].replace(0,np.nan)).round(1)
print(show.sort_values('date').to_string(index=False))
print()
print("--- Статьи серии БЕЗ пары (не матчировались) ---")
if unmatched:
    u = pd.DataFrame(unmatched)[['date','title_studio','сцена','функция','порог_входа','shows','reads']]
    u['date']=u['date'].dt.date
    print(u.to_string(index=False))
