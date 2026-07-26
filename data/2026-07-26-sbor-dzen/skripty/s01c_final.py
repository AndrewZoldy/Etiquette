# -*- coding: utf-8 -*-
"""ТРЕБОВАНИЕ 1 (финал): лестница 1-4 с корректным взвешенным квантилем + Оахака + регрессии."""
import pandas as pd, numpy as np
from common import load, wmedian, wmedian_lower
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 60)
NB, SEED = 4000, 20260726
m = load()
m['cell2'] = m['сцена'].astype(str)+'|'+m['функция'].astype(str)

# санити-чек оценщика
_t = np.array([1,2,3,4,10,20.]); assert abs(wmedian(_t, np.ones(6)) - np.median(_t)) < 1e-9
_t5 = np.array([1,2,3,4,10.]);   assert abs(wmedian(_t5, np.ones(5)) - np.median(_t5)) < 1e-9
print("Санити-чек: при равных весах wmedian == np.median  -> OK\n")

def ci_ratio(a,b,nb=NB,seed=SEED):
    a=np.asarray(a,float); b=np.asarray(b,float); lr=np.random.default_rng(seed); out=np.empty(nb)
    for i in range(nb): out[i]=np.median(a[lr.integers(0,len(a),len(a))])/max(np.median(b[lr.integers(0,len(b),len(b))]),1e-9)
    return np.median(a)/max(np.median(b),1e-9), np.percentile(out,2.5), np.percentile(out,97.5)

def reweight(src,tgt,cellcol,minn=5):
    tgt=tgt.copy(); src=src.copy()
    vc=tgt[cellcol].value_counts(); keep=set(vc[vc>=minn].index)
    tgt['_c']=tgt[cellcol].where(tgt[cellcol].isin(keep),'прочее')
    src['_c']=src[cellcol].where(src[cellcol].isin(keep),'прочее')
    ps=src['_c'].value_counts(normalize=True); pt=tgt['_c'].value_counts(normalize=True)
    w=tgt['_c'].map(lambda c:(ps.get(c,0.0)/pt[c]) if pt.get(c,0)>0 else 0.0)
    return tgt,w.values,keep,ps,pt

def fwd(A,B,cc):
    tgt,w,keep,ps,pt = reweight(A,B,cc)
    wm = wmedian(tgt['reads'].values,w); r = np.median(A['reads'])/max(wm,1e-9)
    lr=np.random.default_rng(SEED); out=np.empty(NB)
    av=A['reads'].values.astype(float); bv=tgt['reads'].values.astype(float); bw=np.asarray(w,float)
    for i in range(NB):
        ia=lr.integers(0,len(av),len(av)); ib=lr.integers(0,len(bv),len(bv))
        out[i]=np.median(av[ia])/max(wmedian(bv[ib],bw[ib]),1e-9)
    return r, np.percentile(out,2.5), np.percentile(out,97.5), wm, len(keep), tgt, w, ps, pt

def rev(A,B,cc):
    tgt,w,keep,ps,pt = reweight(B,A,cc)
    wm = wmedian(tgt['reads'].values,w); r = wm/max(np.median(B['reads']),1e-9)
    lr=np.random.default_rng(SEED); out=np.empty(NB)
    av=tgt['reads'].values.astype(float); aw=np.asarray(w,float); bv=B['reads'].values.astype(float)
    for i in range(NB):
        ia=lr.integers(0,len(av),len(av)); ib=lr.integers(0,len(bv),len(bv))
        out[i]=wmedian(av[ia],aw[ia])/max(np.median(bv[ib]),1e-9)
    return r, np.percentile(out,2.5), np.percentile(out,97.5), wm, len(keep)

print("="*112)
print("ТАБЛИЦА 1.1  ЛЕСТНИЦА КОНТРОЛЕЙ, reads, 2025H1 -> 2026H1, бутстрап 4000, CI95%")
print("="*112)
A = m[m['half']=='2025H1']; B = m[m['half']=='2026H1']
rows=[]
s1a,s1b = A,B
s2a,s2b = A[A['ceT']], B[B['ceT']]
s3a,s3b = s2a[s2a['age_days']>=150], s2b[s2b['age_days']>=150]
for name,a,b in [('1. сырьё',s1a,s1b),('2. + ce==True',s2a,s2b),('3. + age>=150',s3a,s3b)]:
    r,lo,hi = ci_ratio(a['reads'].values,b['reads'].values)
    rows.append({'ступень':name,'nA':len(a),'nB':len(b),'мед A':int(np.median(a['reads'])),
                 'мед B':int(np.median(b['reads'])),'отнош.':round(r,2),'CI низ':round(lo,2),'CI верх':round(hi,2),
                 'цифра критика':{'1. сырьё':20.40,'2. + ce==True':8.86,'3. + age>=150':6.19}[name]})
for cc,lab in [('cell','4. + состав (сцена|функция|порог)'),('cell2','4b. + состав (сцена|функция)'),('сцена','4c. + состав (сцена)')]:
    r,lo,hi,wm,nk,tgt,w,ps,pt = fwd(s3a,s3b,cc)
    rows.append({'ступень':lab,'nA':len(s3a),'nB':len(s3b),'мед A':int(np.median(s3a['reads'])),
                 'мед B':int(round(wm)),'отнош.':round(r,2),'CI низ':round(lo,2),'CI верх':round(hi,2),
                 'цифра критика':3.95 if cc=='cell' else np.nan})
t11 = pd.DataFrame(rows); print(t11.to_string(index=False))
print("\nПРИМЕЧАНИЕ: 'мед B' на ступенях 4 — ВЗВЕШЕННАЯ медиана 2026H1, приведённая к составу 2025H1.")
print("ячеек с n>=5 в 2026H1 после ценза: сцена|функция|порог = 0, сцена|функция = 0, сцена = 3")

print("\n" + "="*112)
print("ТАБЛИЦА 1.2  СИММЕТРИЧНАЯ ПРОВЕРКА ОАХАКИ (2025H1 -> состав 2026H1) и обе стороны на разных окнах")
print("="*112)
A1=m[(m['half']=='2025H1')&m['ceT']&(m['age_days']>=150)]; B1=m[(m['half']=='2026H1')&m['ceT']&(m['age_days']>=150)]
A2=m[(m['half']=='2025H1')&m['ceT']];                      B2=m[(m['half']=='2026H1')&m['ceT']]
A3=m[(m['эпоха']=='1_до_спада')&m['ceT']];                 B3=m[(m['эпоха']=='3_дно')&m['ceT']&(m['age_days']>=150)]
A4=A3;                                                     B4=m[(m['эпоха']=='3_дно')&m['ceT']]
A5=m[m['эпоха']=='1_до_спада'];                            B5=m[m['эпоха']=='3_дно']
rows=[]
for lbl,a,b in [('2025H1 vs 2026H1, ce=T, age>=150 (ступень 3-4 критика)',A1,B1),
                ('2025H1 vs 2026H1, ce=T, без ценза',A2,B2),
                ('до спада vs дно, ce=T, age>=150',A3,B3),
                ('до спада vs дно, ce=T, без ценза',A4,B4),
                ('до спада vs дно, СЫРЬЁ (ce=False внутри)',A5,B5)]:
    r0,l0,h0 = ci_ratio(a['reads'].values,b['reads'].values)
    for cc in ['cell','cell2','сцена']:
        rf,lf,hf,wmf,nkf,_,_,_,_ = fwd(a,b,cc)
        rr,lr_,hr,wmr,nkr = rev(a,b,cc)
        rows.append({'окно':lbl,'ячейка':cc,'nA':len(a),'nB':len(b),
                     'без станд.':round(r0,2),
                     'прямое (B->состав A)':round(rf,2),'CI прям':f"[{lf:.2f};{hf:.2f}]",'яч.n>=5 в B':nkf,
                     'обратное (A->состав B)':round(rr,2),'CI обр':f"[{lr_:.2f};{hr:.2f}]",'яч.n>=5 в A':nkr})
t12=pd.DataFrame(rows); print(t12.to_string(index=False))

print("\n" + "="*112)
print("ТАБЛИЦА 1.3  ЯЧЕЙКИ И ВЕСА для основной устойчивой спецификации (до спада vs дно, ce=T, без ценза, ячейка=сцена|функция)")
print("="*112)
r,lo,hi,wm,nk,tgt,w,ps,pt = fwd(A4,B4,'cell2')
tb=pd.DataFrame({'доля до спада,%':(ps*100).round(1),'доля дно,%':(pt*100).round(1)}).fillna(0)
tb['вес']=(ps/pt).round(3); tb['n дно']=tgt['_c'].value_counts(); tb['мед reads дно']=tgt.groupby('_c')['reads'].median().round(0)
print(tb.sort_values('доля дно,%',ascending=False).to_string())
print(f"\nсырое отношение {np.median(A4['reads'])/np.median(B4['reads']):.2f}x -> после стандартизации {r:.2f}x  CI[{lo:.2f};{hi:.2f}]")
print(f"Проверка конвенции оценщика: интерполированная взвеш.медиана={wm:.0f}, нижняя взвеш.медиана={wmedian_lower(tgt['reads'].values,w):.0f}")

# ---------------- РЕГРЕССИИ ----------------
print("\n" + "="*112)
print("ТАБЛИЦА 1.4  РЕГРЕССИИ log10(reads+1) на индикатор post (дата >= 2025-11-01)")
print("="*112)
def ols(X,y):
    b,*_ = np.linalg.lstsq(X,y,rcond=None)
    yh=X@b; ss=((y-yh)**2).sum(); r2=1-ss/((y-y.mean())**2).sum()
    return b, r2

def build(df, spec):
    n=len(df); cols=[np.ones(n)]; names=['const']
    cols.append(df['post'].values.astype(float)); names.append('post')
    if 'ce' in spec: cols.append(df['ceF'].values.astype(float)); names.append('ceF')
    if 'age' in spec: cols.append(np.log10(df['age_days'].values+1)); names.append('log10(age)')
    if 'mix' in spec:
        for c in ['сцена','функция','порог_входа']:
            lv=sorted(df[c].astype(str).unique())[1:]
            for v in lv:
                cols.append((df[c].astype(str)==v).values.astype(float)); names.append(f'{c}={v}')
    return np.column_stack(cols), names

def run(df, label):
    y=np.log10(df['reads'].values+1.0)
    out=[]
    for spec,sl in [([], 'M1: post'),(['ce'],'M2: +ceF'),(['ce','age'],'M3: +log10(age)'),
                    (['ce','age','mix'],'M4: +сцена+функция+порог')]:
        X,names=build(df,spec); b,r2=ols(X,y)
        d={'модель':sl,'n':len(df),'коэф. post':round(b[names.index('post')],3),
           'кратность post':round(10**(-b[names.index('post')]),2),
           'коэф. ceF':round(b[names.index('ceF')],3) if 'ceF' in names else np.nan,
           'кратность ceF':round(10**(-b[names.index('ceF')]),2) if 'ceF' in names else np.nan,
           'R2':round(r2,3)}
        # бутстрап CI для post и ceF
        lr=np.random.default_rng(SEED); bp=np.empty(NB); bc=np.empty(NB)
        ip=names.index('post'); ic=names.index('ceF') if 'ceF' in names else None
        for i in range(NB):
            idx=lr.integers(0,len(df),len(df))
            try:
                bb,_=ols(X[idx],y[idx]); bp[i]=bb[ip]; bc[i]=bb[ic] if ic is not None else np.nan
            except Exception: bp[i]=np.nan; bc[i]=np.nan
        bp=bp[np.isfinite(bp)]
        d['CI кратность post']=f"[{10**(-np.percentile(bp,97.5)):.2f};{10**(-np.percentile(bp,2.5)):.2f}]"
        if ic is not None:
            bc=bc[np.isfinite(bc)]
            d['CI кратность ceF']=f"[{10**(-np.percentile(bc,97.5)):.2f};{10**(-np.percentile(bc,2.5)):.2f}]"
        out.append(d)
    print(f"\n--- Выборка: {label} ---")
    print(pd.DataFrame(out).to_string(index=False))

run(m, "все 623 статьи")
run(m[m['half'].isin(['2025H1','2026H1'])], "только 2025H1 + 2026H1 (n=250)")
run(m[m['эпоха'].isin(['1_до_спада','3_дно'])], "до спада + дно (n=556)")

print("\n--- Коллинеарность post и log10(age): почему M3/M4 не идентифицированы ---")
mm=m.copy(); mm['la']=np.log10(mm['age_days']+1)
print(f"Пирсон(post, log10(age)) на всех 623 = {np.corrcoef(mm['post'],mm['la'])[0,1]:.3f}")
sub=mm[mm['half'].isin(['2025H1','2026H1'])]
print(f"Пирсон(post, log10(age)) на 2025H1+2026H1 = {np.corrcoef(sub['post'],sub['la'])[0,1]:.3f}")
print(f"age_days: post=0 -> медиана {mm[mm['post']==0]['age_days'].median():.0f} (диапазон {mm[mm['post']==0]['age_days'].min()}-{mm[mm['post']==0]['age_days'].max()})")
print(f"age_days: post=1 -> медиана {mm[mm['post']==1]['age_days'].median():.0f} (диапазон {mm[mm['post']==1]['age_days'].min()}-{mm[mm['post']==1]['age_days'].max()})")
print("Пересечение диапазонов age между post=0 и post=1:",
      f"[{max(mm[mm['post']==1]['age_days'].min(), mm[mm['post']==0]['age_days'].min())};"
      f"{min(mm[mm['post']==1]['age_days'].max(), mm[mm['post']==0]['age_days'].max())}]",
      f"-> статей post=0 в этом диапазоне: {int(((mm['post']==0)&(mm['age_days']<=mm[mm['post']==1]['age_days'].max())).sum())}")
print(f"\nПирсон(post, ceF) = {np.corrcoef(mm['post'],mm['ceF'].astype(float))[0,1]:.3f}; ceF при post=0: {int(mm[mm['post']==0]['ceF'].sum())} из {int((mm['post']==0).sum())}")
