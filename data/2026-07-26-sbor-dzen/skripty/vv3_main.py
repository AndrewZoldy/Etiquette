# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from scipy import stats
pd.set_option('display.width', 280); pd.set_option('display.max_columns', 80); pd.set_option('display.max_rows', 400)

d = pd.read_pickle('vv_merged.pkl')
d['is_rub'] = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
rub = d[d.is_rub].sort_values('date').copy()

def sp(x, y, label, n_min=10):
    x = pd.Series(x); y = pd.Series(y)
    ok = x.notna() & y.notna()
    x, y = x[ok], y[ok]
    n = len(x)
    if n < n_min:
        return f"{label:52s} n={n:4d}  ГРУППА <10 — вывод не формулируется"
    r, p = stats.spearmanr(x, y)
    return f"{label:52s} n={n:4d}  rho={r:+.3f}  p={p:.4f}"

print("#"*100)
print("# ЧАСТЬ 1. ДЛИНА vs ДОЧИТЫВАЕМОСТЬ ВНУТРИ РУБРИКИ (10 выпусков)")
print("#"*100)
cols = ['date','title_studio','n_words','абзацев','слов_в_абзаце_мед','вопросов','n_images',
        'длина_последнего_абзаца','time_to_read_s','min_per_read','shows','opens','reads','ctr','read_rate','comments']
t = rub[cols].copy()
t['№'] = range(1,11)
t['дата'] = t.date.dt.strftime('%d.%m.%Y')
out = t[['№','дата','n_words','абзацев','слов_в_абзаце_мед','вопросов','n_images','длина_последнего_абзаца',
         'time_to_read_s','shows','opens','reads','ctr','read_rate','min_per_read','comments']]
out.columns = ['№','дата','слов','абз','слов/абз_мед','?','карт','посл_абз','дзен_сек','показы','откр','дочит','CTR','дочитыв','мин/дочит','комм']
out = out.copy()
out['CTR'] = (out['CTR']*100).round(2); out['дочитыв'] = (out['дочитыв']*100).round(1)
out['мин/дочит'] = out['мин/дочит'].round(2)
print(out.to_string(index=False))
print()
print(sp(rub.n_words, rub.read_rate, "рубрика: слов ~ дочитываемость"))
print(sp(rub.n_words, rub.reads,     "рубрика: слов ~ дочитывания (абс.)"))
print(sp(rub.n_words, rub.ctr,       "рубрика: слов ~ CTR"))
print(sp(rub.n_words, rub.opens,     "рубрика: слов ~ открытия"))
print(sp(np.arange(len(rub)), rub.n_words, "рубрика: номер выпуска ~ слов (тренд объёма)"))
print(sp(np.arange(len(rub)), rub.read_rate, "рубрика: номер выпуска ~ дочитываемость"))
print(sp(rub.абзацев, rub.read_rate, "рубрика: абзацев ~ дочитываемость"))
print(sp(rub.слов_в_абзаце_мед, rub.read_rate, "рубрика: медиана абзаца ~ дочитываемость"))
print(sp(rub.time_to_read_s, rub.read_rate, "рубрика: время чтения Дзена ~ дочитываемость"))
print(sp(rub.shows, rub.read_rate, "рубрика: показы ~ дочитываемость (контроль раздачи)"))
print(sp(rub.shows, rub.n_words, "рубрика: показы ~ слов (проверка смешения)"))

# частная корреляция слов~дочитываемость при контроле показов (Спирмен на рангах)
def pcorr_spearman(x,y,z):
    X=pd.Series(x).rank(); Y=pd.Series(y).rank(); Z=pd.Series(z).rank()
    rxy=np.corrcoef(X,Y)[0,1]; rxz=np.corrcoef(X,Z)[0,1]; ryz=np.corrcoef(Y,Z)[0,1]
    return (rxy-rxz*ryz)/np.sqrt((1-rxz**2)*(1-ryz**2))
print(f"{'рубрика: слов~дочитываемость | контроль показов':52s} n=  10  rho_part={pcorr_spearman(rub.n_words,rub.read_rate,rub.shows):+.3f}")

# бины по длине внутри рубрики
print()
print("Таблица 1б. Рубрика, бины по длине (медианы; группы по 3-4 выпуска — только описание, не вывод)")
rub['бин'] = pd.cut(rub.n_words, [1400,1700,2100,2800], labels=['1505–1627','1808–2007','2275–2742'])
g = rub.groupby('бин', observed=True).agg(n=('oid','size'), слов_мед=('n_words','median'),
        дочитыв_мед=('read_rate','median'), дочит_мед=('reads','median'), CTR_мед=('ctr','median'),
        абз_мед=('абзацев','median'), комм_мед=('comments','median'))
g['дочитыв_мед']=(g.дочитыв_мед*100).round(1); g['CTR_мед']=(g.CTR_мед*100).round(2)
print(g.to_string())

print()
print("#"*100)
print("# ЧАСТЬ 2. ДЛИНА vs ДОЧИТЫВАЕМОСТЬ ПО ВСЕМУ КАНАЛУ")
print("#"*100)
base = d[d.n_words.notna() & d.read_rate.notna()].copy()
ce_off = base[base.comments_enabled==False]
print(f"Всего с текстом и метрикой: {len(base)};  comments_enabled==False: {len(ce_off)} (серия застольного этикета, 2025-09..2026-02)")
print(f"  серия CE=False: медиана слов {ce_off.n_words.median():.0f}, медиана дочитываемости {ce_off.read_rate.median()*100:.1f}%")
print()
rows=[]
for name, sub in [('ВЕСЬ КАНАЛ (как есть)', base),
                  ('ВЕСЬ КАНАЛ без CE=False', base[base.comments_enabled!=False])]:
    for ep in ['ВСЕ','1_до_спада','2_склон','3_дно']:
        s = sub if ep=='ВСЕ' else sub[sub['эпоха']==ep]
        n=len(s)
        if n<10:
            rows.append([name,ep,n,None,None,None,None,'<10 — вывод не формулируется']); continue
        r,p = stats.spearmanr(s.n_words, s.read_rate)
        r2,p2 = stats.spearmanr(s.n_words, s.reads)
        rows.append([name,ep,n,round(r,3),round(p,6),round(r2,3),round(p2,6),
                     f"мед.слов={s.n_words.median():.0f} мед.дочитыв={s.read_rate.median()*100:.1f}%"])
R=pd.DataFrame(rows, columns=['выборка','эпоха','n','rho слов~дочитываемость','p','rho слов~дочитывания','p2','справка'])
print(R.to_string(index=False))

print()
print("Таблица 2б. Лестница длины по каналу без CE=False (медианы; группы <10 помечены)")
bins=[0,400,600,800,1000,1500,3000]
labs=['<400','400–599','600–799','800–999','1000–1499','1500+']
for name, sub in [('канал без CE=False', base[base.comments_enabled!=False]),
                  ('эпоха 3_дно без CE=False', base[(base.comments_enabled!=False)&(base['эпоха']=='3_дно')])]:
    s=sub.copy(); s['бин']=pd.cut(s.n_words,bins,labels=labs)
    g=s.groupby('бин',observed=True).agg(n=('oid','size'), слов_мед=('n_words','median'),
        дочитыв_мед=('read_rate','median'), дочит_мед=('reads','median'), показы_мед=('shows','median'),
        CTR_мед=('ctr','median'), абз_мед=('абзацев','median'), слов_абз_мед=('слов_в_абзаце_мед','median'))
    g['дочитыв_мед']=(g.дочитыв_мед*100).round(1); g['CTR_мед']=(g.CTR_мед*100).round(2)
    g['вывод?']=np.where(g.n>=10,'да','НЕТ (<10)')
    print(f"\n-- {name} --")
    print(g.to_string())
