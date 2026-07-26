# -*- coding: utf-8 -*-
"""R1 + R3 + R8: воронка на медианах, бенчмарки в срезах, три числа решения."""
import pandas as pd, numpy as np, os, math, json
np.random.seed(20260726)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 500)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
full = pd.read_pickle(os.path.join(OUT,'full.pkl'))
ves  = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
V = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date').reset_index(drop=True)
V['num'] = np.arange(1, len(V)+1)
assert len(V)==10

def med(x): return float(np.median(np.asarray(x, dtype=float)))
def q(x,p): return float(np.percentile(np.asarray(x,dtype=float), p))

def boot_med(x, B=20000):
    x = np.asarray(x, dtype=float); n=len(x)
    idx = np.random.randint(0, n, size=(B,n))
    m = np.median(x[idx], axis=1)
    return med(x), np.percentile(m,2.5), np.percentile(m,97.5)

print('='*110)
print('R1-A. РЯДЫ РУБРИКИ, ОТСОРТИРОВАННЫЕ, И ПОЗИЦИЯ ЗНАЧЕНИЙ ДОСЬЕ')
print('='*110)
cols = {'shows':'Показы','opens':'Открытия','reads':'Дочитывания','ctr':'CTR','read_rate':'Дочитываемость',
        'n_words':'Слов','comments':'Комментариев','min_per_read':'Минут на дочитывание',
        'n_images':'Картинок','подзаголовков':'Подзаголовков'}
dossier = {'shows':63774,'opens':595,'reads':148,'ctr':0.0106,'read_rate':0.244,'n_words':1867,
           'comments':None,'min_per_read':1.36,'n_images':5,'подзаголовков':0}
rows=[]
for c,ru in cols.items():
    s = np.sort(V[c].astype(float).values)
    m, lo, hi = boot_med(V[c].values)
    dv = dossier.get(c)
    pos = ''
    if dv is not None:
        # позиция значения досье в отсортированном ряду (1-based), если оно есть
        hit = [i+1 for i,x in enumerate(s) if abs(x-dv) < (1e-9 if c not in ('ctr','read_rate') else 5e-4)]
        pos = ('%s-е знач.' % hit[0]) if hit else 'НЕТ В ДАННЫХ'
    rows.append({'показатель':ru,'ряд':', '.join(('%.4f'%x if c in ('ctr','read_rate','min_per_read') else '%d'%x) for x in s),
                 'медиана':m,'boot95_lo':lo,'boot95_hi':hi,'в досье':dv,'позиция значения досье':pos})
t = pd.DataFrame(rows)
print(t.to_string(index=False))
print()
print('среднее дочитываемости    = %.5f' % V['read_rate'].mean())
print('агрегат дочитываемости    = %.5f (сумма дочит / сумма открытий = %d/%d)' % (V['reads'].sum()/V['opens'].sum(), V['reads'].sum(), V['opens'].sum()))
print('агрегат CTR               = %.5f (%d/%d)' % (V['opens'].sum()/V['shows'].sum(), V['opens'].sum(), V['shows'].sum()))
print('среднее слов              = %.1f' % V['n_words'].mean())
print('среднее показов           = %.1f' % V['shows'].mean())

print()
print('='*110)
print('R3-A. РАСШИФРОВКА ОТБОРА 623 / 620 / 202')
print('='*110)
print('всего строк в full.pkl (= лист «Статьи» выгрузки): %d' % len(full))
print('  из них src=="both" (сошлись с публичной карточкой, есть текст): %d' % (full['src']=='both').sum())
print('  из них src=="left_only" (только Студия, нет текста/карточки): %d' % (full['src']=='left_only').sum())
lo = full[full['src']=='left_only']
print(lo[['date','title_studio','shows','opens','reads','эпоха']].to_string())
print()
print('эпоха 3_дно (с 01.11.2025): n = %d' % (full['эпоха']=='3_дно').sum())
d3 = full[full['эпоха']=='3_дно']
print('  из них src both      : %d' % (d3['src']=='both').sum())
print('  из них рубрика       : %d' % d3['title_studio'].str.startswith('Светская жизнь Петербурга').sum())
print('  дно ∩ both ∩ не рубрика = %d   <-- это и есть «202»' % len(d3[(d3['src']=='both') & ~d3['title_studio'].str.startswith('Светская жизнь Петербурга')]))
print('  дно ∩ не рубрика (включая left_only) = %d' % len(d3[~d3['title_studio'].str.startswith('Светская жизнь Петербурга')]))
base202 = d3[(d3['src']=='both') & ~d3['title_studio'].str.startswith('Светская жизнь Петербурга')].copy()
print('  период базы 202: %s .. %s' % (base202['date'].min().date(), base202['date'].max().date()))
print('  медианы базы 202: показы %.0f | открытия %.0f | дочит %.0f | CTR %.4f | дочитываемость %.4f | слов %.0f | мин/дочит %.3f | картинок %.0f | подзаг %.0f'
      % (med(base202['shows']), med(base202['opens']), med(base202['reads']), med(base202['ctr']),
         med(base202['read_rate']), med(base202['n_words']), med(base202['min_per_read']),
         med(base202['n_images']), med(base202['n_headers'])))
print('  комм/100 дочит (медиана по статьям) = %.2f ; агрегат = %.2f'
      % (100*med(base202['comments']/base202['reads'].clip(lower=1)), 100*base202['comments'].sum()/base202['reads'].sum()))

print()
print('='*110)
print('R1-B. ВОРОНКА РУБРИКИ ПРОТИВ БАЗЫ 202 — СТРОГО НА МЕДИАНАХ')
print('='*110)
def line(name, vv, bb, kind='num'):
    mv, lov, hiv = boot_med(vv); mb = med(bb)
    ratio = mv/mb if mb else np.nan
    return {'показатель':name,'рубрика (n=10)':mv,'boot95 рубрики':'[%.4g; %.4g]'%(lov,hiv),
            'база 202':mb,'рубрика/база':ratio,'разрыв':('выше в %.2f×'%ratio) if ratio>=1 else ('ниже в %.2f×'%(1/ratio))}
L=[]
L.append(line('Показы', V['shows'], base202['shows']))
L.append(line('Открытия', V['opens'], base202['opens']))
L.append(line('CTR', V['ctr'], base202['ctr']))
L.append(line('Дочитывания', V['reads'], base202['reads']))
L.append(line('Дочитываемость', V['read_rate'], base202['read_rate']))
L.append(line('Слов', V['n_words'], base202['n_words']))
L.append(line('Подзаголовков', V['n_headers'], base202['n_headers']))
L.append(line('Картинок', V['n_images'], base202['n_images']))
L.append(line('Минут на дочитывание', V['min_per_read'], base202['min_per_read']))
L.append(line('Комментариев (абс.)', V['comments'], base202['comments']))
print(pd.DataFrame(L).to_string(index=False))

print()
print('--- ПРОВЕРКА НЕСХОДИМОСТИ ВОРОНКИ (произведение медиан != медиана произведения) ---')
ms, mc, mr, mrd = med(V['shows']), med(V['ctr']), med(V['read_rate']), med(V['reads'])
print('произведение медиан рубрики : %.1f × %.6f × %.6f = %.2f' % (ms, mc, mr, ms*mc*mr))
print('медиана дочитываний рубрики : %.1f' % mrd)
print('расхождение                 : %+.2f дочитывания (%.1f%% от медианы)' % (ms*mc*mr-mrd, 100*(ms*mc*mr-mrd)/mrd))
bs, bc, br, brd = med(base202['shows']), med(base202['ctr']), med(base202['read_rate']), med(base202['reads'])
print('произведение медиан базы202 : %.1f × %.6f × %.6f = %.2f ; медиана дочитываний базы = %.1f (расхождение %+.1f)'
      % (bs, bc, br, bs*bc*br, brd, bs*bc*br-brd))

print()
print('--- ЛОГ-РАСКЛАДКА ДЕФИЦИТА ДОЧИТЫВАНИЙ (2 члена: CTR и дочитываемость) ---')
lc = math.log(bc/mc); lr = math.log(br/mr); tot = lc+lr
print('ln(CTR база/рубрика)            = ln(%.6f/%.6f) = ln(%.4f) = %.4f' % (bc, mc, bc/mc, lc))
print('ln(дочитываемость база/рубрика) = ln(%.6f/%.6f) = ln(%.4f) = %.4f' % (br, mr, br/mr, lr))
print('сумма = %.4f  ->  доля CTR = %.1f%% ; доля дочитываемости = %.1f%%' % (tot, 100*lc/tot, 100*lr/tot))
print('exp(сумма) = %.3f× — это разрыв «если бы воронка сходилась»' % math.exp(tot))
print('ФАКТИЧЕСКИЙ разрыв по первичному показателю: %.1f / %.1f = %.3f×  (ln = %.4f)' % (brd, mrd, brd/mrd, math.log(brd/mrd)))
ls = math.log(bs/ms)
print()
print('--- ЛОГ-РАСКЛАДКА С ТРЕМЯ ЧЛЕНАМИ (включая показы) ---')
print('ln(показы база/рубрика)         = ln(%.4f) = %+.4f  (в пользу рубрики)' % (bs/ms, ls))
print('сумма трёх = %.4f ; exp = %.3f× ; медианный разрыв дочитываний %.3f× ; невязка %+.4f в логах'
      % (ls+lc+lr, math.exp(ls+lc+lr), brd/mrd, math.log(brd/mrd)-(ls+lc+lr)))

# бутстрап отношений медиан
def boot_ratio(a, b, B=20000):
    a=np.asarray(a,float); b=np.asarray(b,float)
    ia=np.random.randint(0,len(a),(B,len(a))); ib=np.random.randint(0,len(b),(B,len(b)))
    r=np.median(b[ib],axis=1)/np.median(a[ia],axis=1)
    return np.percentile(r,2.5), np.percentile(r,97.5)
print()
print('--- БУТСТРАП 95%% CI ОТНОШЕНИЙ база/рубрика (B=20000) ---')
for nm, a, b in [('CTR', V['ctr'], base202['ctr']), ('Дочитываемость', V['read_rate'], base202['read_rate']),
                 ('Дочитывания', V['reads'], base202['reads'])]:
    lo_, hi_ = boot_ratio(a, b)
    print('  %-16s точечно %.2f×   CI [%.2f; %.2f]' % (nm, med(b)/med(a), lo_, hi_))
# доля CTR в логах с бутстрапом
B=20000
ia=np.random.randint(0,10,(B,10)); ib=np.random.randint(0,len(base202),(B,len(base202)))
vc_=V['ctr'].values; vr_=V['read_rate'].values; bc_=base202['ctr'].values; br_=base202['read_rate'].values
lcb=np.log(np.median(bc_[ib],axis=1)/np.median(vc_[ia],axis=1))
lrb=np.log(np.median(br_[ib],axis=1)/np.median(vr_[ia],axis=1))
sh=lcb/(lcb+lrb)
print('  доля CTR в логах: точечно %.1f%%  бутстрап CI [%.1f%%; %.1f%%]' % (100*lc/tot, 100*np.percentile(sh,2.5), 100*np.percentile(sh,97.5)))

print()
print('='*110)
print('R3-B. БЕНЧМАРК В ДВУХ СРЕЗАХ')
print('='*110)
isv = full['title_studio'].str.startswith('Светская жизнь Петербурга')
sliceA = full[(full['date']>=pd.Timestamp('2026-05-18')) & (full['date']<=pd.Timestamp('2026-07-26 23:59:59')) & (~isv)]
sliceB = full[(full['shows']>=50000) & (full['shows']<=90000) & (~isv)]
sliceB_bottom = sliceB[sliceB['эпоха']=='3_дно']
sliceAB = full[(full['date']>=pd.Timestamp('2026-05-18')) & (~isv) & (full['shows']>=50000) & (full['shows']<=90000)]
def desc(nm, d):
    if len(d)==0:
        print('%-46s n=0' % nm); return
    print('%-46s n=%3d | медCTR %.4f (%.2f%%) | медДочитываемость %.4f (%.2f%%) | медДочитывания %8.1f | медПоказы %9.0f | медСлов %5.0f'
          % (nm, len(d), med(d['ctr']), 100*med(d['ctr']), med(d['read_rate']), 100*med(d['read_rate']),
             med(d['reads']), med(d['shows']), med(d['n_words'])))
desc('(а) 18.05-26.07.2026 без рубрики', sliceA)
desc('(б) показы 50-90 тыс., вся история, без рубрики', sliceB)
desc('(б-дно) показы 50-90 тыс., только дно', sliceB_bottom)
desc('(а∩б) 18.05-26.07 И показы 50-90 тыс.', sliceAB)
desc('база 202 (дно, без рубрики)', base202)
desc('РУБРИКА (10 выпусков)', V)
print()
print('состав среза (б) показы 50-90 тыс. без рубрики:')
print(sliceB[['date','title_studio','shows','opens','reads','ctr','read_rate','n_words','эпоха']].sort_values('shows').to_string())
print()
print('состав среза (а∩б):')
print(sliceAB[['date','title_studio','shows','opens','reads','ctr','read_rate','n_words']].sort_values('shows').to_string())

print()
print('--- пересчёт разрывов по каждому срезу ---')
for nm, d in [('(а) период 18.05-26.07', sliceA), ('(б) полоса 50-90k', sliceB), ('(б-дно) полоса 50-90k, дно', sliceB_bottom),
              ('(а∩б)', sliceAB), ('база 202', base202)]:
    if len(d)==0: continue
    c_, r_, rd_ = med(d['ctr']), med(d['read_rate']), med(d['reads'])
    lc_ = math.log(c_/mc); lr_ = math.log(r_/mr); t_=lc_+lr_
    print('%-28s n=%3d | CTR разрыв %5.2f× | дочитываемость %5.2f× | дочитывания %6.2f× | доля CTR в логах %5.1f%%'
          % (nm, len(d), c_/mc, r_/mr, rd_/mrd, 100*lc_/t_))

print()
print('--- rho(показы, дочитываемость) и rho(показы, дочитывания) в базах ---')
from scipy import stats
for nm, d in [('вся история 620', full[full['src']=='both']), ('дно 202', base202), ('срез (а)', sliceA), ('рубрика 10', V)]:
    a = stats.spearmanr(d['shows'], d['read_rate']); b = stats.spearmanr(d['shows'], d['reads']); c2 = stats.spearmanr(d['shows'], d['ctr'])
    print('%-18s n=%3d | rho(показы,дочитываемость)=%+.3f p=%.4g | rho(показы,дочитывания)=%+.3f p=%.3g | rho(показы,CTR)=%+.3f p=%.3g'
          % (nm, len(d), a.statistic, a.pvalue, b.statistic, b.pvalue, c2.statistic, c2.pvalue))

print()
print('='*110)
print('R8. ТРИ ЧИСЛА РЕШЕНИЯ')
print('='*110)
SH = med(V['shows']); CT = med(V['ctr'])
print('(а) ПОТОЛОК ФОРМАТНОЙ ПРОГРАММЫ при неизменном CTR = %.1f × %.6f = %.2f открытий' % (SH, CT, SH*CT))
for rr in [med(V['read_rate']), 0.361, 0.45, 0.53]:
    print('     дочитываемость %5.2f%% -> %6.1f дочитываний  (%.1f%% от медианы канала %s)'
          % (100*rr, SH*CT*rr, 100*SH*CT*rr/brd, ('%.0f'%brd)))
print('     медиана канала (база 202) = %.0f дочитываний; половина = %.0f' % (brd, brd/2))
print()
print('(б) ТРЕБУЕМЫЙ CTR для выхода на %.0f дочитываний:' % brd)
for rr in [0.30, 0.361, 0.40, 0.45, 0.53]:
    need = brd/(SH*rr)
    print('     при дочитываемости %5.2f%%: CTR = %.0f/(%.1f×%.4f) = %.4f (%.2f%%) = %.2f× текущего %.2f%%'
          % (100*rr, brd, SH, rr, need, 100*need, need/CT, 100*CT))
print()
print('(в) АЛЬТЕРНАТИВНАЯ СТОИМОСТЬ РУБРИКИ')
print('     фактические дочитывания 10 выпусков = %d' % V['reads'].sum())
print('     10 × медиана канала (база 202)      = 10 × %.0f = %.0f' % (brd, 10*brd))
print('     упущено                             = %.0f' % (10*brd - V['reads'].sum()))
print('     10 × медиана среза (а)              = 10 × %.0f = %.0f ; упущено %.0f' % (med(sliceA['reads']), 10*med(sliceA['reads']), 10*med(sliceA['reads'])-V['reads'].sum()))
print('     10 × медиана среза (б)              = 10 × %.0f = %.0f ; упущено %.0f' % (med(sliceB['reads']), 10*med(sliceB['reads']), 10*med(sliceB['reads'])-V['reads'].sum()))
lo_,hi_ = np.percentile(np.median(base202['reads'].values[np.random.randint(0,len(base202),(20000,len(base202)))],axis=1),[2.5,97.5])
print('     бутстрап CI медианы дочитываний базы 202: [%.0f; %.0f] -> упущено [%.0f; %.0f]' % (lo_,hi_,10*lo_-V['reads'].sum(),10*hi_-V['reads'].sum()))
print()
print('--- пять «светских» коротких статей из досье: проверка ---')
names = ['Ошибки, которые сразу выдают','Темы для светских бесед','Дама здоровается первая','5 ice breakers','Как превратить культурный выход']
for n_ in names:
    r = full[full['title_studio'].str.contains(n_, regex=False)]
    for _, x in r.iterrows():
        print('  %-62s %s слов=%4.0f показы=%9d открытия=%7d дочит=%7d CTR=%.4f дочитываемость=%.4f' %
              (x['title_studio'][:62], x['date'].date(), x['n_words'], x['shows'], x['opens'], x['reads'], x['ctr'], x['read_rate']))
print()
print('--- канал: дочитываемость по полосам объёма (все 620, дно 202) ---')
for nm, d in [('все 620', full[full['src']=='both']), ('дно 202', base202)]:
    bins = [0,600,900,1200,1500,2700,100000]
    lab = ['<600','600-899','900-1199','1200-1499','1500-2699','2700+']
    d = d.copy(); d['bin'] = pd.cut(d['n_words'], bins=bins, labels=lab, right=False)
    g = d.groupby('bin', observed=True).agg(n=('oid','size'), rr=('read_rate','median'), ctr=('ctr','median'), reads=('reads','median'))
    print(nm); print(g.to_string())
