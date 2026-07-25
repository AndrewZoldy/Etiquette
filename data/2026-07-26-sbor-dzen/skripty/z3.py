import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 120); pd.set_option('display.max_rows', 400)
m = pd.read_pickle('out/full.pkl')
E1, E3 = '1_до_спада', '3_дно'
m['title'] = m['title_public'].fillna(m['title_studio'])
se = m[m['сцена'] == 'стол_еда']
print('=== стол_еда, эпоха 1 (n=%d), по показам' % len(se[se['эпоха']==E1]))
for _, r in se[se['эпоха']==E1].sort_values('shows', ascending=False).iterrows():
    print('%10.0f %7.0f %5.3f %s | %s | %s | %s' % (r.shows, r.reads, r.ctr, r['функция'][:12], r['порог_входа'][:7], r.date.date(), r.title))
print('\n=== стол_еда, эпоха 3 (n=%d), по показам' % len(se[se['эпоха']==E3]))
for _, r in se[se['эпоха']==E3].sort_values('shows', ascending=False).iterrows():
    print('%10.0f %7.0f %5.3f %s | %s | %s | %s' % (r.shows, r.reads, r.ctr, r['функция'][:12], r['порог_входа'][:7], r.date.date(), r.title))
