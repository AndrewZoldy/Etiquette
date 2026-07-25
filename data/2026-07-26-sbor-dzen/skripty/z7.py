import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 140); pd.set_option('display.max_rows', 500)
art = pd.read_pickle('out/art.pkl'); rol = pd.read_pickle('out/rol.pkl'); pos = pd.read_pickle('out/pos.pkl')
for nm, d in [('art', art), ('rol', rol), ('pos', pos)]:
    print(nm, d.shape); print(list(d.columns))
m = pd.read_pickle('out/full_sim.pkl')

def mo(d): return d['date'].dt.to_period('M')
rows = []
for p in sorted(set(mo(art)) | set(mo(rol)) | set(mo(pos))):
    A = art[mo(art)==p]; R = rol[mo(rol)==p]; P = pos[mo(pos)==p]
    rows.append(dict(ym=str(p), n_art=len(A), n_rol=len(R), n_pos=len(P), n_all=len(A)+len(R)+len(P),
        art_med=A.shows.median() if len(A) else np.nan,
        art_med_reads=A.reads.median() if len(A) else np.nan,
        art_ctr=A.ctr.median() if len(A) else np.nan,
        flop_art=(A.shows<10000).mean() if len(A) else np.nan,
        pos_med=P.shows.median() if len(P) else np.nan,
        pos_ctr=P.ctr.median() if 'ctr' in P and len(P) else np.nan,
        rol_med=R.shows.median() if len(R) else np.nan))
t = pd.DataFrame(rows)
print('\n=== помесячно')
print(t.round(3).to_string())

print('\n=== посты: что они дают (все время)')
print(pos.describe(include='all').T.head(30).to_string())
