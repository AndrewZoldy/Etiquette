# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from scipy import stats
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
d = pd.read_pickle('vv_merged.pkl')
d['is_rub'] = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
rub = d[d.is_rub].sort_values('date').copy()

print("### A. ПРОВЕРКА УТВЕРЖДЕНИЯ ДОСЬЕ «ни у одной из 620 статей нет подзаголовков»")
print(d['подзаголовков'].value_counts(dropna=False).to_string())
sub = d[d['подзаголовков']>0]
print(f"\nстатей с подзаголовками: {len(sub)}  -> утверждение досье НЕВЕРНО" if len(sub) else "подтверждено")
if len(sub):
    s=sub[['date','title_studio','подзаголовков','n_words','абзацев','слов_в_абзаце_мед','opens','reads','read_rate','ctr']].copy()
    s['read_rate']=(s.read_rate*100).round(1); s['ctr']=(s.ctr*100).round(2); s['дата']=s.date.dt.strftime('%d.%m.%y')
    print(s.drop(columns='date').to_string(index=False))
    print(f"\nмедиана дочитываемости с подзаголовками (n={len(sub)}): {sub.read_rate.median()*100:.1f}%")
    ns=d[(d['подзаголовков']==0)&d.read_rate.notna()]
    print(f"медиана дочитываемости без подзаголовков (n={len(ns)}): {ns.read_rate.median()*100:.1f}%")
    print("ВЫВОД по группе с подзаголовками: " + ("да" if len(sub)>=10 else "НЕТ (<10) — только кейсы"))

print()
print("### B. ДЛИНА ПРЕДЛОЖЕНИЯ — ЛЕСТНИЦА ПО КАНАЛУ (без CE=False) И МЕСТО РУБРИКИ")
b = d[d.read_rate.notna()&d['слов_в_предложении_мед'].notna()&(d.comments_enabled!=False)].copy()
b['бин']=pd.cut(b['слов_в_предложении_мед'],[0,9.99,13,16,100],labels=['<10','10–13','13–16','>16'])
g=b.groupby('бин',observed=True).agg(n=('oid','size'),дочитыв_мед=('read_rate','median'),
   дочит_мед=('reads','median'),слов_мед=('n_words','median'),предл_мед=('слов_в_предложении_мед','median'))
g['дочитыв_мед']=(g.дочитыв_мед*100).round(1); g['вывод?']=np.where(g.n>=10,'да','НЕТ (<10)')
print(g.to_string())
print(f"\nрубрика: медиана слов в предложении = {rub['слов_в_предложении_мед'].median():.1f}  (по выпускам: {sorted(rub['слов_в_предложении_мед'].tolist())})")
print("рубрика по выпускам, предложение vs дочитываемость:")
q=rub[['date','n_words','слов_в_предложении_мед','доля_длинных_предложений','read_rate']].copy()
q['дата']=q.date.dt.strftime('%d.%m'); q['read_rate']=(q.read_rate*100).round(1)
print(q.drop(columns='date').to_string(index=False))
r,p=stats.spearmanr(rub['слов_в_предложении_мед'],rub.read_rate)
print(f"Спирмен рубрика: слов_в_предложении_мед ~ дочитываемость  n=10 rho={r:+.3f} p={p:.4f}")
r,p=stats.spearmanr(rub['слов_в_предложении_мед'],rub.n_words)
print(f"Спирмен рубрика: слов_в_предложении_мед ~ слов            n=10 rho={r:+.3f} p={p:.4f}  <- длина и рыхлость слиты")

print()
print("### C. ГЛАВНЫЙ КОНТРПРИМЕР: «Искусство быть петербуржцем» (21.07.2026) — на следующий день после выпуска 20–26 июля")
pick = ['Искусство быть петербуржцем','Гид по фруктовому этикету','Ошибки, которые сразу выдают',
        'Как превратить культурный выход','Светская жизнь Петербурга: 20-26 июля','Светская жизнь Петербурга: 18 – 24 мая']
mm = pd.Series(False,index=d.index)
for n in pick: mm |= d.title_studio.str.contains(n,case=False,na=False,regex=False)
f2=['n_words','абзацев','слов_в_абзаце_мед','слов_в_предложении_мед','доля_длинных_предложений','вопросов','подзаголовков',
    'n_images','длина_первого_абзаца','длина_последнего_абзаца','time_to_read_s','min_per_read','предложений',
    'обращение_вы_на100слов','первое_лицо_на100слов','цифры_на100слов','лексразнообразие']
c=d[mm].sort_values('read_rate',ascending=False)[['date','title_studio']+f2+['shows','opens','reads','ctr','read_rate','comments']].copy()
c['дата']=c.date.dt.strftime('%d.%m.%y'); c['title_studio']=c.title_studio.str.slice(0,44)
c['ctr']=(c.ctr*100).round(2); c['read_rate']=(c.read_rate*100).round(1)
print(c.drop(columns='date').set_index('title_studio').T.to_string())

print()
print("### D. ПЕТЕРБУРГ / ГОРОД: все статьи канала про город — рубрика против остальных")
mp = d.title_studio.str.contains('Петербур|Питер|Москв|город',case=False,na=False)
pt=d[mp][['date','title_studio','n_words','абзацев','слов_в_абзаце_мед','shows','opens','reads','ctr','read_rate','is_rub']].copy()
pt['дата']=pt.date.dt.strftime('%d.%m.%y'); pt['ctr']=(pt.ctr*100).round(2); pt['read_rate']=(pt.read_rate*100).round(1)
pt['title_studio']=pt.title_studio.str.slice(0,50)
print(pt.drop(columns='date').sort_values('read_rate',ascending=False).to_string(index=False))
nr=d[mp&(~d.is_rub)]
print(f"\nне-рубрика про город: n={len(nr)} -> {'вывод можно' if len(nr)>=10 else 'ГРУППА <10, вывод не формулируется, только кейсы'}")
if len(nr): print(f"  медиана дочитываемости {nr.read_rate.median()*100:.1f}%, медиана слов {nr.n_words.median():.0f}, медиана CTR {nr.ctr.median()*100:.2f}%")
print(f"рубрика: медиана дочитываемости {rub.read_rate.median()*100:.1f}%, слов {rub.n_words.median():.0f}, CTR {rub.ctr.median()*100:.2f}%")

print()
print("### E. АБЗАЦЕВ МНОГО — ЭТО САМО ПО СЕБЕ ПЛОХО? (канал без CE=False)")
b2=d[d.read_rate.notna()&d['абзацев'].notna()&(d.comments_enabled!=False)].copy()
b2['бинА']=pd.cut(b2['абзацев'],[0,8,14,25,40,200],labels=['1–8','9–14','15–25','26–40','41+'])
g2=b2.groupby('бинА',observed=True).agg(n=('oid','size'),дочитыв_мед=('read_rate','median'),дочит_мед=('reads','median'),
    слов_мед=('n_words','median'),слов_абз_мед=('слов_в_абзаце_мед','median'))
g2['дочитыв_мед']=(g2.дочитыв_мед*100).round(1); g2['вывод?']=np.where(g2.n>=10,'да','НЕТ (<10)')
print(g2.to_string())
print("\nдвумерно: абзацев x медиана длины абзаца (дочитываемость, медиана; n в скобках)")
b2['бинП']=pd.cut(b2['слов_в_абзаце_мед'],[0,20,40,60,500],labels=['<=20','21–40','41–60','60+'])
pv=b2.pivot_table(index='бинА',columns='бинП',values='read_rate',aggfunc='median',observed=True)*100
cnt=b2.pivot_table(index='бинА',columns='бинП',values='read_rate',aggfunc='size',observed=True)
comb=pv.round(1).astype(str)+" ("+cnt.fillna(0).astype(int).astype(str)+")"
print(comb.to_string())
print("\nрубрика попадает в клетку: абзацев 41+ x слов_в_абзаце 41–60 ->",
      f"{rub[(rub.абзацев>40)&(rub.слов_в_абзаце_мед>40)&(rub.слов_в_абзаце_мед<=60)].shape[0]} из 10 выпусков")
