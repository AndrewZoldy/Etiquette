import pandas as pd, numpy as np, re, json, os, math
from collections import Counter
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 500)
m = pd.read_pickle('out/full.pkl').sort_values('date').reset_index(drop=True)
m['title'] = m['title_public'].fillna(m['title_studio']).astype(str)
E1, E3 = '1_до_спада', '3_дно'
STOP = set('и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех никогда можно при наконец два об другой хоть после над больше тот через эти нас про всего них какая много разве три эту моя впрочем свою этой перед иногда лучше чуть том нельзя такой им более всегда конечно всю между это'.split())
def toks(s):
    w = re.findall(r'[а-яёa-z]+', str(s).lower())
    return [x[:6] for x in w if len(x) > 3 and x not in STOP]

# ---- НОВИЗНА ЗАГОЛОВКА: макс. Жаккар с любым РАНЕЕ вышедшим заголовком канала
T = [set(toks(t)) for t in m['title']]
maxsim = np.zeros(len(m)); who = ['']*len(m)
for i in range(len(m)):
    best, bj = 0.0, -1
    for j in range(i):
        u = len(T[i] | T[j])
        if not u: continue
        s = len(T[i] & T[j])/u
        if s > best: best, bj = s, j
    maxsim[i] = best; who[i] = m['title'].iloc[bj] if bj >= 0 else ''
m['title_sim_prev'] = maxsim; m['nearest_prev'] = who

# ---- НОВИЗНА ТЕКСТА (косинус tf-idf по всем предыдущим)
docs = {}
for oid in m['oid']:
    p = f'out/pages/{oid}.json'
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding='utf-8'))
            docs[oid] = Counter(toks(d.get('text','')))
        except Exception: pass
print('текстов загружено:', len(docs), 'из', len(m))
df = Counter()
for v in docs.values():
    df.update(v.keys())
N = len(docs)
idf = {w: math.log(N/(1+n)) for w, n in df.items()}
vecs = {}
for oid, cnt in docs.items():
    v = {w: (1+math.log(c))*idf.get(w,0) for w, c in cnt.items() if len(w) > 3}
    nrm = math.sqrt(sum(x*x for x in v.values())) or 1
    vecs[oid] = {w: x/nrm for w, x in v.items()}
oids = list(m['oid'])
tsim = np.full(len(m), np.nan); twho = ['']*len(m)
for i, oi in enumerate(oids):
    if oi not in vecs: continue
    vi = vecs[oi]; best, bj = 0.0, -1
    for j in range(i):
        oj = oids[j]
        if oj not in vecs: continue
        vj = vecs[oj]
        if len(vi) > len(vj): vi_, vj_ = vj, vi
        else: vi_, vj_ = vi, vj
        s = sum(x*vj_.get(w,0) for w, x in vi_.items())
        if s > best: best, bj = s, j
    tsim[i] = best; twho[i] = m['title'].iloc[bj] if bj >= 0 else ''
m['text_sim_prev'] = tsim; m['nearest_text'] = twho
m.to_pickle('out/full_sim.pkl')

a = m[m['эпоха']==E1]; c = m[m['эпоха']==E3]
print('\n=== новизна по эпохам (медианы)')
print(m.groupby('эпоха')[['title_sim_prev','text_sim_prev']].median().round(3).to_string())
print(m.assign(half=m.date.dt.year.astype(str)+'H'+np.where(m.date.dt.month<=6,'1','2')).groupby('half')[['title_sim_prev','text_sim_prev']].agg(['median','size']).round(3).to_string())

print('\n=== связь новизны с показами / CTR, ОТДЕЛЬНО по эпохам (Спирмен)')
for ep, d in [('до', a), ('дно', c)]:
    for f in ['title_sim_prev','text_sim_prev']:
        d2 = d.dropna(subset=[f])
        print('%s %s vs shows %.3f | vs ctr %.3f | vs reads %.3f (n=%d)' %
              (ep, f, d2[f].corr(d2.shows, method='spearman'), d2[f].corr(d2.ctr, method='spearman'),
               d2[f].corr(d2.reads, method='spearman'), len(d2)))

print('\n=== терцили похожести текста на прошлое: медианы показов')
for ep, d in [('до', a), ('дно', c)]:
    d2 = d.dropna(subset=['text_sim_prev']).copy()
    d2['t'] = pd.qcut(d2.text_sim_prev, 3, labels=['новое','среднее','повтор'])
    print(ep); print(d2.groupby('t', observed=True).agg(n=('shows','size'), sim=('text_sim_prev','median'),
        med_shows=('shows','median'), med_reads=('reads','median'), med_ctr=('ctr','median')).round(4).to_string())

print('\n=== то же внутри стол_еда')
for ep, d in [('до', a), ('дно', c)]:
    x = d[(d['сцена']=='стол_еда')].dropna(subset=['text_sim_prev']).copy()
    x['t'] = pd.qcut(x.text_sim_prev, 2, labels=['новее','повторнее'])
    print(ep); print(x.groupby('t', observed=True).agg(n=('shows','size'), sim=('text_sim_prev','median'),
        med_shows=('shows','median'), med_ctr=('ctr','median')).round(4).to_string())
