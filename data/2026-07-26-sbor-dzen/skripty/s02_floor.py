# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 2: пересчёт Фактов 4 и 5 на comments_enabled==True."""
import pandas as pd, numpy as np
from common import load
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
NB,SEED=4000,20260726
m=load()
HALVES=['2023H2','2024H1','2024H2','2025H1','2025H2','2026H1']

def floor_tab(df,lbl):
    rows=[]
    for h in HALVES+['2026H2']:
        s=df[df['half']==h]
        if len(s)==0: continue
        sh=s['shows'].values
        rows.append({'полугодие':h,'n':len(s),
            'доля <10k,%':round((sh<10000).mean()*100,1),
            'доля <3k,%':round((sh<3000).mean()*100,1),
            'p10':int(np.percentile(sh,10)),'p50':int(np.percentile(sh,50)),'p90':int(np.percentile(sh,90)),
            'p90/p10':round(np.percentile(sh,90)/max(np.percentile(sh,10),1e-9),1),
            'p25':int(np.percentile(sh,25)),'p75':int(np.percentile(sh,75)),'max':int(sh.max()),
            'вывод?': 'нет (n<10)' if len(s)<10 else ''})
    t=pd.DataFrame(rows); print(f"\n--- {lbl} ---"); print(t.to_string(index=False)); return t

print("="*118)
print("ТРЕБОВАНИЕ 2, ЧАСТЬ A: ПОЛ ПОКАЗОВ по полугодиям — сырьё vs comments_enabled==True")
print("="*118)
t_raw = floor_tab(m,'СЫРЬЁ (как в Факте 4 досье)')
t_ce  = floor_tab(m[m['ceT']],'ТОЛЬКО comments_enabled==True')
t_cef = floor_tab(m[m['ceF']],'ТОЛЬКО comments_enabled==False (серия)')

print("\n--- Прямое сопоставление ключевых чисел с заявкой критика ---")
cmp=pd.DataFrame({
 'показатель':['доля <10k 2024H1','доля <10k 2025H1','доля <10k 2026H1(ce=T)','доля <3k 2026H1(ce=T)',
               'p90/p10 2024H1','p90/p10 2025H1','p90/p10 2026H1(ce=T)'],
 'цифра критика':['8,9%','0,0%','8,3%','0,0%','150','52','101']})
def g(tab,h,col):
    r=tab[tab['полугодие']==h]; return None if len(r)==0 else r.iloc[0][col]
cmp['мой расчёт']=[f"{g(t_ce,'2024H1','доля <10k,%')}%",f"{g(t_ce,'2025H1','доля <10k,%')}%",
                   f"{g(t_ce,'2026H1','доля <10k,%')}%",f"{g(t_ce,'2026H1','доля <3k,%')}%",
                   f"{g(t_ce,'2024H1','p90/p10')}",f"{g(t_ce,'2025H1','p90/p10')}",f"{g(t_ce,'2026H1','p90/p10')}"]
print(cmp.to_string(index=False))
print("\nСырьё для контраста: доля <10k 2026H1 =", g(t_raw,'2026H1','доля <10k,%'),
      "%, доля <3k 2026H1 =", g(t_raw,'2026H1','доля <3k,%'), "%, p90/p10 2026H1 =", g(t_raw,'2026H1','p90/p10'))

# бутстрап CI для доли <10k на ce=True
print("\n--- Бутстрап CI (4000) для доли shows<10000 на ce=True ---")
for h in HALVES:
    s=m[(m['half']==h)&m['ceT']]['shows'].values
    if len(s)<10: print(f"{h}: n={len(s)} <10, вывод не формулируется"); continue
    lr=np.random.default_rng(SEED); b=np.array([ (s[lr.integers(0,len(s),len(s))]<10000).mean() for _ in range(NB)])
    print(f"{h}: n={len(s):3d} доля={(s<10000).mean()*100:5.1f}%  CI95%=[{np.percentile(b,2.5)*100:.1f}%;{np.percentile(b,97.5)*100:.1f}%]")

# то же на ДОЧИТЫВАНИЯХ (первичная метрика по правилу 7) — относительный пол
print("\n--- ОТНОСИТЕЛЬНЫЙ пол (масштабно-инвариантно, не нарушает правило 6): "
      "доля статей с shows < 10% медианы СВОЕГО полугодия; и p50/p10 ---")
rows=[]
for h in HALVES+['2026H2']:
    for lbl,d in [('сырьё',m),('ce=True',m[m['ceT']])]:
        s=d[d['half']==h]['shows'].values
        if len(s)<10: continue
        med=np.median(s)
        rows.append({'полугодие':h,'выборка':lbl,'n':len(s),
                     'доля <10% медианы,%':round((s<0.1*med).mean()*100,1),
                     'доля <3% медианы,%':round((s<0.03*med).mean()*100,1),
                     'p50/p10':round(med/max(np.percentile(s,10),1e-9),1),
                     'p90/p50':round(np.percentile(s,90)/max(med,1e-9),1)})
print(pd.DataFrame(rows).sort_values(['полугодие','выборка']).to_string(index=False))

print("\n" + "="*118)
print("ТРЕБОВАНИЕ 2, ЧАСТЬ B: КВИНТИЛИ CTR внутри эпохи 'дно' — медиана показов и дочитываний")
print("="*118)
def qtab(df,lbl,ycols=('shows','reads','opens')):
    d=df.dropna(subset=['ctr']).copy()
    d['q']=pd.qcut(d['ctr'],5,labels=[1,2,3,4,5])
    rows=[]
    for q,g in d.groupby('q',observed=True):
        r={'квинтиль CTR':int(q),'n':len(g),'мед CTR':round(g['ctr'].median(),4)}
        for y in ycols: r[f'мед {y}']=int(g[y].median())
        r['вывод?']='нет (n<10)' if len(g)<10 else ''
        rows.append(r)
    t=pd.DataFrame(rows); print(f"\n--- {lbl} (n={len(d)}) ---"); print(t.to_string(index=False))
    for y in ycols:
        v=t[f'мед {y}'].values
        mono = 'монотонна' if all(np.diff(v)>0) else 'НЕМОНОТОННА'
        print(f"  {y}: q5/q1 = {v[-1]/max(v[0],1e-9):.2f}x ; max/min = {v.max()/max(v.min(),1e-9):.2f}x ; {mono}")
    return t

d_bot=m[m['эпоха']=='3_дно']; d_pre=m[m['эпоха']=='1_до_спада']
qtab(d_pre,"ДО СПАДА, СЫРЬЁ")
qtab(d_bot,"ДНО, СЫРЬЁ (как в Факте 5 досье)")
qtab(d_pre[d_pre['ceT']],"ДО СПАДА, ce=True")
q_bot_ce=qtab(d_bot[d_bot['ceT']],"ДНО, ce=True  <<< ГЛАВНАЯ ТАБЛИЦА ТРЕБОВАНИЯ")
qtab(d_bot[d_bot['ceF']],"ДНО, ce=False (серия)")

print("\nЦифры критика для 'дно, ce=True' (медиана показов): 62016 / 157694 / 49034 / 255228 / 80397")
print("мой расчёт:", ' / '.join(str(x) for x in q_bot_ce['мед shows'].tolist()))

print("\n--- Спирмен CTR x показы и CTR x дочитывания ---")
rows=[]
for lbl,d in [('до спада, сырьё',d_pre),('до спада, ce=True',d_pre[d_pre['ceT']]),
              ('склон, сырьё',m[m['эпоха']=='2_склон']),
              ('дно, сырьё',d_bot),('дно, ce=True',d_bot[d_bot['ceT']]),('дно, ce=False',d_bot[d_bot['ceF']])]:
    dd=d.dropna(subset=['ctr'])
    rows.append({'группа':lbl,'n':len(dd),
                 'Спирмен ctr~shows':round(dd[['ctr','shows']].corr(method='spearman').iloc[0,1],3),
                 'Спирмен ctr~reads':round(dd[['ctr','reads']].corr(method='spearman').iloc[0,1],3)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n--- Доля 'миллионников' и застрявших: сырьё vs ce=True ---")
rows=[]
for lbl,d in [('до спада, сырьё',d_pre),('до спада, ce=True',d_pre[d_pre['ceT']]),
              ('дно, сырьё',d_bot),('дно, ce=True',d_bot[d_bot['ceT']]),('дно, ce=False',d_bot[d_bot['ceF']])]:
    rows.append({'группа':lbl,'n':len(d),
                 'shows<3k,%':round((d['shows']<3000).mean()*100,1),
                 'shows<10k,%':round((d['shows']<10000).mean()*100,1),
                 'shows>1M,%':round((d['shows']>1_000_000).mean()*100,1),
                 'shows>500k,%':round((d['shows']>500_000).mean()*100,1)})
print(pd.DataFrame(rows).to_string(index=False))
