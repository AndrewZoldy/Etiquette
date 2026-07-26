# -*- coding: utf-8 -*-
"""R2: разведение длины и календаря. Попарные и частные rho, LOO, точные перестановки, мощность, VIF."""
import pandas as pd, numpy as np, os, math, itertools
from scipy import stats
np.random.seed(20260726)
pd.set_option('display.width', 320); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 500)
OUT = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out'
ves = pd.read_pickle(os.path.join(OUT,'vestnik.pkl'))
V = ves[ves['title_studio'].str.startswith('Светская жизнь Петербурга')].sort_values('date').reset_index(drop=True)
V['num'] = np.arange(1, 11)
V['days'] = (V['date'] - V['date'].iloc[0]).dt.total_seconds()/86400.0

CAND = {'слов':'n_words', 'номер выпуска':'num', 'показы':'shows'}
OUTC = {'дочитываемость':'read_rate', 'дочитывания':'reads', 'CTR':'ctr'}
n = len(V)

# ---------- точное распределение Spearman rho при n=10 (перечисление 10! перестановок) ----------
print('строю точное нулевое распределение Spearman для n=10 (10! = 3 628 800 перестановок)...', flush=True)
perms = np.array(list(itertools.permutations(range(1, n+1))), dtype=np.int16)
base = np.arange(1, n+1, dtype=np.int16)
d2 = ((perms - base)**2).sum(axis=1)
rho_null = 1.0 - 6.0*d2/(n*(n*n-1))
rho_null_abs = np.sort(np.abs(rho_null))
def exact_p(r):
    """точный двусторонний p = доля перестановок с |rho| >= |r|"""
    return float((rho_null_abs >= abs(r) - 1e-12).sum()) / len(rho_null_abs)
# критическое значение alpha=0.05 двустороннее
k = int(np.floor(0.05*len(rho_null_abs)))
crit = rho_null_abs[len(rho_null_abs)-k]
print('точное критическое |rho| при alpha=0.05 (n=10): %.4f   (в требовании 0,648)' % crit)
print('проверка: p(|rho|>=0.6485) = %.5f ; p(|rho|>=0.6364) = %.5f' % (exact_p(0.6485), exact_p(0.63636)))
print()

R = lambda a, b: stats.spearmanr(V[a], V[b]).statistic
def rk(c): return stats.rankdata(V[c].values)

print('='*118)
print('R2-A. ПОПАРНЫЕ SPEARMAN rho, ВСЕ ТРИ КАНДИДАТА × ВСЕ ТРИ ИСХОДА (n=10), p — ТОЧНЫЙ ПЕРЕСТАНОВОЧНЫЙ')
print('='*118)
rows=[]
for cn, cc in CAND.items():
    for on, oc in OUTC.items():
        r = R(cc, oc)
        rows.append({'кандидат':cn,'исход':on,'rho':r,'|rho|':abs(r),'точный p':exact_p(r),
                     'значим при 0,648':'ДА' if abs(r)>=0.6485 else 'нет'})
print(pd.DataFrame(rows).to_string(index=False))
print()
print('--- корреляции между кандидатами (конфаунд) ---')
for a,b in itertools.combinations(CAND.items(),2):
    r = R(a[1], b[1])
    print('  rho(%s, %s) = %+.4f   точный p = %.5f   %s' % (a[0], b[0], r, exact_p(r), 'ЗНАЧИМО' if abs(r)>=0.6485 else ''))
print()
print('--- сырые ряды ---')
print(V[['date','title_studio','num','n_words','shows','opens','reads','ctr','read_rate']].to_string(index=False))

# ---------- частные корреляции на рангах ----------
def partial(xc, yc, zc):
    rxy, rxz, ryz = R(xc,yc), R(xc,zc), R(yc,zc)
    return (rxy - rxz*ryz)/math.sqrt((1-rxz**2)*(1-ryz**2)), rxy, rxz, ryz

print()
print('='*118)
print('R2-B. ЧАСТНЫЕ SPEARMAN rho: каждый кандидат при контроле каждого другого')
print('='*118)
rows=[]
for on, oc in OUTC.items():
    for (an,ac),(bn,bc) in itertools.permutations(CAND.items(), 2):
        pr, rxy, rxz, ryz = partial(ac, oc, bc)
        # p по t-критерию с df = n-3
        df = n-3
        t = pr*math.sqrt(df/(1-pr**2)) if abs(pr)<1 else np.inf
        p = 2*(1-stats.t.cdf(abs(t), df))
        rows.append({'исход':on,'кандидат':an,'контроль':bn,'сырой rho':rxy,'частный rho':pr,
                     '|частный|':abs(pr),'p (t, df=7)':p,'значим при 0,666':'ДА' if abs(pr)>=0.666 else 'нет',
                     'потеря |rho|':abs(rxy)-abs(pr)})
P = pd.DataFrame(rows)
print(P.to_string(index=False))
print()
print('--- КЛЮЧЕВАЯ ПАРА: длина против календаря внутри дочитываемости ---')
key = P[(P['исход']=='дочитываемость') & (P['кандидат'].isin(['слов','номер выпуска'])) & (P['контроль'].isin(['слов','номер выпуска']))]
print(key.to_string(index=False))
print()
print('--- частная при контроле ДВУХ переменных (слов | номер + показы) — регрессия на рангах ---')
def partial2(xc, yc, z1, z2):
    Xr = np.column_stack([rk(z1), rk(z2), np.ones(n)])
    ex = rk(xc) - Xr @ np.linalg.lstsq(Xr, rk(xc), rcond=None)[0]
    ey = rk(yc) - Xr @ np.linalg.lstsq(Xr, rk(yc), rcond=None)[0]
    return stats.pearsonr(ex, ey).statistic
for on, oc in OUTC.items():
    a = partial2('n_words', oc, 'num', 'shows'); b = partial2('num', oc, 'n_words', 'shows'); c = partial2('shows', oc, 'num', 'n_words')
    print('  %-16s частная слов|(номер,показы) = %+.4f ; номер|(слов,показы) = %+.4f ; показы|(номер,слов) = %+.4f  (порог df=6: 0,707)'
          % (on, a, b, c))

# ---------- LOO джекнайф ----------
print()
print('='*118)
print('R2-C. LOO-ДЖЕКНАЙФ ПО КАЖДОМУ ВЫПУСКУ (n=9 в каждой строке; порог значимости при n=9 — 0,683)')
print('='*118)
crit9 = None
perms9 = np.array(list(itertools.permutations(range(1,10))), dtype=np.int16)
base9 = np.arange(1,10,dtype=np.int16)
rn9 = np.sort(np.abs(1.0-6.0*((perms9-base9)**2).sum(axis=1)/(9*80)))
k9 = int(np.floor(0.05*len(rn9))); crit9 = rn9[len(rn9)-k9]
print('точное критическое |rho| при n=9, alpha=0.05: %.4f' % crit9)
def loo_table(xc, yc, zc=None, lbl=''):
    out=[]
    for i in range(n):
        W = V.drop(index=i)
        if zc is None:
            r = stats.spearmanr(W[xc], W[yc]).statistic
            out.append(r)
        else:
            rxy = stats.spearmanr(W[xc],W[yc]).statistic; rxz = stats.spearmanr(W[xc],W[zc]).statistic; ryz = stats.spearmanr(W[yc],W[zc]).statistic
            out.append((rxy-rxz*ryz)/math.sqrt((1-rxz**2)*(1-ryz**2)))
    return np.array(out)

specs = [('rho(слов, дочитываемость)','n_words','read_rate',None),
         ('rho(номер, дочитываемость)','num','read_rate',None),
         ('rho(показы, дочитываемость)','shows','read_rate',None),
         ('rho(номер, слов)','num','n_words',None),
         ('rho(слов, дочитывания)','n_words','reads',None),
         ('rho(номер, дочитывания)','num','reads',None),
         ('rho(показы, дочитывания)','shows','reads',None),
         ('rho(слов, CTR)','n_words','ctr',None),
         ('rho(номер, CTR)','num','ctr',None),
         ('rho(показы, CTR)','shows','ctr',None),
         ('частн. слов|номер -> дочитываемость','n_words','read_rate','num'),
         ('частн. номер|слов -> дочитываемость','num','read_rate','n_words'),
         ('частн. слов|номер -> дочитывания','n_words','reads','num'),
         ('частн. номер|слов -> дочитывания','num','reads','n_words'),
         ('частн. слов|номер -> CTR','n_words','ctr','num'),
         ('частн. номер|слов -> CTR','num','ctr','n_words')]
res=[]
labels = ['без %s' % t.replace('Светская жизнь Петербурга: ','') for t in V['title_studio']]
for lbl, xc, yc, zc in specs:
    arr = loo_table(xc, yc, zc)
    full_r = (stats.spearmanr(V[xc],V[yc]).statistic if zc is None else partial(xc,yc,zc)[0])
    d = {'величина':lbl,'на всех 10':full_r,'LOO min':arr.min(),'LOO max':arr.max(),
         'меняет знак':'ДА' if (arr.min()<0)!=(arr.max()<0) else 'нет',
         'LOO>порога всегда':'ДА' if np.all(np.abs(arr)>= (crit9 if zc is None else 0.707)) else 'нет'}
    for j,l in enumerate(labels): d[l]=arr[j]
    res.append(d)
LO = pd.DataFrame(res)
print(LO[['величина','на всех 10','LOO min','LOO max','меняет знак','LOO>порога всегда']].to_string(index=False))
print()
print('--- полная LOO-матрица (столбец = какой выпуск выброшен) ---')
print(LO.set_index('величина')[labels].round(3).to_string())

# ---------- VIF, раздутие SE ----------
print()
print('='*118)
print('R2-D. КОЛЛИНЕАРНОСТЬ, VIF, РАЗДУТИЕ SE, МОЩНОСТЬ')
print('='*118)
r_wn = R('n_words','num')
print('rho(слов, номер) = %+.4f -> R2 = %.4f' % (r_wn, r_wn**2))
print('VIF = 1/(1-R2) = %.3f ; раздутие SE = sqrt(VIF) = %.3f' % (1/(1-r_wn**2), math.sqrt(1/(1-r_wn**2))))
r_ws = R('n_words','shows'); r_ns = R('num','shows')
print('rho(слов, показы) = %+.4f ; rho(номер, показы) = %+.4f' % (r_ws, r_ns))
Xr = np.column_stack([rk('num'), rk('shows'), np.ones(n)])
b = np.linalg.lstsq(Xr, rk('n_words'), rcond=None)[0]
r2_full = 1 - ((rk('n_words') - Xr@b)**2).sum()/((rk('n_words')-rk('n_words').mean())**2).sum()
print('R2(слов ~ номер + показы) на рангах = %.4f -> VIF = %.3f ; раздутие SE = %.3f' % (r2_full, 1/(1-r2_full), math.sqrt(1/(1-r2_full))))
print()
za = stats.norm.ppf(0.975)
def need_n(r, power=0.8, ncov=1):
    zb = stats.norm.ppf(power); zr = math.atanh(r)
    return (za+zb)**2/zr**2 + 2 + ncov
print('требуемый n для мощности 0,80 (alpha=0,05 двустор.), частная корреляция с 1 контролем:')
for r in [0.2,0.3,0.4,0.5,0.6,0.7,0.8]:
    print('   r = %.1f -> n = %5.1f  (округляя вверх: %d)' % (r, need_n(r), math.ceil(need_n(r))))
def power_at(r, nn, ncov=1):
    if r==0: return 0.05
    zr = math.atanh(r)*math.sqrt(nn-3-ncov+1)
    return float(stats.norm.cdf(zr-za) + stats.norm.cdf(-zr-za))
print()
print('фактическая мощность при n=10 (df=7):')
for r in [0.102, 0.20, 0.30, 0.469, 0.50, 0.666, 0.745, 0.806, 0.891]:
    print('   |r| = %.3f -> мощность %.3f' % (r, power_at(r, 10)))
print()
print('минимальный обнаружимый |частный r| при n=10 и мощности 0,80: ', end='')
lo_,hi_=0.01,0.999
for _ in range(60):
    mid=(lo_+hi_)/2
    if power_at(mid,10) < 0.8: lo_=mid
    else: hi_=mid
print('%.3f' % hi_)

# ---------- бутстрап частных ----------
print()
print('--- бутстрап (B=20000) частных rho внутри дочитываемости ---')
B=20000; idx=np.random.randint(0,n,(B,n))
def sp(a,b):
    ra=stats.rankdata(a,axis=1); rb=stats.rankdata(b,axis=1)
    ra=ra-ra.mean(axis=1,keepdims=True); rb=rb-rb.mean(axis=1,keepdims=True)
    return (ra*rb).sum(axis=1)/np.sqrt((ra**2).sum(axis=1)*(rb**2).sum(axis=1))
W_=V['n_words'].values[idx]; N_=V['num'].values[idx]; RR_=V['read_rate'].values[idx]; RD_=V['reads'].values[idx]
rxy=sp(W_,RR_); rxz=sp(W_,N_); ryz=sp(RR_,N_)
pw=(rxy-rxz*ryz)/np.sqrt(np.clip((1-rxz**2)*(1-ryz**2),1e-12,None))
rxy2=sp(N_,RR_); rxz2=sp(N_,W_); ryz2=sp(RR_,W_)
pn=(rxy2-rxz2*ryz2)/np.sqrt(np.clip((1-rxz2**2)*(1-ryz2**2),1e-12,None))
pw=pw[np.isfinite(pw)]; pn=pn[np.isfinite(pn)]
print('  частная слов|номер : точечно %+.4f  боотстрап CI [%+.3f; %+.3f] ; доля бутстрапов с |r|>=0,666 = %.1f%% ; доля отрицательных = %.1f%%'
      % (partial('n_words','read_rate','num')[0], np.percentile(pw,2.5), np.percentile(pw,97.5), 100*np.mean(np.abs(pw)>=0.666), 100*np.mean(pw<0)))
print('  частная номер|слов : точечно %+.4f  боотстрап CI [%+.3f; %+.3f] ; доля бутстрапов с |r|>=0,666 = %.1f%% ; доля отрицательных = %.1f%%'
      % (partial('num','read_rate','n_words')[0], np.percentile(pn,2.5), np.percentile(pn,97.5), 100*np.mean(np.abs(pn)>=0.666), 100*np.mean(pn<0)))

# ---------- ABAB дизайн: расчёт n ----------
print()
print('='*118)
print('R2-E. ДИЗАЙН ABAB: СКОЛЬКО НЕДЕЛЬ НУЖНО, ЧТОБЫ ДЛИНА СТАЛА ОРТОГОНАЛЬНА КАЛЕНДАРЮ')
print('='*118)
sd = V['read_rate'].std(ddof=1)
print('SD дочитываемости внутри рубрики = %.4f (%.2f п.п.) ; размах %.2f-%.2f п.п.' % (sd, 100*sd, 100*V['read_rate'].min(), 100*V['read_rate'].max()))
print('при чередовании ABAB длина ортогональна номеру по построению (rho(длина,номер)=0), контроль не нужен -> df=n-2')
for delta in [0.03,0.05,0.07,0.10,0.14]:
    d_ = delta/sd
    nn = 2*((stats.norm.ppf(0.975)+stats.norm.ppf(0.8))**2)/(d_**2)
    print('   чтобы поймать разницу %4.1f п.п. дочитываемости (d = %.2f): нужно %5.1f выпусков всего (%.0f недель) при мощности 0,80'
          % (100*delta, d_, 2*math.ceil(nn/2), 2*math.ceil(nn/2)))
print()
print('блочный дизайн «10 новых против 10 исторических»: rho(номер, блок) = 1,00 по построению -> длина и календарь снова')
print('коллинеарны полностью, VIF = бесконечность, частный эффект длины неидентифицируем. Отклоняется.')
