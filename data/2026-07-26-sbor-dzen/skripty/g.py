import re, html, io

raw = open('vc.html', encoding='utf-8', errors='replace').read()
t = re.sub(r'<[^>]+>', ' ', raw)
t = html.unescape(t)
t = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), t)
t = re.sub(r'\s+', ' ', t)
open('vc_full.txt', 'w', encoding='utf-8').write(t)

out = io.open('grep.txt', 'w', encoding='utf-8')
out.write('LEN %d\n' % len(t))
kws = ['83', 'Крауд', 'Яндекс', 'абота.ру', 'абота.ру', 'онтур', '42%', '34%',
       '33%', '29%', '25%', '32%', 'созвон', 'мессендж', 'часов', 'опрош',
       'исследован', 'респондент']
for kw in kws:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t)]
    out.write('\n=== %s  count=%d\n' % (kw, len(idxs)))
    for i in idxs[:6]:
        out.write('   ...' + t[max(0, i - 260):i + 260].strip() + '\n')
out.close()
print('done')
