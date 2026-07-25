import json, io
d=json.load(open('out/batches_sheets/sheets_08.json',encoding='utf-8'))
out=io.open('sheet08_all.txt','w',encoding='utf-8')
def t(s,n=190):
    if not s: return ""
    s=" ".join(s.split())
    return s[:n]+("…" if len(s)>n else "")
for i,a in enumerate(d):
    print("="*70, file=out)
    print(f"[{i}] oid={a['oid']} | картинок={a['картинок']} | слов={a['слов']}", file=out)
    print(f"ЗАГОЛОВОК: {a['заголовок']}", file=out)
    print(f"ПОЛОТНО: {a['полотно']}", file=out)
    if a.get('подзаголовки'): print("ПОДЗАГ: "+" | ".join(a['подзаголовки'][:8]), file=out)
    print(f"ПЕРВЫЙ: {t(a.get('первый_абзац'),260)}", file=out)
    for k in a['кадры_в_контексте']:
        print(f"  #{k['n']} ДО: {t(k.get('текст_перед'))}", file=out)
        print(f"      ПОСЛЕ: {t(k.get('текст_после'))}", file=out)
        if k.get('подпись'): print(f"      ПОДПИСЬ: {t(k['подпись'],120)}", file=out)
out.close()
print("ok")
