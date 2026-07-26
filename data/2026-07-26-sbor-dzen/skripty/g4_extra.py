# -*- coding: utf-8 -*-
"""R5(д) прокси накопления, R1 доп. доли (комментарии), инвентаризация выгрузки."""
import pandas as pd, numpy as np, os, json, glob, math
from scipy import stats
np.random.seed(20260726)
pd.set_option('display.width', 320); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 400)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
full = pd.read_pickle(os.path.join(OUT,'full.pkl'))
ves  = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
V = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date').reset_index(drop=True)
V['num']=np.arange(1,11)
both = full[full['src']=='both']
d3 = both[both['эпоха']=='3_дно']
base = d3[~d3['title_studio'].str.startswith('Светская жизнь Петербурга')]

# --- структура файла комментариев ---
p0 = os.path.join(OUT,'comments', V['oid'].iloc[0]+'.json')
print('пример файла комментариев:', os.path.basename(p0), 'exists', os.path.exists(p0))
if os.path.exists(p0):
    d = json.load(open(p0, encoding='utf-8'))
    print('тип:', type(d).__name__, ('ключи: '+str(list(d.keys())[:12])) if isinstance(d,dict) else ('n=%d'%len(d)))
    if isinstance(d, dict):
        for k in list(d.keys())[:6]:
            v = d[k]
            print('  ', k, type(v).__name__, (len(v) if hasattr(v,'__len__') else v))
        it = d.get('comments') or d.get('items') or []
        if it: print('  первый элемент:', json.dumps(it[0], ensure_ascii=False)[:600])
    else:
        print('  первый элемент:', json.dumps(d[0], ensure_ascii=False)[:600])
print()
print('='*120)
print('R5(д)-ПРОКСИ. НАКОПЛЕНИЕ ВОВЛЕЧЕНИЯ ПО СУТКАМ ОТ ПУБЛИКАЦИИ (по времени комментариев)')
print('  прямых показов по дням в выгрузке нет; комментарии — единственный доступный временной след')
print('='*120)
def load_comments(oid):
    p = os.path.join(OUT,'comments', oid+'.json')
    if not os.path.exists(p): return []
    d = json.load(open(p, encoding='utf-8'))
    if isinstance(d, dict):
        for k in ('comments','items','root','all'):
            if isinstance(d.get(k), list): return d[k]
        return []
    return d if isinstance(d, list) else []
def ts_of(c):
    for k in ('timestamp','time','createTime','addTime','ts','date'):
        if k in c and isinstance(c[k], (int,float)) and c[k]>1e9:
            return c[k]/1000.0 if c[k]>1e11 else c[k]
    return None
rows=[]
for r in V.itertuples():
    cs = load_comments(r.oid)
    ts = [ts_of(c) for c in cs]; ts=[t for t in ts if t]
    if not ts:
        rows.append(dict(выпуск=r.title_studio[-14:], n_комм=len(cs), доля_24ч=np.nan, доля_48ч=np.nan, доля_72ч=np.nan, доля_96ч=np.nan)); continue
    pub = r.date.timestamp()
    age = np.array([(t-pub)/86400.0 for t in ts]); age=age[age>=-0.05]
    rows.append(dict(выпуск=r.title_studio.replace('Светская жизнь Петербурга: ',''), n_комм=len(age),
        доля_24ч=(age<=1).mean(), доля_48ч=(age<=2).mean(), доля_72ч=(age<=3).mean(), доля_96ч=(age<=4).mean(),
        доля_7д=(age<=7).mean(), медиана_возраста=np.median(age)))
A = pd.DataFrame(rows)
print(A.to_string(index=False))
if A['доля_48ч'].notna().sum()>=1:
    print()
    print('медиана доли комментариев за первые 48 ч = %.3f ; за 24 ч = %.3f ; за 72 ч = %.3f ; за 7 дней = %.3f'
          % (A['доля_48ч'].median(), A['доля_24ч'].median(), A['доля_72ч'].median(), A['доля_7д'].median()))
    print('порог решающего правила: >=60%% показов за первые двое суток. Прокси по комментариям даёт %.1f%% за 48 ч.'
          % (100*A['доля_48ч'].median()))
    print('ВАЖНО: это вовлечение, а не показы. Прямого ответа на (д) в выгрузке нет.')

print()
print('='*120
      )
print('R1-C. КОММЕНТАРИИ НА 100 ДОЧИТЫВАНИЙ — ПЕРЕСЧЁТ НА МЕДИАНАХ')
print('='*120)
V2 = V.copy(); V2['c100'] = 100*V2['comments']/V2['reads']
b2 = base.copy(); b2['c100'] = 100*b2['comments']/b2['reads'].clip(lower=1)
print('рубрика: ряд c100 =', ', '.join('%.1f'%x for x in np.sort(V2['c100'].values)))
print('рубрика: медиана %.2f ; агрегат %.2f (%d комм / %d дочит)' % (V2['c100'].median(), 100*V2['comments'].sum()/V2['reads'].sum(), V2['comments'].sum(), V2['reads'].sum()))
print('база 202/204: медиана %.2f ; агрегат %.2f' % (b2['c100'].median(), 100*b2['comments'].sum()/b2['reads'].sum()))
print('отношение медиан = %.2f×  (в досье «в 3-19 раз», база «около 4 на 100»)' % (V2['c100'].median()/b2['c100'].median()))
B=20000
ia=np.random.randint(0,10,(B,10)); ib=np.random.randint(0,len(b2),(B,len(b2)))
rr = np.median(V2['c100'].values[ia],axis=1)/np.median(b2['c100'].values[ib],axis=1)
print('бутстрап CI отношения: [%.2f; %.2f]' % (np.percentile(rr,2.5), np.percentile(rr,97.5)))
print('медиана абсолютных комментариев: рубрика %.1f ; база %.1f -> ниже в %.2f×'
      % (V2['comments'].median(), b2['comments'].median(), b2['comments'].median()/V2['comments'].median()))

print()
print('='*120)
print('R5(б)(в)(г)(д). ИНВЕНТАРИЗАЦИЯ ВЫГРУЗКИ: ЧТО В НЕЙ ЕСТЬ ФАКТИЧЕСКИ')
print('='*120)
import openpyxl, warnings
warnings.filterwarnings('ignore')
wb = openpyxl.load_workbook(r'D:/Work/Etiquette/Etiquette/data/2026-07-25-dzen-vse-vremya.xlsx', read_only=True, data_only=True)
ws = wb['Статьи']
hdr = None
for i,r in enumerate(ws.iter_rows(values_only=True)):
    if i==3: hdr = list(r); break
wb.close()
print('листы файла: Как читать, Сводка, Статьи, Ролики, Посты, Видео')
print('колонок на листе «Статьи»: %d' % len([h for h in hdr if h]))
for i,h in enumerate(hdr):
    if h: print('   %2d. %s' % (i+1, h))
print()
for need, verdict in [
   ('карта скролла / удержания по статье', 'НЕТ ни одной колонки'),
   ('гео на уровне публикации', 'НЕТ ни одной колонки'),
   ('источник трафика (подписка/рекомендации) по публикации', 'НЕТ ни одной колонки'),
   ('показы по дням после публикации', 'НЕТ: одна строка на публикацию, «Всё время»')]:
    print('  %-56s -> %s' % (need, verdict))

print()
print('='*120)
print('ДОП. ПРОВЕРКА: КАКИЕ ЯЗЫКОВЫЕ/СТРУКТУРНЫЕ ПРИЗНАКИ РАБОТАЮТ НА ВСЁМ КАНАЛЕ (n>=10 в группах)')
print('='*120)
tf = pd.read_pickle(os.path.join(OUT,'text_feats.pkl'))
M = both.merge(tf, on='oid', how='inner', suffixes=('','_tf'))
print('склеено:', M.shape)
M['bin_sent'] = pd.cut(M['слов_в_предложении_мед'], [0,10,13,16,100], labels=['<=10','10-13','13-16','>16'])
g = M.groupby('bin_sent', observed=True).agg(n=('oid','size'), rr=('read_rate','median'), ctr=('ctr','median'), reads=('reads','median'), w=('n_words','median'))
print('дочитываемость по медианной длине предложения (все 620):'); print(g.to_string())
MB = M[M['эпоха']=='3_дно']
g2 = MB.groupby('bin_sent', observed=True).agg(n=('oid','size'), rr=('read_rate','median'), ctr=('ctr','median'), reads=('reads','median'))
print('то же, только дно:'); print(g2.to_string())
print()
print('длина предложения у 10 выпусков рубрики: медиана %.1f (размах %.1f-%.1f) -> все в полосе «13-16/>16»'
      % (V['слов_в_предложении_мед'].median(), V['слов_в_предложении_мед'].min(), V['слов_в_предложении_мед'].max()))
print()
print('--- проверка: полоса 1 500-2 700 слов на канале (нужна для сноски «частично механическое») ---')
band = both[(both['n_words']>=1500)&(both['n_words']<2700)]
print('n = %d ; из них рубрика = %d ; не рубрика = %d -> сравнение внутри полосы невозможно (правило 2)'
      % (len(band), band['title_studio'].str.startswith('Светская жизнь').sum(), (~band['title_studio'].str.startswith('Светская жизнь')).sum()))
print()
print('--- нормо-формат канала 505-917 слов (пять светских статей досье) ---')
norm = base[(base['n_words']>=505)&(base['n_words']<=917)]
print('в дне без рубрики: n=%d ; медCTR %.4f ; медДочитываемость %.4f ; медДочит %.0f'
      % (len(norm), norm['ctr'].median(), norm['read_rate'].median(), norm['reads'].median()))
norm2 = both[(both['n_words']>=505)&(both['n_words']<=917)]
print('во всех 620: n=%d ; медCTR %.4f ; медДочитываемость %.4f ; медДочит %.0f'
      % (len(norm2), norm2['ctr'].median(), norm2['read_rate'].median(), norm2['reads'].median()))
print('размах дочитываемости в этой полосе (дно): %.3f - %.3f ; доля статей с дочитываемостью 51-68%%: %.1f%%'
      % (norm['read_rate'].min(), norm['read_rate'].max(), 100*((norm['read_rate']>=0.51)&(norm['read_rate']<=0.68)).mean()))
