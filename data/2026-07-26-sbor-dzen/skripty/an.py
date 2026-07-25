import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'C:/Users/andre/AppData/Local/Temp/claude/d--Work-Etiquette-Etiquette/cb7faf60-9cf2-48cf-8e9b-78a1a01a6376/scratchpad/out/themes/стол_еда.json'
s = open(p, encoding='utf-8').read().replace(': NaN', ': null')
d = json.loads(s)
arts = d['статьи']
print(len(arts))
for i, a in enumerate(arts):
    print(i, '|', a['заголовок'], '|', a['дата'], '|', a['эпоха'], '|', a['показы'], '|', a['дочитывания'], '|', a['комментарии'], '|', a['функция'], '|', a['порог'])
