# -*- coding: utf-8 -*-
import pandas as pd, numpy as np

DATA = 'out/full.pkl'
RNG_SEED = 20260726
NB = 4000

def load():
    m = pd.read_pickle(DATA)
    m = m.copy()
    m['half'] = m['date'].dt.year.astype(str) + 'H' + np.where(m['date'].dt.month <= 6, '1', '2')
    # ce as clean tri-state
    ce = m['comments_enabled']
    m['ce'] = ce.map(lambda x: True if x is True else (False if x is False else np.nan))
    m['ceT'] = m['ce'] == True
    m['ceF'] = m['ce'] == False
    m['post'] = (m['date'] >= pd.Timestamp('2025-11-01')).astype(int)
    m['cell'] = m['сцена'].astype(str) + '|' + m['функция'].astype(str) + '|' + m['порог_входа'].astype(str)
    return m

def wmedian(x, w):
    """Взвешенная медиана — интерполированный взвешенный квантиль.
    При равных весах СТРОГО сводится к np.median (в т.ч. усреднение двух центральных
    при чётном n), поэтому ступени лестницы сравнимы между собой."""
    x = np.asarray(x, dtype=float); w = np.asarray(w, dtype=float)
    ok = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[ok], w[ok]
    if len(x) == 0: return np.nan
    if len(x) == 1: return float(x[0])
    o = np.argsort(x); x, w = x[o], w[o]
    cw = np.cumsum(w)
    p = (cw - 0.5 * w) / w.sum()
    return float(np.interp(0.5, p, x))


def wmedian_lower(x, w):
    """Альтернативная конвенция: нижняя взвешенная медиана (первое значение с cum.весом>=0.5)."""
    x = np.asarray(x, dtype=float); w = np.asarray(w, dtype=float)
    ok = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[ok], w[ok]
    if len(x) == 0: return np.nan
    o = np.argsort(x); x, w = x[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return float(x[np.searchsorted(cw, 0.5, side='left')])

def boot_ratio_medians(a, b, nb=NB, seed=RNG_SEED):
    """CI отношения median(a)/median(b), независимый ресемплинг двух групп."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
    rng = np.random.default_rng(seed)
    na, nb_ = len(a), len(b)
    out = np.empty(nb)
    for i in range(nb):
        ma = np.median(a[rng.integers(0, na, na)])
        mb = np.median(b[rng.integers(0, nb_, nb_)])
        out[i] = ma / mb if mb > 0 else np.nan
    out = out[np.isfinite(out)]
    return float(np.median(a)/np.median(b)), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))

def pct(x):
    return f"{x:.1f}%"
