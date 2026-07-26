# -*- coding: utf-8 -*-
"""R6: экспозиция по 10 опубликованным выпускам + R5(а) + расшифровка 202 + проверка «минут»."""
import pandas as pd, numpy as np, os, re, json, math, itertools
from scipy import stats
np.random.seed(20260726)
pd.set_option('display.width', 400); pd.set_option('display.max_columns', 80); pd.set_option('display.max_rows', 600)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
full = pd.read_pickle(os.path.join(OUT,'full.pkl'))
ves  = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
V = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date').reset_index(drop=True)
V['num'] = np.arange(1,11)

MON = {'января':1,'февраля':2,'марта':3,'апреля':4,'мая':5,'июня':6,'июля':7,'августа':8,'сентября':9,'октября':10,'ноября':11,'декабря':12}
MONRE = '|'.join(MON.keys())
DATE_RE = re.compile(r'(\d{1,2})\s+(%s)' % MONRE)
TIME_RE = re.compile(r'\b([01]?\d|2[0-3])[:.]([0-5]\d)\b')

# --- точное критическое rho для n=10 ---
perms = np.array(list(itertools.permutations(range(1,11))), dtype=np.int16)
d2 = ((perms - np.arange(1,11,dtype=np.int16))**2).sum(axis=1)
rho_null_abs = np.sort(np.abs(1.0-6.0*d2/(10*99)))
def exact_p(r): return float((rho_null_abs >= abs(r)-1e-12).sum())/len(rho_null_abs)

recs=[]
for r in V.itertuples():
    pg = json.load(open(os.path.join(OUT,'pages', r.oid+'.json'), encoding='utf-8'))
    vr = json.load(open(os.path.join(OUT,'vraw', r.oid+'.json'), encoding='utf-8'))
    blocks = (vr['draft'].get('draftJsState') or {}).get('blocks') or []
    paras = pg['paragraphs']
    pub = r.date
    # неделя выпуска = 7 дней от даты публикации (понедельник) включительно
    week = [(pub.normalize() + pd.Timedelta(days=i)) for i in range(7)]
    sat = [d for d in week if d.dayofweek==5][0]
    weekset = {(d.day, d.month) for d in week}
    words = [len(p.split()) for p in paras]
    tot = sum(words)
    # события
    ev_par = 0; ev_mentions = 0; anydate = 0; first_sat_idx = None; sat_mentions = 0
    startdate = 0
    for i,p in enumerate(paras):
        ms = DATE_RE.findall(p)
        inweek = [(int(a), MON[b]) for a,b in ms if (int(a), MON[b]) in weekset]
        anydate += len(ms)
        if inweek:
            ev_par += 1; ev_mentions += len(inweek)
        if DATE_RE.match(p.strip()):
            startdate += 1
        if (sat.day, sat.month) in [(int(a),MON[b]) for a,b in ms]:
            sat_mentions += 1
            if first_sat_idx is None: first_sat_idx = i
    before = sum(words[:first_sat_idx]) if first_sat_idx is not None else tot
    # выделения
    nst = sum(len(b.get('inlineStyleRanges') or []) for b in blocks)
    stylechars = sum(sum(x.get('length',0) for x in (b.get('inlineStyleRanges') or [])) for b in blocks)
    styles = sorted({x.get('style') for b in blocks for x in (b.get('inlineStyleRanges') or [])})
    ntimes = sum(len(TIME_RE.findall(p)) for p in paras)
    quotes = sum(p.count('«') for p in paras)
    recs.append(dict(num=r.num, выпуск=r.title_studio.replace('Светская жизнь Петербурга: ',''),
        dow=r.date.day_name(), hour=r.date.hour, слов=tot, абзацев=len(paras),
        медиана_абзаца=float(np.median(words)), первый_абзац=words[0], последний_абзац=words[-1],
        событий_абзацев=ev_par, упоминаний_дат_недели=ev_mentions, всего_упоминаний_дат=anydate,
        абзацев_с_даты=startdate, кавычек=quotes, времён_ЧЧММ=ntimes,
        иллюстраций=int(r.n_images), подзаголовков=int(r.n_headers), ссылок=len(pg['links']),
        выделений=nst, знаков_под_выделением=stylechars, стили=','.join(s for s in styles if s),
        вопросов=int(r.вопросов), суббота=str(sat.date()), упоминаний_субботы=sat_mentions,
        индекс_1го_субботнего=(first_sat_idx if first_sat_idx is not None else -1),
        доля_текста_до_субботы=before/tot,
        read_rate=r.read_rate, reads=r.reads, ctr=r.ctr, shows=r.shows, opens=r.opens,
        мед_слов_в_предл=r.слов_в_предложении_мед, cover_tpl=r.cover_tpl, cover_color=r.cover_main_color,
        brightness=r.brightness, saturation=r.saturation, contrast=r.contrast, якорь=int(r.конкретный_якорь)))
E = pd.DataFrame(recs)
print('='*130)
print('R6-A. ЭКСПОЗИЦИЯ, ИЗМЕРЕННАЯ НА ВСЕХ 10 ОПУБЛИКОВАННЫХ ВЫПУСКАХ')
print('='*130)
show = ['num','выпуск','слов','абзацев','медиана_абзаца','событий_абзацев','упоминаний_дат_недели','всего_упоминаний_дат',
        'абзацев_с_даты','иллюстраций','подзаголовков','выделений','знаков_под_выделением','времён_ЧЧММ','кавычек','вопросов',
        'суббота','упоминаний_субботы','индекс_1го_субботнего','доля_текста_до_субботы','read_rate','reads','ctr']
print(E[show].to_string(index=False))
print()
print('--- медианы и дисперсия по каждой переменной экспозиции ---')
vars_ = ['слов','абзацев','медиана_абзаца','первый_абзац','последний_абзац','событий_абзацев','упоминаний_дат_недели',
         'всего_упоминаний_дат','абзацев_с_даты','иллюстраций','подзаголовков','выделений','знаков_под_выделением',
         'времён_ЧЧММ','кавычек','вопросов','доля_текста_до_субботы','упоминаний_субботы','мед_слов_в_предл','hour',
         'brightness','saturation','contrast','якорь']
rows=[]
for v in vars_:
    x = E[v].astype(float).values
    rows.append({'переменная':v,'медиана':np.median(x),'min':x.min(),'max':x.max(),'SD':x.std(ddof=1),
                 'уник. значений':len(np.unique(x)),'дисперсия':'НУЛЕВАЯ' if x.std()==0 else 'есть'})
D = pd.DataFrame(rows)
print(D.to_string(index=False))
print()
print('--- категориальные / константные признаки ---')
for c in ['dow','cover_tpl','cover_color','стили']:
    print('  %-12s уник. значений: %d -> %s' % (c, E[c].nunique(), dict(E[c].value_counts())))
print('  обложка (шаблон cover_tpl) одинаковый у всех 10: %s' % (E['cover_tpl'].nunique()==1))
print('  день выхода одинаковый у всех 10: %s (%s)' % (E['dow'].nunique()==1, E['dow'].iloc[0]))

print()
print('='*130)
print('R6-B. rho КАЖДОЙ ПЕРЕМЕННОЙ ЭКСПОЗИЦИИ С ДОЧИТЫВАЕМОСТЬЮ И С ДОЧИТЫВАНИЯМИ (n=10; порог 0,648 / точный 0,636)')
print('='*130)
rows=[]
for v in vars_:
    x = E[v].astype(float).values
    if x.std()==0:
        rows.append({'переменная':v,'дисперсия':'НУЛЕВАЯ','rho с дочитываемостью':np.nan,'p':np.nan,
                     'rho с дочитываниями':np.nan,'p ':np.nan,'вердикт':'ретроспективно неидентифицируемо'})
        continue
    r1 = stats.spearmanr(x, E['read_rate']).statistic
    r2 = stats.spearmanr(x, E['reads']).statistic
    verd = []
    verd.append('дочитываемость: %s' % ('ЗНАЧИМО' if abs(r1)>=0.648 else '|rho|<0,648 -> доля <=10%'))
    verd.append('дочитывания: %s' % ('ЗНАЧИМО' if abs(r2)>=0.648 else 'нет'))
    rows.append({'переменная':v,'дисперсия':'есть','rho с дочитываемостью':r1,'p':exact_p(r1),
                 'rho с дочитываниями':r2,'p ':exact_p(r2),'вердикт':'; '.join(verd)})
print(pd.DataFrame(rows).to_string(index=False))
print()
print('--- частные rho экспозиции при контроле номера выпуска (df=7, порог 0,666) ---')
def partial(x, y, z):
    rxy = stats.spearmanr(x,y).statistic; rxz = stats.spearmanr(x,z).statistic; ryz = stats.spearmanr(y,z).statistic
    return (rxy-rxz*ryz)/math.sqrt((1-rxz**2)*(1-ryz**2))
for v in vars_:
    x = E[v].astype(float).values
    if x.std()==0: continue
    p1 = partial(x, E['read_rate'].values, E['num'].values)
    p2 = partial(x, E['reads'].values, E['num'].values)
    print('  %-24s rho(номер, X) = %+.3f | частн. X|номер -> дочитываемость = %+.3f %s | -> дочитывания = %+.3f %s'
          % (v, stats.spearmanr(x, E['num']).statistic, p1, '(ЗНАЧ)' if abs(p1)>=0.666 else '      ', p2, '(ЗНАЧ)' if abs(p2)>=0.666 else ''))

print()
print('='*130)
print('R6-C. ЧТО ИЗМЕРЕНО В ДОСЬЕ НА ЧЕРНОВИКЕ / ОДНОМ ВЫПУСКЕ — И ЧТО РЕАЛЬНО В 10 ВЫПУСКАХ')
print('='*130)
print('досье: «41 событие», «42 абзаца», «медиана абзаца 52 слова», «5,86 события в день», «61 слово на событие» — черновик 2 517 слов (не опубликован)')
print('в 10 опубликованных: событий(абзацев с датой недели) медиана %.1f (размах %d-%d) ; абзацев медиана %.1f (%d-%d) ; медиана абзаца медиана %.1f (%.0f-%.0f)'
      % (E['событий_абзацев'].median(), E['событий_абзацев'].min(), E['событий_абзацев'].max(),
         E['абзацев'].median(), E['абзацев'].min(), E['абзацев'].max(),
         E['медиана_абзаца'].median(), E['медиана_абзаца'].min(), E['медиана_абзаца'].max()))
print('последний выпуск (20-26 июля): абзацев %d, медиана абзаца %.0f, иллюстраций %d — досье говорит «52 абзаца, медиана 52 слова, 5 илл.»'
      % (E['абзацев'].iloc[-1], E['медиана_абзаца'].iloc[-1], E['иллюстраций'].iloc[-1]))
print('слов на событие (медиана по 10): %.1f' % np.median(E['слов']/E['событий_абзацев'].clip(lower=1)))

print()
print('='*130)
print('R5(а). СКОЛЬКО НЕ-ДАЙДЖЕСТОВ ДЛИННЕЕ 1 200 СЛОВ')
print('='*130)
isv = full['title_studio'].str.startswith('Светская жизнь Петербурга')
both = full[full['src']=='both']
d3 = both[both['эпоха']=='3_дно']
base = d3[~d3['title_studio'].str.startswith('Светская жизнь Петербурга')]
for nm, d in [('все 620 статей с текстом', both), ('дно (база), без рубрики', base)]:
    for thr in [1200, 1500, 1000, 900]:
        sub = d[(d['n_words']>=thr) & (~d['title_studio'].str.startswith('Светская жизнь Петербурга'))]
        print('%-28s слов >= %4d : n = %3d %s' % (nm, thr, len(sub), '<-- ГРУППА МЕНЬШЕ 10, ВЫВОД НЕ ФОРМУЛИРУЕТСЯ' if len(sub)<10 else ''))
print()
print('все статьи канала (кроме рубрики) длиннее 1 200 слов — полный список:')
lst = both[(both['n_words']>=1200) & (~isv)]
print(lst[['date','title_studio','n_words','shows','opens','reads','ctr','read_rate','эпоха']].sort_values('n_words', ascending=False).to_string(index=False))
print()
print('все статьи канала (кроме рубрики) длиннее 1 000 слов:')
lst2 = both[(both['n_words']>=1000) & (~isv)]
print(lst2[['date','title_studio','n_words','reads','ctr','read_rate','эпоха']].sort_values('n_words', ascending=False).to_string(index=False))
print()
print('максимум слов среди не-рубричных статей: %.0f ; 95-й процентиль: %.0f ; 99-й: %.0f'
      % (both[~isv]['n_words'].max(), np.percentile(both[~isv]['n_words'],95), np.percentile(both[~isv]['n_words'],99)))

print()
print('='*130)
print('R3(доп). ПОИСК ФИЛЬТРА, ДАЮЩЕГО РОВНО 202')
print('='*130)
cands = {
 'дно ∩ both ∩ не рубрика': len(base),
 'дно ∩ both ∩ не рубрика ∩ reads>0': len(base[base['reads']>0]),
 'дно ∩ все ∩ не рубрика': len(full[(full['эпоха']=='3_дно') & ~isv]),
 'дно ∩ both': len(d3),
 'дно ∩ both ∩ не рубрика ∩ age>=7д': len(base[base['date']<=pd.Timestamp('2026-07-19')]),
 'дно ∩ both ∩ не рубрика ∩ age>=14д': len(base[base['date']<=pd.Timestamp('2026-07-12')]),
 'дно ∩ both ∩ не рубрика ∩ age>=30д': len(base[base['date']<=pd.Timestamp('2026-06-26')]),
 'дно ∩ both ∩ не рубрика ∩ не серийная': len(base[base['серийная_рубрика']==0]),
 'дно ∩ both ∩ не серийная': len(d3[d3['серийная_рубрика']==0]),
}
for k,v in cands.items():
    print('  %-46s n = %3d %s' % (k, v, '<== РОВНО 202' if v==202 else ''))
print()
print('серийные рубрики в дне (кроме «Светской жизни»):')
ser = d3[(d3['серийная_рубрика']==1) & ~d3['title_studio'].str.startswith('Светская жизнь Петербурга')]
print(ser[['date','title_studio','n_words','reads','read_rate']].to_string(index=False) if len(ser) else '  нет')
print()
for nm, d in [('202-кандидат: дно∩both∩не рубрика∩не серийная', d3[(d3['серийная_рубрика']==0)]),
              ('204: дно∩both∩не рубрика', base)]:
    print('%-46s n=%3d медCTR %.4f медДочитываемость %.4f медДочит %.0f медСлов %.0f медПоказы %.0f'
          % (nm, len(d), d['ctr'].median(), d['read_rate'].median(), d['reads'].median(), d['n_words'].median(), d['shows'].median()))

print()
print('='*130)
print('R4(доп). ПРОВЕРКА КОЛОНКИ «МИНУТ НА ДОЧИТЫВАНИЕ» НА АРИФМЕТИКУ')
print('='*130)
print('колонка min_per_read = «Время просмотра, мин» / «Дочитывания»? проверка на рубрике:')
for r in V.itertuples():
    print('   %-30s минуты=%6d дочит=%5d открытия=%5d | minutes/reads=%.4f (в файле %.4f) | minutes/opens=%.4f'
          % (r.title_studio.replace('Светская жизнь Петербурга: ',''), r.minutes, r.reads, r.opens,
             r.minutes/r.reads, r.min_per_read, r.minutes/r.opens))
print()
mw = V['n_words'].median(); mm = V['min_per_read'].median()
print('рубрика: медиана слов %.0f / медиана мин-на-дочит %.4f = %.0f слов в минуту' % (mw, mm, mw/mm))
print('рубрика: медиана слов %.0f / медиана (минуты/открытия) %.4f = %.0f слов в минуту' % (mw, (V['minutes']/V['opens']).median(), mw/(V['minutes']/V['opens']).median()))
bw = base['n_words'].median(); bm = base['min_per_read'].median()
print('канал(база): медиана слов %.0f / медиана мин-на-дочит %.4f = %.0f слов в минуту' % (bw, bm, bw/bm))
print('канал(база): медиана слов %.0f / медиана (минуты/открытия) %.4f = %.0f слов в минуту' % (bw, (base['minutes']/base['opens']).median(), bw/(base['minutes']/base['opens']).median()))
print('норма чтения взрослого — 200-250 слов/мин; оба значения выше в 2,5-6 раз')
print()
print('контрольная проверка на РОЛИКАХ (дочитываемость ~100%, значит «дочитавшие» = почти все открывшие):')
print('  если бы «Время просмотра, мин» было честным временем на пользователя, мин/дочит у роликов был бы ~0,2-1,0 мин.')
print('  фактическая медиана мин/дочит у роликов из листа «Сводка» выгрузки = 0,00405 мин = 0,24 секунды.')
print('  вывод: колонка «Время просмотра, мин» в этой выгрузке НЕ является временем на одного просмотревшего.')
print()
print('минуты==0 или ==1 у скольких статей канала (квантование):')
print('  minutes<=1: %d из %d (%.1f%%) ; minutes<=5: %d (%.1f%%)' % ((both['minutes']<=1).sum(), len(both), 100*(both['minutes']<=1).mean(), (both['minutes']<=5).sum(), 100*(both['minutes']<=5).mean()))
print('  rho(слов, мин-на-дочит) по 620 статьям = %+.3f ; rho(слов, минуты/открытия) = %+.3f'
      % (stats.spearmanr(both['n_words'], both['min_per_read']).statistic,
         stats.spearmanr(both['n_words'], both['minutes']/both['opens'].clip(lower=1)).statistic))
E.to_pickle(os.path.join(OUT,'expo10.pkl'))
