# -*- coding: utf-8 -*-
import pandas as pd, numpy as np

DATA = 'out/full.pkl'

def load():
    m = pd.read_pickle(DATA)
    m = m.copy()
    m['ce'] = m['comments_enabled']
    y = m['date'].dt.year
    h = np.where(m['date'].dt.month <= 6, 'H1', 'H2')
    m['half'] = y.astype(str) + h
    m['post'] = (m['date'] >= pd.Timestamp('2025-11-01')).astype(int)
    m['ceF'] = (m['ce'] == False).astype(int)
    m['cell'] = m['сцена'].astype(str) + '|' + m['функция'].astype(str) + '|' + m['порог_входа'].astype(str)
    return m

def wquantile(x, w, q=0.5):
    """Взвешенный квантиль по середине ступеньки CDF.
    При равных весах ТОЧНО совпадает со стандартной медианой (np.median / pandas median)."""
    x = np.asarray(x, dtype=float); w = np.asarray(w, dtype=float)
    ok = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[ok], w[ok]
    if len(x) == 0 or w.sum() <= 0:
        return np.nan
    o = np.argsort(x, kind='mergesort')
    x, w = x[o], w[o]
    S = np.cumsum(w)
    p = (S - w / 2.0) / S[-1]
    return float(np.interp(q, p, x))

def wmedian(x, w=None):
    if w is None:
        w = np.ones(len(x))
    return wquantile(x, w, 0.5)

def collapse_cells(cells, counts, min_n=5):
    """Возвращает map cell -> cell_or_prochee по счётчикам целевой выборки."""
    keep = set(counts[counts >= min_n].index)
    return {c: (c if c in keep else 'ПРОЧЕЕ') for c in cells}

def std_weights(df_target, df_ref, cellcol='cell2'):
    """Веса для df_target так, чтобы его состав совпал с df_ref."""
    st = df_target[cellcol].value_counts(normalize=True)
    sr = df_ref[cellcol].value_counts(normalize=True)
    w = df_target[cellcol].map(lambda c: (sr.get(c, 0.0) / st[c]) if st.get(c, 0) > 0 else 0.0)
    return w.values

def boot_ratio(a_vals, b_vals, a_w=None, b_w=None, n=4000, seed=42):
    """CI отношения медиан a/b (a = ранняя эпоха, b = поздняя)."""
    rng = np.random.default_rng(seed)
    a_vals = np.asarray(a_vals, float); b_vals = np.asarray(b_vals, float)
    a_w = np.ones(len(a_vals)) if a_w is None else np.asarray(a_w, float)
    b_w = np.ones(len(b_vals)) if b_w is None else np.asarray(b_w, float)
    na, nb = len(a_vals), len(b_vals)
    out = np.empty(n)
    for i in range(n):
        ia = rng.integers(0, na, na); ib = rng.integers(0, nb, nb)
        ma = wmedian(a_vals[ia], a_w[ia]); mb = wmedian(b_vals[ib], b_w[ib])
        out[i] = ma / mb if (mb and mb > 0) else np.nan
    out = out[np.isfinite(out)]
    return np.percentile(out, 2.5), np.percentile(out, 97.5), out

def ols(y, X, names):
    """OLS через lstsq; возвращает коэффициенты, SE (гомоскедастичные и HC1)."""
    y = np.asarray(y, float); X = np.asarray(X, float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    XtXi = np.linalg.pinv(X.T @ X)
    s2 = (resid @ resid) / (n - k)
    se = np.sqrt(np.diag(XtXi * s2))
    # HC1
    meat = (X * (resid ** 2)[:, None]).T @ X
    V = XtXi @ meat @ XtXi * (n / (n - k))
    se_hc1 = np.sqrt(np.diag(V))
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid @ resid) / ss_tot
    return dict(zip(names, beta)), dict(zip(names, se)), dict(zip(names, se_hc1)), r2, n

def dummies(df, col, drop_first=True):
    d = pd.get_dummies(df[col].astype(str), prefix=col, drop_first=drop_first).astype(float)
    return d
