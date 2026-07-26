# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
D = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/'
m = pd.read_pickle(D + 'full.pkl')
m['date'] = pd.to_datetime(m['date'])
m['ceT'] = (m['comments_enabled'] == True); m['ceF'] = (m['comments_enabled'] == False)
m['svet'] = m['title_studio'].astype(str).str.startswith('Светская жизнь Петербурга')
m['cl2'] = m['ceT'] & ~m['svet']
rng = np.random.default_rng(20260726)
def rci(a,b,n=4000):
    a=np.asarray(a,float);b=np.asarray(b,float);r=np.empty(n)
    for i in range(n): r[i]=np.median(rng.choice(a,len(a),True))/max(np.median(rng.choice(b,len(b),True)),1e-9)
    return np.percentile(r,[2.5,97.5])

print('=== V. Серия: ранняя фаза vs поздняя (пулы n>=10, правило 3) ===')
ph = [('сен16-окт31 2025','2025-09-16','2025-11-01'), ('ноя2025-мар2026','2025-11-01','2026-04-01'), ('апр-май2026','2026-04-01','2026-05-22')]
ct = m[m['cl2']]
for lab,a,b in ph:
    f = m[m['ceF'] & (m['date']>=a) & (m['date']<b)]
    c = ct[(ct['date']>=a) & (ct['date']<b)]
    # внутринедельные отношения
    rr=[]
    for _,r in f.iterrows():
        cc=ct[(ct['date']>=r['date']-pd.Timedelta(days=3))&(ct['date']<=r['date']+pd.Timedelta(days=3))]
        if len(cc) and r['reads']>0: rr.append(cc['reads'].median()/r['reads'])
    ok = 'ДА' if len(f)>=10 else 'n<10 — вывод не формулируется'
    print(f'  {lab:18s} n_серия={len(f):2d} мед_shows={f["shows"].median():8.0f} мед_reads={f["reads"].median():7.0f} '
          f'| n_чист={len(c):3d} мед_reads={c["reads"].median():7.0f} | внутринед.разрыв_reads(медиана)={np.median(rr) if rr else float("nan"):8.1f} | правило3: {ok}')
f_early = m[m['ceF'] & (m['date']<'2025-11-01')]; f_late = m[m['ceF'] & (m['date']>='2025-11-01')]
print(f'  пул ранний n={len(f_early)} (правило 3: n<10 => НЕ формулируем) поздний n={len(f_late)}')
print(f'  сен+окт (n={len(f_early)}) мед_shows={f_early["shows"].median():.0f} vs ноя+ (n={len(f_late)}) мед_shows={f_late["shows"].median():.0f}')

print()
print('=== W. Ступень по ПОКАЗАМ, двойная чистка, стыки 3/3 ===')
for cut in pd.period_range('2025-08','2026-05',freq='M'):
    c=cut.to_timestamp()
    a=m[m['cl2']&(m['date']>=c-pd.DateOffset(months=3))&(m['date']<c)]['shows']
    b=m[m['cl2']&(m['date']>=c)&(m['date']<c+pd.DateOffset(months=3))]['shows']
    if len(a)<10 or len(b)<10: continue
    ci=rci(a.values,b.values)
    print(f'  {cut}: n={len(a)}/{len(b)} отн={a.median()/b.median():6.2f} CI=[{ci[0]:5.2f};{ci[1]:7.2f}]{"  <== искл. 1" if ci[0]>1 else ""}')

print()
print('=== X. Отдача на базу с поправкой на максимальный отток (фактор <=1.199) ===')
tot=m[['date','subs']].copy()
for fl in ['rol.pkl','pos.pkl']:
    x=pd.read_pickle(D+fl); x['date']=pd.to_datetime(x['date']); tot=pd.concat([tot,x[['date','subs']]],ignore_index=True)
tot=tot.dropna()
gross_all=tot['subs'].sum(); cur=88465
print(f'валовые подписки всего={int(gross_all)}, текущая база={cur} => макс. накопленный отток={1-cur/gross_all:.1%}, фактор завышения базы<= {gross_all/cur:.3f}')
def ub(d): return tot.loc[tot['date']<=d,'subs'].sum()
per={}
for lab,a,b in [('2023H2','2023-07-01','2024-01-01'),('2024H1','2024-01-01','2024-07-01'),('2024H2','2024-07-01','2025-01-01'),
                ('2025H1','2025-01-01','2025-07-01'),('пик май-сен25','2025-05-01','2025-10-01'),('дно ноя25-мар26','2025-11-01','2026-04-01')]:
    s=m[m['cl2']&(m['date']>=a)&(m['date']<b)]; per[lab]=(s['reads'].median(), ub(a), len(s))
for lab,(md,base,n) in per.items():
    print(f'  {lab:16s} n={n:3d} мед_reads={md:9.0f} база_UB={int(base):7d} отдача={md/base:8.4f}')
bt=per['дно ноя25-мар26']
print()
for lab in ['2023H2','2024H1','2024H2','2025H1']:
    md,base,_=per[lab]
    ratio=(md/base)/(bt[0]/bt[1])
    print(f'  падение отдачи на базу «{lab} -> дно»: точечно {ratio:.2f}x; худший случай при макс. искажении {ratio/1.199:.2f}x')
