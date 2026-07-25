import pandas as pd, numpy as np
pd.set_option('display.width', 220)
pd.set_option('display.max_columns', 100)
m = pd.read_pickle('out/full.pkl')
m['half'] = m['date'].dt.year.astype(str) + 'H' + np.where(m['date'].dt.month <= 6, '1', '2')
print(m['эпоха'].value_counts())
for c in ['сцена','функция','порог_входа','фокус','объект_осуждения','серийная_рубрика','уверенность_разметки',
          'цифра_в_заголовке','негативная_рамка','вопрос','обращение_вы','конкретный_якорь','спорность']:
    print('---', c, m[c].dtype)
    print(m[c].value_counts(dropna=False).head(20))
