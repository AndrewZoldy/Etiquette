# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 3, часть Б: конкурирующие объяснения разрыва серии."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width',260); pd.set_option('display.max_columns',60); pd.set_option('display.max_colwidth',60)
NB,SEED=4000,20260726
m=load(); T=m[m['ceF']]; C=m[m['ceT']]

print("="*118)
print("A. САМЫЙ ЖЁСТКИЙ ДИЗАЙН: серия vs ближайшая ce=True статья канала в пределах ±3 дней")
print("   (одна и та же неделя, одна и та же алгоритмическая обстановка; различие — только слот/комментарии)")
print("="*118)
rows=[]
for i,r in T.iterrows():
    dd=(C['date']-r['date']).dt.total_seconds().abs()/86400
    near=C[dd<=3]
    if len(near)==0: continue
    rows.append({'дата серии':r['date'].date(),'reads серия':r['reads'],'shows серия':r['shows'],'ctr серия':r['ctr'],
                 'n соседей':len(near),'мед reads соседей':near['reads'].median(),'мед shows соседей':near['shows'].median(),
                 'мед ctr соседей':near['ctr'].median(),
                 'отн reads':near['reads'].median()/max(r['reads'],1e-9),
                 'отн shows':near['shows'].median()/max(r['shows'],1e-9),
                 'отн ctr':near['ctr'].median()/max(r['ctr'],1e-9)})
p=pd.DataFrame(rows)
print(f"пар (серия x соседи ±3 дн): {len(p)} из {len(T)}")
for c in ['отн reads','отн shows','отн ctr']:
    v=p[c].replace([np.inf,-np.inf],np.nan).dropna().values
    lr=np.random.default_rng(SEED); bs=np.array([np.median(v[lr.integers(0,len(v),len(v))]) for _ in range(NB)])
    print(f"  {c}: медиана={np.median(v):.2f}x  CI95%=[{np.percentile(bs,2.5):.2f};{np.percentile(bs,97.5):.2f}]  "
          f"p25={np.percentile(v,25):.2f} p75={np.percentile(v,75):.2f}  доля>1: {(v>1).mean()*100:.0f}%")
print(f"\n  Медианы напрямую: reads серия {p['reads серия'].median():,.0f} vs соседи {p['мед reads соседей'].median():,.0f} "
      f"= {p['мед reads соседей'].median()/max(p['reads серия'].median(),1e-9):.1f}x")
print(f"  shows: {p['shows серия'].median():,.0f} vs {p['мед shows соседей'].median():,.0f} "
      f"= {p['мед shows соседей'].median()/max(p['shows серия'].median(),1e-9):.1f}x")
print(f"  ctr:   {p['ctr серия'].median():.4f} vs {p['мед ctr соседей'].median():.4f} "
      f"= {p['мед ctr соседей'].median()/max(p['ctr серия'].median(),1e-9):.2f}x")

print("\n"+"="*118)
print("B. ПРОВЕРКА 'УЗКОГО СПРАВОЧНИКА': что за статьи в контроле внутри тройки стол_еда|польза|бытовая")
print("="*118)
k='стол_еда|польза|бытовая'
cc=C[(C['cell']==k)&(C['date']>=pd.Timestamp('2025-09-01'))][['date','dow','shows','opens','reads','ctr','comments','title_studio']].sort_values('reads',ascending=False)
cc['date']=cc['date'].dt.strftime('%Y-%m-%d')
print(f"КОНТРОЛЬ (ce=True, тройка {k}, с сен.2025), n={len(cc)}:")
print(cc.to_string(index=False))
tt=T[T['cell']==k][['date','dow','shows','opens','reads','ctr','title_studio']].sort_values('reads',ascending=False)
tt['date']=tt['date'].dt.strftime('%Y-%m-%d')
print(f"\nСЕРИЯ (ce=False, та же тройка), n={len(tt)} — топ-8 и низ-8:")
print(pd.concat([tt.head(8),tt.tail(8)]).to_string(index=False))

print("\n"+"="*118)
print("C. БИМОДАЛЬНОСТЬ ВНУТРИ СЕРИИ: 8 статей >100k показов vs 48 статей <10k — чем отличаются")
print("="*118)
hi=T[T['shows']>100_000]; lo=T[T['shows']<10_000]
print(f"n(>100k)={len(hi)}, n(<10k)={len(lo)}")
rows=[]
for c in ['shows','opens','reads','ctr','read_rate','n_words','n_paragraphs','n_images','n_links','time_to_read_s','hour','age_days','brightness','saturation']:
    rows.append({'признак':c,'верх серии (>100k)':round(float(hi[c].median()),4),'низ серии (<10k)':round(float(lo[c].median()),4)})
print(pd.DataFrame(rows).to_string(index=False))
print("\nсцена/функция в верхе серии:", hi['сцена'].value_counts().to_dict(), hi['функция'].value_counts().to_dict())
print("сцена/функция в низе серии:", lo['сцена'].value_counts().to_dict(), lo['функция'].value_counts().to_dict())
print("порог_входа: верх", hi['порог_входа'].value_counts().to_dict(), "| низ", lo['порог_входа'].value_counts().to_dict())
print("*** n(>100k)=8 < 10 => по правилу 3 отдельный вывод по этой подгруппе НЕ формулируется, таблица приведена как контрпример ***")

print("\n"+"="*118)
print("D. ВЕС СЕРИИ В ОБЩЕЙ КАРТИНЕ (эпоха 'дно' и полугодия)")
print("="*118)
for lbl,d in [('эпоха дно',m[m['эпоха']=='3_дно']),('2025H2',m[m['half']=='2025H2']),('2026H1',m[m['half']=='2026H1'])]:
    tot=d['reads'].sum(); ser=d[d['ceF']]['reads'].sum()
    print(f"{lbl}: статей {len(d)}, из них серия {int(d['ceF'].sum())} ({d['ceF'].mean()*100:.1f}% статей); "
          f"доля серии в сумме дочитываний {ser/tot*100:.2f}%; доля в сумме показов {d[d['ceF']]['shows'].sum()/d['shows'].sum()*100:.2f}%")

print("\n"+"="*118)
print("E. КОНТРПРИМЕР-ТЕСТ: были ли ДО серии (до 16.09.2025) статьи того же узкого справочного типа")
print("   стол_еда|польза|бытовая с ce=True — и как они шли")
print("="*118)
pre=C[(C['cell']==k)&(C['date']<pd.Timestamp('2025-09-16'))]
print(f"n={len(pre)}, медиана reads={pre['reads'].median():,.0f}, медиана shows={pre['shows'].median():,.0f}, медиана ctr={pre['ctr'].median():.4f}")
print(f"доля с shows<10k: {(pre['shows']<10000).mean()*100:.1f}%; доля с reads<100: {(pre['reads']<100).mean()*100:.1f}%")
print("\nПо полугодиям (тройка стол_еда|польза|бытовая, ce=True):")
g=C[C['cell']==k].groupby('half')['reads'].agg(['size','median'])
g['мед shows']=C[C['cell']==k].groupby('half')['shows'].median()
g['мед ctr']=C[C['cell']==k].groupby('half')['ctr'].median().round(4)
g['вывод?']=np.where(g['size']<10,'нет (n<10)','')
print(g.to_string())
print("\nТа же тройка, ce=False (серия), по полугодиям:")
g2=T[T['cell']==k].groupby('half')['reads'].agg(['size','median'])
g2['мед shows']=T[T['cell']==k].groupby('half')['shows'].median()
g2['мед ctr']=T[T['cell']==k].groupby('half')['ctr'].median().round(4)
print(g2.to_string())

print("\n"+"="*118)
print("F. ПОДПИСКИ И ВОВЛЕЧЁННОСТЬ: серия vs контроль в окне")
print("="*118)
win=C[(C['date']>=T['date'].min())&(C['date']<=T['date'].max())]
rows=[]
for c in ['subs','subs_per_read','likes_per_read','comments_per_read','min_per_read','read_rate','ctr']:
    rows.append({'признак':c,'серия':round(float(T[c].median()),5),'ce=True в окне':round(float(win[c].median()),5)})
print(pd.DataFrame(rows).to_string(index=False))
