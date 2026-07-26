# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 3: матчинг серии ce=False к контролю ce=True."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
NB,SEED=4000,20260726
m=load()
T=m[m['ceF']].copy()          # серия (treated)
C=m[m['ceT']].copy()          # пул контроля
print("="*118); print("ТРЕБОВАНИЕ 3. МАТЧИНГ СЕРИИ ce=False"); print("="*118)
print(f"серия n={len(T)}, пул контроля ce=True n={len(C)}")

def match(T,C,keys,window,k=3,replace=True):
    """Для каждой treated ищем до k ближайших по дате контролей с точным совпадением по keys и |Δдата|<=window."""
    used=set(); pairs=[]
    for i,r in T.iterrows():
        cand=C
        for kk in keys: cand=cand[cand[kk]==r[kk]]
        dd=(cand['date']-r['date']).dt.total_seconds().abs()/86400
        cand=cand.assign(_dd=dd)
        cand=cand[cand['_dd']<=window]
        if not replace: cand=cand[~cand.index.isin(used)]
        cand=cand.nsmallest(k,'_dd')
        if len(cand)==0: continue
        if not replace: used.update(cand.index)
        pairs.append((i,list(cand.index),float(cand['_dd'].median())))
    return pairs

def summarize(T,C,pairs,lbl,keys,window,replace):
    ti=[p[0] for p in pairs]; ci=sorted({c for p in pairs for c in p[1]})
    Tm=T.loc[ti]; Cm=C.loc[ci]
    print(f"\n{'='*118}\n{lbl}\n  ключи={keys}, окно=±{window} дн, замена={'да' if replace else 'нет'}")
    print(f"  матчировано treated: {len(ti)} из {len(T)}; уникальных контролей: {len(ci)}; "
          f"медиана |Δдата| = {np.median([p[2] for p in pairs]) if pairs else float('nan'):.0f} дн")
    if len(ti)<10:
        print("  *** n<10 матчированных пар — ВЫВОД НЕ ФОРМУЛИРУЕТСЯ (правило 3) ***"); return None
    rows=[]
    for col in ['shows','opens','reads','ctr','read_rate','n_words','n_paragraphs','n_links','n_images','time_to_read_s','age_days','comments','likes']:
        a=Tm[col].median(); b=Cm[col].median()
        rows.append({'метрика':col,'серия (мед)':round(float(a),4),'контроль (мед)':round(float(b),4),
                     'разрыв контроль/серия':round(float(b)/float(a),2) if a not in (0,) and pd.notna(a) and a!=0 else np.inf})
    print(pd.DataFrame(rows).to_string(index=False))
    # внутрипарные отношения
    print("\n  Внутрипарные отношения (медиана контролей пары / значение treated):")
    rr=[]
    for col in ['shows','opens','reads','ctr']:
        ratios=[]
        for i,cs,_ in pairs:
            t=T.loc[i,col]; c=C.loc[cs,col].median()
            if pd.notna(t) and pd.notna(c) and t>0: ratios.append(c/t)
        ratios=np.array(ratios)
        lr=np.random.default_rng(SEED)
        bs=np.array([np.median(ratios[lr.integers(0,len(ratios),len(ratios))]) for _ in range(NB)])
        rr.append({'метрика':col,'пар с t>0':len(ratios),'медиана отношения':round(float(np.median(ratios)),2),
                   'CI95%':f"[{np.percentile(bs,2.5):.2f};{np.percentile(bs,97.5):.2f}]",
                   'p25':round(float(np.percentile(ratios,25)),2),'p75':round(float(np.percentile(ratios,75)),2),
                   'доля пар, где контроль выше':f"{(ratios>1).mean()*100:.0f}%"})
    print(pd.DataFrame(rr).to_string(index=False))
    # бутстрап CI разрыва медиан reads
    a=Tm['reads'].values.astype(float); b=Cm['reads'].values.astype(float)
    lr=np.random.default_rng(SEED)
    bs=np.array([np.median(b[lr.integers(0,len(b),len(b))])/max(np.median(a[lr.integers(0,len(a),len(a))]),1e-9) for _ in range(NB)])
    print(f"\n  РАЗРЫВ МЕДИАНЫ ДОЧИТЫВАНИЙ (контроль/серия) = {np.median(b)/max(np.median(a),1e-9):.2f}x  "
          f"CI95%=[{np.percentile(bs,2.5):.2f};{np.percentile(bs,97.5):.2f}]")
    return dict(lbl=lbl,n_t=len(ti),n_c=len(ci),gap=float(np.median(b)/max(np.median(a),1e-9)),
                lo=float(np.percentile(bs,2.5)),hi=float(np.percentile(bs,97.5)))

# --- проверка выполнимости строгой схемы ---
print("\n--- Выполнимость строгой схемы: сколько ce=True в пуле имеют ту же тройку и попадают в ±45 дн ---")
p_strict=match(T,C,['сцена','функция','порог_входа'],45,3,True)
print(f"строгая (тройка, ±45 дн): матчировано {len(p_strict)} из {len(T)}")
print("Причина потерь — распределение тройки в серии vs в пуле внутри окна серии:")
win=C[(C['date']>=T['date'].min()-pd.Timedelta(days=45))&(C['date']<=T['date'].max()+pd.Timedelta(days=45))]
cmpc=pd.DataFrame({'серия n':T['cell'].value_counts(),'пул ce=True в окне n':win['cell'].value_counts()}).fillna(0).astype(int)
print(cmpc[cmpc['серия n']>0].to_string())

res=[]
for keys,window,repl,lbl in [
    (['сцена','функция','порог_входа'],45,True, 'СХЕМА 1 (как просил критик): тройка сцена+функция+порог, ±45 дн, с заменой'),
    (['сцена','функция','порог_входа'],90,True, 'СХЕМА 2: тройка, ±90 дн'),
    (['сцена','функция','порог_входа'],400,True,'СХЕМА 3: тройка, ±400 дн (окно почти снято)'),
    (['сцена','порог_входа'],45,True,           'СХЕМА 4: сцена+порог, ±45 дн'),
    (['сцена'],45,True,                         'СХЕМА 5: только сцена, ±45 дн'),
    (['сцена'],90,True,                         'СХЕМА 6: только сцена, ±90 дн'),
    (['сцена','функция'],90,True,               'СХЕМА 7: сцена+функция, ±90 дн'),
    (['сцена','функция','порог_входа'],90,False,'СХЕМА 8: тройка, ±90 дн, БЕЗ замены'),
]:
    r=summarize(T,C,match(T,C,keys,window,3,repl),lbl,keys,window,repl)
    if r: res.append(r)

print("\n"+"="*118); print("СВОДКА РАЗРЫВОВ ПО СХЕМАМ (дочитывания)"); print("="*118)
print(pd.DataFrame(res)[['lbl','n_t','n_c','gap','lo','hi']].to_string(index=False))

print("\n"+"="*118)
print("СОСТАВ ПО СЦЕНАМ: серия vs весь пул ce=True vs пул ce=True внутри окна серии")
print("="*118)
sc=pd.DataFrame({'серия %':T['сцена'].value_counts(normalize=True)*100,
                 'ce=True весь %':C['сцена'].value_counts(normalize=True)*100,
                 'ce=True в окне серии %':win['сцена'].value_counts(normalize=True)*100,
                 'серия n':T['сцена'].value_counts(),'ce=True в окне n':win['сцена'].value_counts()}).fillna(0).round(1)
print(sc.sort_values('серия %',ascending=False).to_string())

print("\n"+"="*118)
print("ХАРАКТЕРИСТИКИ ТЕКСТА: серия vs контроль (весь ce=True и ce=True в окне серии)")
print("="*118)
rows=[]
for col in ['n_words','n_paragraphs','n_links','n_images','n_headers','n_list_items','time_to_read_s','n_chars']:
    rows.append({'признак':col,'серия ce=False':round(float(T[col].median()),1),
                 'ce=True в окне':round(float(win[col].median()),1),
                 'ce=True весь':round(float(C[col].median()),1),
                 'отн. окно/серия':round(float(win[col].median())/float(T[col].median()),2) if T[col].median()>0 else np.inf})
print(pd.DataFrame(rows).to_string(index=False))
print("\np25/p75 по n_words: серия",[round(float(T['n_words'].quantile(q)),0) for q in (.25,.75)],
      "| ce=True в окне",[round(float(win['n_words'].quantile(q)),0) for q in (.25,.75)])

print("\n"+"="*118)
print("КОНТРОЛЬНЫЙ ТЕСТ: 'узкий справочник' объясняет? Сравнение внутри одной тройки, без матчинга по дате")
print("="*118)
key='стол_еда|польза|бытовая'
for k in [key,'стол_еда|разъяснение_нормы|бытовая','гости_праздники|польза|бытовая']:
    a=T[T['cell']==k]; b=C[(C['cell']==k)&(C['date']>=pd.Timestamp('2025-09-01'))]
    b_all=C[C['cell']==k]
    print(f"\n[{k}]  серия n={len(a)} мед reads={a['reads'].median() if len(a) else np.nan:,.0f} | "
          f"ce=True с сен.2025 n={len(b)} мед reads={b['reads'].median() if len(b) else np.nan:,.0f} | "
          f"ce=True все время n={len(b_all)} мед reads={b_all['reads'].median() if len(b_all) else np.nan:,.0f}")
    if len(a)>=10 and len(b)>=10:
        print(f"   разрыв (ce=True с сен.2025 / серия) = {b['reads'].median()/max(a['reads'].median(),1e-9):.2f}x")
    elif len(b)<10:
        print(f"   *** контроль внутри тройки n={len(b)} < 10 — вывод по этой тройке не формулируется ***")
