# -*- coding: utf-8 -*-
import pandas as pd, numpy as np
from scipy import stats
pd.set_option('display.width',300); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',400)
d=pd.read_pickle('vv_merged.pkl'); C=pd.read_pickle('vv_comments.pkl')
d['is_rub']=d.title_studio.str.contains('Светская жизнь',case=False,na=False)
rub=d[d.is_rub].sort_values('date'); base=d[d.n_words.notna()]

print("### 1. СВЕРКА ЦИФР ДОСЬЕ")
dno=d[(d['эпоха']=='3_дно')]; dno_nr=dno[~dno.is_rub]
print(f"эпоха 3_дно всего: {len(dno)} (досье: 202); без рубрики: {len(dno_nr)}")
for nm,g in [('РУБРИКА',rub),('ДНО без рубрики',dno_nr)]:
    print(f"  {nm:18s} показы={g.shows.median():.0f} откр={g.opens.median():.0f} дочит={g.reads.median():.0f} "
          f"CTR={g.ctr.median()*100:.2f}% дочитыв={g.read_rate.median()*100:.1f}% слов={g.n_words.median():.0f} "
          f"мин/дочит={g.min_per_read.median():.2f} подзаг={g['подзаголовков'].median():.0f} карт={g.n_images.median():.0f}")
print(f"  ПРОВЕРКА досье «мин на дочитывание 1,36 / 0,96»: факт рубрика={rub.min_per_read.median():.2f}, дно_без_рубрики={dno_nr.min_per_read.median():.2f}")
print(f"  ПРОВЕРКА досье «ни у одной из 620 нет подзаголовков»: статей с подзаг>0 = {(d['подзаголовков']>0).sum()}")
print(f"  дочитываемость канала (все 620): {base.read_rate.median()*100:.1f}%")

print("\n### 2. ПЕРВИЧНЫЙ ПОКАЗАТЕЛЬ — ДОЧИТЫВАНИЯ В АБСОЛЮТЕ")
print(f"сумма дочитываний всех 10 выпусков рубрики: {rub.reads.sum():,}")
for t in ['Ошибки, которые сразу выдают','Темы для светских бесед','Дама здоровается первая','Искусство быть петербуржцем']:
    r=d[d.title_studio.str.contains(t,regex=False,na=False)].iloc[0]
    print(f"  одна статья «{r.title_studio[:44]}»: {int(r.reads):,} дочитываний ({r.n_words:.0f} слов) = {r.reads/rub.reads.sum():.1f}x всей рубрики")
print(f"медиана дочитываний: рубрика {rub.reads.median():.0f} vs дно без рубрики {dno_nr.reads.median():.0f}")

print("\n### 3. КУДА ПОПАДАЕТ НОВЫЙ ЧЕРНОВИК (2517 слов, 42 абзаца, 0 подзаг, 0 картинок)")
wp=2517/42
print(f"расчётная средняя длина абзаца черновика: {wp:.0f} слов -> клетка «абзацев 41+ x абзац 41–60 слов»")
b=d[d.read_rate.notna()&(d.comments_enabled!=False)]
cell=b[(b['абзацев']>=41)&(b['слов_в_абзаце_мед']>40)&(b['слов_в_абзаце_мед']<=60)]
print(f"  в этой клетке n={len(cell)} — все выпуски рубрики? {cell.is_rub.all()}; медиана дочитываемости {cell.read_rate.median()*100:.1f}%")
cell2=b[(b['абзацев']>=30)&(b['слов_в_абзаце_мед']<=20)]
print(f"  альтернативная клетка «абзацев>=30 x абзац<=20 слов»: n={len(cell2)}, медиана дочитываемости {cell2.read_rate.median()*100:.1f}%, медиана дочитываний {cell2.reads.median():.0f}")
print(f"  черновик короче последнего выпуска на {2742-2517} слов (-8%), но абзацев 42 против 52 -> длина абзаца РАСТЁТ с 52 до ~60")

print("\n### 4. КОММЕНТАРИИ: РАЗГОВОРЧИВОСТЬ — ЭТО ЯДРО ИЗ СЕМИ ЧЕЛОВЕК")
print(f"всего комментариев 302; ответов друг другу (child): {(C.level=='child').sum()} = {(C.level=='child').mean()*100:.0f}%")
top7=C.author.value_counts().head(7)
print(f"7 авторов дали {top7.sum()} комментариев = {top7.sum()/len(C)*100:.1f}%")
print(top7.to_string())
cc=C.groupby('вып').agg(комм=('text','size'),авторов=('author','nunique'))
cc['дочит']=rub.reads.values; cc['слов']=rub.n_words.values
cc['комм_на_100_дочит']=(cc.комм/cc.дочит*100).round(1)
cc['уник_авторов_на_100_дочит']=(cc.авторов/cc.дочит*100).round(1)
print(cc.to_string())
r,p=stats.spearmanr(cc.слов,cc.комм); print(f"Спирмен: слов ~ комментариев  n=10 rho={r:+.3f} p={p:.4f}")
r,p=stats.spearmanr(cc.слов,cc.авторов); print(f"Спирмен: слов ~ уникальных авторов n=10 rho={r:+.3f} p={p:.4f}")
print(f"\nконтрпример: выпуск 5 (15.06, 1627 слов) — 77 комм / 11 авторов; выпуск 10 (20.07, 2742 слова) — 8 комм / 3 автора")

print("\n### 5. СЕРИЯ CE=False — ЧТО ЭТО И МЕНЯЕТ ЛИ ВЫВОД")
ce=d[d.comments_enabled==False]
print(f"n={len(ce)}, период {ce.date.min():%d.%m.%Y}–{ce.date.max():%d.%m.%Y}, медиана слов {ce.n_words.median():.0f}, "
      f"медиана дочитываемости {ce.read_rate.median()*100:.1f}%, медиана дочитываний {ce.reads.median():.0f}")
print("ни одной статьи >1000 слов в этой серии:", (ce.n_words>1000).sum()==0, f"(макс {ce.n_words.max():.0f} слов)")
r1,p1=stats.spearmanr(base.n_words,base.read_rate)
bb=base[base.comments_enabled!=False]; r2,p2=stats.spearmanr(bb.n_words,bb.read_rate)
print(f"слов~дочитываемость: с серией rho={r1:+.3f} (n={len(base)}), без серии rho={r2:+.3f} (n={len(bb)}) -> серия НЕ создаёт эффект")
bbb=bb[~bb.is_rub]; r3,p3=stats.spearmanr(bbb.n_words,bbb.read_rate)
print(f"без серии И без рубрики: rho={r3:+.3f} p={p3:.5f} n={len(bbb)} -> эффект длины сохраняется и без рубрики")
