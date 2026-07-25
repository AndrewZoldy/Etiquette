import pandas as pd, numpy as np, re
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
m['title'] = m['title_public'].fillna(m['title_studio']).astype(str)
E1, E3 = '1_до_спада', '3_дно'
a = m[m['эпоха']==E1]; c = m[m['эпоха']==E3]

# ---- РЕГИСТР ЗАГОЛОВКА: "вопрос читателя" vs "номенклатура/справочник"
VERB = re.compile(r'\b(как|можно ли|почему|зачем|что делать|нужно ли|стоит ли|кто|когда|где|надо ли|правда ли)\b', re.I)
def reg(t):
    t = t.strip()
    if '?' in t or VERB.search(t): return 'вопрос_читателя'
    # номинативный: нет личного глагола-сказуемого (грубо: нет глагольных окончаний в 3л/2л/инф)
    if re.search(r'\b\w+(ть|тся|ет|ют|ит|ат|ят|ете|йте|ла|ло|ли)\b', t, re.I): return 'утверждение'
    return 'номенклатура'
m['регистр'] = m['title'].map(reg)
a = m[m['эпоха']==E1]; c = m[m['эпоха']==E3]
print('=== регистр заголовка: доли и медианы по эпохам')
for ep, d in [('до', a), ('дно', c)]:
    g = d.groupby('регистр').agg(n=('shows','size'), доля=('shows', lambda s: len(s)/len(d)),
        med_shows=('shows','median'), med_reads=('reads','median'), med_ctr=('ctr','median'))
    print(ep); print(g.round(4).to_string())

print('\n=== регистр внутри стол_еда')
for ep, d in [('до', a), ('дно', c)]:
    x = d[d['сцена']=='стол_еда']
    g = x.groupby('регистр').agg(n=('shows','size'), med_shows=('shows','median'), med_ctr=('ctr','median'))
    print(ep); print(g.round(4).to_string())

print('\n=== признаки заголовка отдельно ДО и ПОСЛЕ (медиана показов / CTR / n)')
for f in ['вопрос','цифра_в_заголовке','негативная_рамка','обращение_вы','конкретный_якорь','спорность','серийная_рубрика']:
    out = []
    for ep, d in [('до', a), ('дно', c)]:
        for v in [0,1]:
            y = d[d[f]==v]
            out.append('%s %s=%d n=%3d med=%9.0f ctr=%.3f' % (ep, f, v, len(y), y.shows.median() if len(y) else np.nan, y.ctr.median() if len(y) else np.nan))
    print(' | '.join(out))
print('\nдоли признаков: до -> дно')
for f in ['вопрос','цифра_в_заголовке','негативная_рамка','обращение_вы','конкретный_якорь','спорность','серийная_рубрика']:
    print('%-22s %.3f -> %.3f' % (f, a[f].mean(), c[f].mean()))

# ---- соседние публикации внутри стол_еда на дне
print('\n=== соседние пары стол_еда на дне (разрыв <=7 дней): отношение показов')
se3 = c[c['сцена']=='стол_еда'].sort_values('date')
prev = se3.shift(1)
d = se3.assign(gap=(se3.date-prev.date).dt.days, prev_shows=prev.shows.values, prev_title=prev.title.values)
d = d[d.gap<=7]
d['ratio'] = np.maximum(d.shows, d.prev_shows)/np.minimum(d.shows, d.prev_shows)
print('пар n=%d, медианное отношение показов между соседними по дате статьями одной темы: %.1fx' % (len(d), d.ratio.median()))
print(d[['date','gap','ratio','prev_shows','shows','prev_title','title']].sort_values('ratio', ascending=False).head(12).to_string())

# ---- есть ли пол раздачи
print('\n=== распределение показов на дне: нижние значения')
print(np.sort(c.shows.values)[:25])
print('opens у застрявших (<3000 показов):')
z = c[c.shows<3000]
print(z[['shows','opens','reads','ctr','subs']].describe().round(2).to_string())
