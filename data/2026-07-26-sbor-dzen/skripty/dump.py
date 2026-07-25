import json, sys, io
d=json.load(open('out/batches_sheets/sheets_08.json',encoding='utf-8'))
out=io.open('sheet08_dump.txt','w',encoding='utf-8')
print(len(d), file=out)
print(json.dumps(d[0],ensure_ascii=False,indent=1)[:4000], file=out)
out.close()
