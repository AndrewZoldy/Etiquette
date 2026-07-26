# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
D = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/'
m = pd.read_pickle(D + 'full.pkl')
m['date'] = pd.to_datetime(m['date'])
m['half'] = m['date'].dt.year.astype(str) + np.where(m['date'].dt.month <= 6, 'H1', 'H2')
m['ceT'] = (m['comments_enabled'] == True); m['ceF'] = (m['comments_enabled'] == False)
m['svet'] = m['title_studio'].astype(str).str.startswith('Светская жизнь Петербурга')
m['cl2'] = m['ceT'] & ~m['svet']
m['ym2'] = m['date'].dt.to_period('M').astype(str)
rng = np.random.default_rng(20260726)
def rci(a, b, n=4000):
    a=np.asarray(a,float); b=np.asarray(b,float); r=np.empty(n)
    for i in range(n): r[i]=np.median(rng.choice(a,len(a),True))/max(np.median(rng.choice(b,len(b),True)),1e-9)
    return np.percentile(r,[2.5,97.5])

print('=== Q. Серия ce=False по месяцам vs чистый канал того же месяца ===')
rows=[]
for ym,g in m[m['date']>='2025-09-01'].groupby('ym2'):
    f=g[g['ceF']]; t=g[g['cl2']]
    if len(f)==0: continue
    rows.append(dict(месяц=ym, n_серия=len(f), мед_shows_серия=int(f['shows'].median()), мед_reads_серия=int(f['reads'].median()),
                     n_чист=len(t), мед_shows_чист=int(t['shows'].median()) if len(t) else None,
                     мед_reads_чист=int(t['reads'].median()) if len(t) else None,
                     разрыв_shows=round(t['shows'].median()/f['shows'].median(),1) if len(t) else None))
print(pd.DataFrame(rows).to_string(index=False))
print('-> серия провалена С ПЕРВОГО месяца (сен-окт 2025), когда чистый канал был ещё на 342k/141k показов')

print()
print('=== R. Внутринедельный матчинг серии (+-3 дня, только ce=True контроль) ===')
ct=m[m['cl2']]
res={k:[] for k in ['shows','opens','reads','ctr']}
nm=0
for _,r in m[m['ceF']].iterrows():
    c=ct[(ct['date']>=r['date']-pd.Timedelta(days=3))&(ct['date']<=r['date']+pd.Timedelta(days=3))]
    if len(c)==0: continue
    nm+=1
    for k in res: res[k].append(c[k].median()/max(r[k],1e-9) if r[k]==r[k] and r[k]>0 else np.nan)
print('матчировано', nm, 'из', m['ceF'].sum())
for k,v in res.items():
    v=np.array([x for x in v if x==x])
    ci=np.percentile([np.median(rng.choice(v,len(v),True)) for _ in range(4000)],[2.5,97.5])
    print(f'  {k:6s} медиана внутрипарного отношения={np.median(v):8.2f} CI=[{ci[0]:.2f};{ci[1]:.2f}] доля пар>1={np.mean(v>1):.2f} n={len(v)}')

print()
print('=== S. Подъём 2024H1 -> 2024H2 -> 2025H1: стандартизация состава (двойн. чистка) ===')
def stand(A,B,keys,minn=5,val='reads'):
    A=A.copy();B=B.copy()
    A['c']=A[keys].astype(str).agg('|'.join,axis=1);B['c']=B[keys].astype(str).agg('|'.join,axis=1)
    big=B['c'].value_counts();keep=set(big[big>=minn].index)
    A['c']=np.where(A['c'].isin(keep),A['c'],'ПР');B['c']=np.where(B['c'].isin(keep),B['c'],'ПР')
    pa=A['c'].value_counts(normalize=True);pb=B['c'].value_counts(normalize=True)
    B=B[B['c'].isin(pa.index)];w=B['c'].map(lambda c:pa.get(c,0)/pb.get(c,1e-9)).values
    x=B[val].values.astype(float);o=np.argsort(x);x,w=x[o],w[o];cw=np.cumsum(w);p=(cw-0.5*w)/w.sum()
    return float(np.interp(0.5,p,x)),int((big>=minn).sum())
for a,b in [('2024H1','2024H2'),('2024H2','2025H1'),('2024H1','2025H1')]:
    A=m[m['cl2']&(m['half']==a)];B=m[m['cl2']&(m['half']==b)]
    raw=B['reads'].median()/A['reads'].median()
    r1,k1=stand(B,A,['сцена']); r2,k2=stand(B,A,['сцена','функция','порог_входа'])
    ci=rci(B['reads'].values,A['reads'].values)
    print(f'  {a}->{b}: подъём сырой={raw:6.2f} CI=[{ci[0]:.2f};{ci[1]:.2f}] | A перевзв. к составу B: сцена={B["reads"].median()/r1:6.2f}(k={k1}) тройка={B["reads"].median()/r2:6.2f}(k={k2})')

print()
print('=== T. Раздача на единицу базы: односторонняя граница (валовые подписки = ВЕРХНЯЯ граница базы) ===')
tot=m[['date','subs']].copy()
for f in ['rol.pkl','pos.pkl']:
    x=pd.read_pickle(D+f); x['date']=pd.to_datetime(x['date']); tot=pd.concat([tot,x[['date','subs']]],ignore_index=True)
tot=tot.dropna()
def ub(d): return tot.loc[tot['date']<=d,'subs'].sum()
print('   период        мед.reads(двойн.чистка)   ВЕРХН.гран.базы на начало   reads/база_UB (=НИЖНЯЯ граница отдачи на подписчика)')
for lab,a,b in [('2023H2','2023-07-01','2024-01-01'),('2024H1','2024-01-01','2024-07-01'),('2024H2','2024-07-01','2025-01-01'),
                ('2025H1','2025-01-01','2025-07-01'),('пик май-сен25','2025-05-01','2025-10-01'),('дно ноя25-мар26','2025-11-01','2026-04-01')]:
    s=m[m['cl2']&(m['date']>=a)&(m['date']<b)]
    base=ub(a)
    print(f'   {lab:16s} n={len(s):3d} мед={s["reads"].median():9.0f}   база_UB={int(base):7d}   отдача_LB={s["reads"].median()/base:8.4f}')
print('  ВНИМАНИЕ: база_UB монотонно растёт, поэтому отношение = НИЖНЯЯ граница падения отдачи на подписчика.')
print(f'  Падение отдачи на базу, дно vs 2024H1: не меньше чем {(m[m["cl2"]&(m["half"]=="2024H1")]["reads"].median()/ub("2024-01-01"))/(m[m["cl2"]&(m["date"]>="2025-11-01")&(m["date"]<"2026-04-01")]["reads"].median()/ub("2025-11-01")):.2f}x')

print()
print('=== U. Сумма reads по месяцам: устойчивость (правило 2) — доля топ-2 ===')
g=m[m['date']>='2025-05-01'].groupby('ym2').apply(lambda d: pd.Series({
  'n':len(d),'сумма_млн':round(d['reads'].sum()/1e6,3),
  'доля_топ2':round(d['reads'].nlargest(2).sum()/max(d['reads'].sum(),1),3),
  'сумма_без_топ2_млн':round((d['reads'].sum()-d['reads'].nlargest(2).sum())/1e6,3)}),include_groups=False)
print(g.to_string())
