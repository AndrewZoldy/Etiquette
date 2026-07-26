# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from scipy import stats
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)
d = pd.read_pickle('vv_merged.pkl')
d['is_rub'] = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
rub = d[d.is_rub].sort_values('date').copy()
b = d[d.read_pickle_dummy] if False else d[d.read_rate.notna()&d['абзацев'].notna()&(d.comments_enabled!=False)].copy()

print("### F. «МНОГО АБЗАЦЕВ» — КТО ЭТО. Все статьи канала с абзацев>=30 (без CE=False)")
m = b[b['абзацев']>=30].sort_values('слов_в_абзаце_мед')
mm=m[['date','title_studio','n_words','абзацев','слов_в_абзаце_мед','подзаголовков','вопросов','слов_в_предложении_мед',
      'shows','opens','reads','ctr','read_rate','is_rub']].copy()
mm['дата']=mm.date.dt.strftime('%d.%m.%y'); mm['ctr']=(mm.ctr*100).round(2); mm['read_rate']=(mm.read_rate*100).round(1)
mm['title_studio']=mm.title_studio.str.slice(0,46)
print(mm.drop(columns='date').to_string(index=False))

print()
print("### G. ПРИ БОЛЬШОМ ЧИСЛЕ АБЗАЦЕВ РЕШАЕТ ДЛИНА АБЗАЦА (абзацев>=30, без CE=False)")
s=b[b['абзацев']>=30].copy()
s['грппа']=np.where(s['слов_в_абзаце_мед']<=20,'абзац <=20 слов','абзац >20 слов')
g=s.groupby('грппа').agg(n=('oid','size'),слов_мед=('n_words','median'),абз_мед=('абзацев','median'),
   слов_абз_мед=('слов_в_абзаце_мед','median'),дочитыв_мед=('read_rate','median'),дочит_мед=('reads','median'),
   показы_мед=('shows','median'),CTR_мед=('ctr','median'),предл_мед=('слов_в_предложении_мед','median'),
   вопр_мед=('вопросов','median'),подзаг_мед=('подзаголовков','median'))
g['дочитыв_мед']=(g.дочитыв_мед*100).round(1); g['CTR_мед']=(g.CTR_мед*100).round(2)
g['вывод?']=np.where(g.n>=10,'да','НЕТ (<10)')
print(g.to_string())
a=s[s['слов_в_абзаце_мед']<=20].read_rate; c2=s[s['слов_в_абзаце_мед']>20].read_rate
if len(a)>=3 and len(c2)>=3:
    u,pu=stats.mannwhitneyu(a,c2,alternative='greater')
    print(f"Манн-Уитни (короткий абзац > длинный): U={u:.0f} p={pu:.5f}  n={len(a)} vs {len(c2)}")
print("\nсостав группы «абзац <=20 слов» при абзацев>=30:")
z=s[s['слов_в_абзаце_мед']<=20][['date','title_studio','n_words','абзацев','слов_в_абзаце_мед','reads','read_rate']].copy()
z['дата']=z.date.dt.strftime('%d.%m.%y'); z['read_rate']=(z.read_rate*100).round(1); z['title_studio']=z.title_studio.str.slice(0,50)
print(z.drop(columns='date').sort_values('read_rate',ascending=False).to_string(index=False))

print()
print("### H. СПИРМЕН: слов_в_абзаце_мед ~ дочитываемость (по каналу и эпохам, без CE=False)")
for name,sub in [('канал без CE=False',b),('1_до_спада',b[b['эпоха']=='1_до_спада']),
                 ('2_склон',b[b['эпоха']=='2_склон']),('3_дно',b[b['эпоха']=='3_дно']),
                 ('3_дно, не рубрика',b[(b['эпоха']=='3_дно')&(~b.is_rub)])]:
    n=len(sub)
    if n<10: print(f"  {name:22s} n={n:4d} <10 — вывод не формулируется"); continue
    r,p=stats.spearmanr(sub['слов_в_абзаце_мед'],sub.read_rate)
    r2,p2=stats.spearmanr(sub['абзацев'],sub.read_rate)
    print(f"  {name:22s} n={n:4d}  слов_в_абзаце~дочитыв rho={r:+.3f} p={p:.5f} | абзацев~дочитыв rho={r2:+.3f} p={p2:.5f}")

print()
print("### I. КОНТРПРИМЕРЫ ПРОТИВ «ДЛИНА = ПРИГОВОР»: 1000–1500 слов, не рубрика")
q=d[(d.n_words>=1000)&(d.n_words<1500)][['date','title_studio','n_words','абзацев','слов_в_абзаце_мед','подзаголовков',
    'вопросов','слов_в_предложении_мед','n_images','time_to_read_s','min_per_read','shows','opens','reads','ctr','read_rate']].copy()
q['дата']=q.date.dt.strftime('%d.%m.%y'); q['ctr']=(q.ctr*100).round(2); q['read_rate']=(q.read_rate*100).round(1)
q['title_studio']=q.title_studio.str.slice(0,46)
print(q.drop(columns='date').sort_values('read_rate',ascending=False).to_string(index=False))
print(f"\nn={len(q)} -> {'вывод можно' if len(q)>=10 else 'мало'};  медиана дочитываемости {q.read_rate.median():.1f}%")
print(f"из них >=45% дочитываемости: {(q.read_rate>=45).sum()} из {len(q)}")
