# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from scipy import stats
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 90); pd.set_option('display.max_rows', 500)

d = pd.read_pickle('vv_merged.pkl')
d['is_rub'] = d.title_studio.str.contains('Светская жизнь', case=False, na=False)
rub = d[d.is_rub].sort_values('date').copy()

print("### 0. КТО ВООБЩЕ ДЛИННЕЕ 1500 СЛОВ В КАНАЛЕ")
long_ = d[d.n_words>=1500].sort_values('n_words')
print(f"статей >=1500 слов: {len(long_)}; из них рубрика: {long_.is_rub.sum()}")
print(long_[['date','title_studio','n_words','reads','read_rate','is_rub']].to_string(index=False))
print()
for th in [1200,1000,900]:
    s=d[d.n_words>=th]
    print(f">= {th} слов: n={len(s)}, из них рубрика {s.is_rub.sum()}, НЕ рубрика {(~s.is_rub).sum()}")

print()
print("### ЧАСТЬ 4. ЕСТЬ ЛИ СТАТЬЯ >1500 СЛОВ С ДОЧИТЫВАЕМОСТЬЮ >45%")
q = d[(d.n_words>1500)]
print(f"кандидатов (>1500 слов): {len(q)}; из них дочитываемость >45%: {(q.read_rate>0.45).sum()}")
print("макс дочитываемость среди >1500 слов:", f"{q.read_rate.max()*100:.1f}%",
      "->", q.loc[q.read_rate.idxmax(),'title_studio'])
print()
print("Ближайшие «длинные и дочитываемые» — топ-15 по дочитываемости среди >=900 слов:")
z = d[d.n_words>=900].sort_values('read_rate',ascending=False).head(15)
zz = z[['date','title_studio','n_words','абзацев','слов_в_абзаце_мед','подзаголовков','вопросов','n_images',
        'длина_последнего_абзаца','слов_в_предложении_мед','time_to_read_s','min_per_read','opens','reads','read_rate','is_rub']].copy()
zz['read_rate']=(zz.read_rate*100).round(1); zz['дата']=zz.date.dt.strftime('%d.%m.%y'); zz=zz.drop(columns=['date'])
zz['title_studio']=zz.title_studio.str.slice(0,52)
print(zz.to_string(index=False))

print()
print("### ЧАСТЬ 3. РУБРИКА vs УСПЕШНЫЕ СВЕТСКИЕ СТАТЬИ")
names = ['Ошибки, которые сразу выдают человека не из светской среды',
         'Темы для светских бесед',
         'Дама здоровается первая',
         '5 ice breakers для светского вечера',
         'Как превратить культурный выход в полезное знакомство']
mask = pd.Series(False, index=d.index)
for n in names: mask |= d.title_studio.str.contains(n, case=False, na=False, regex=False)
succ = d[mask].sort_values('read_rate',ascending=False)
print(f"группа «успешные светские» из досье: n={len(succ)} -> <10, ГРУППОВОЙ ВЫВОД НЕ ФОРМУЛИРУЕТСЯ, только кейсы")
feat = ['n_words','абзацев','слов_в_абзаце_мед','вопросов','n_images','длина_последнего_абзаца',
        'time_to_read_s','min_per_read','подзаголовков','слов_в_предложении_мед','финал_вопрос',
        'вопрос_к_читателю','обращение_вы_на100слов','цифры_на100слов','n_paragraphs']
sc = succ[['title_studio']+feat+['opens','reads','read_rate','ctr','comments']].copy()
sc['title_studio']=sc.title_studio.str.slice(0,50); sc['read_rate']=(sc.read_rate*100).round(1); sc['ctr']=(sc.ctr*100).round(2)
print(sc.to_string(index=False))

print()
print("Таблица 3. Медианы: рубрика (n=10) vs 5 светских кейсов (n=5, не вывод) vs расширенная опора")
# расширенная опора >=10: эпоха 3_дно, не рубрика, дочитываемость >=50%
big = d[(~d.is_rub)&(d['эпоха']=='3_дно')&(d.read_rate>=0.50)&(d.n_words.notna())]
big2 = d[(~d.is_rub)&(d.read_rate>=0.50)&(d.n_words.notna())]
groups = [('Рубрика «Светская жизнь»', rub),
          ('5 светских кейсов из досье', succ),
          ('Канал: дно, не рубрика, дочит-ть>=50%', big),
          ('Канал целиком: не рубрика, дочит-ть>=50%', big2)]
rows=[]
for name,g in groups:
    r={'группа':name,'n':len(g),'вывод?':'да' if len(g)>=10 else 'НЕТ (<10)'}
    for f in feat: r[f]=round(g[f].median(),2) if len(g) else None
    r['показы']=g.shows.median(); r['открытия']=g.opens.median(); r['дочитывания']=g.reads.median()
    r['CTR%']=round(g.ctr.median()*100,2); r['дочитыв%']=round(g.read_rate.median()*100,1)
    r['комм/100дочит']=round((g.comments/g.reads*100).median(),1)
    rows.append(r)
T=pd.DataFrame(rows).set_index('группа').T
print(T.to_string())

print()
print("Разрывы рубрика/опора (дно, не рубрика, >=50%):")
a=rub; b=big
for f in feat+['shows','opens','reads']:
    ma,mb=a[f].median(),b[f].median()
    rat = (ma/mb) if mb not in (0,None) and not pd.isna(mb) and mb!=0 else np.nan
    print(f"  {f:28s} рубрика={ma:>9.2f}  опора={mb:>9.2f}  отношение={rat:>7.2f}x")

print()
print("### Контрпримеры внутри рубрики (против «дело только в длине»)")
cp = rub[['date','n_words','абзацев','слов_в_абзаце_мед','вопросов','shows','opens','ctr','reads','read_rate','comments']].copy()
cp['дата']=cp.date.dt.strftime('%d.%m'); cp=cp.drop(columns='date')
cp['read_rate']=(cp.read_rate*100).round(1); cp['ctr']=(cp.ctr*100).round(2)
print(cp.to_string(index=False))
