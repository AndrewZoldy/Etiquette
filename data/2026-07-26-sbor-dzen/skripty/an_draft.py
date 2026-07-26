"""Разбор присланного черновика ровно по тем дефектам, которые назвали читатели рубрики."""
import re, zipfile
from collections import Counter
import numpy as np

P = (r"C:\Users\andre\.claude\uploads\cb7faf60-9cf2-48cf-8e9b-78a1a01a6376"
     r"\6981a7cc-__________________________27______2________.docx")
z = zipfile.ZipFile(P)
xml = z.read("word/document.xml").decode("utf-8", "replace")
paras = []
for pr in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
    t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", pr, re.S))
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&apos;", "'")).strip()
    if t:
        paras.append(t)
title, lead, body = paras[0], paras[1], paras[2:]
text = "\n".join(paras)
WORD = re.compile(r"[А-Яа-яЁёA-Za-z]+")
SENT = re.compile(r"[.!?…]+(?:\s|$)")
words = WORD.findall(text)
sents = [s for s in SENT.split(text) if s.strip()]
slen = [len(WORD.findall(s)) for s in sents]

print("=" * 120)
print("ОБЩИЕ ЦИФРЫ ЧЕРНОВИКА")
print(f"  заголовок: {title}")
print(f"  абзацев (всего/событий): {len(paras)} / {len(body)-1}")
print(f"  слов: {len(words)}, знаков: {len(text)}")
print(f"  предложений: {len(sents)}, медиана длины предложения: {np.median(slen):.0f} слов")
print(f"  доля предложений длиннее 20 слов: {np.mean([x > 20 for x in slen]):.1%}")
print(f"  доля коротких (до 8 слов): {np.mean([x < 8 for x in slen]):.1%}")
pl = [len(WORD.findall(p)) for p in body]
print(f"  медиана длины абзаца: {np.median(pl):.0f} слов, максимум {max(pl)}")
print(f"  вопросительных знаков: {text.count('?')}")
print(f"  обращений на «вы»: {len(re.findall(r'\\b(вы|вас|вам|ваш\\w*)\\b', text, re.I))}")
print(f"  подзаголовков: 0 (в документе нет стилей заголовков)")

print("\n" + "=" * 120)
print("ДЕФЕКТ 1. ПОВТОРЯЮЩИЕСЯ ЭПИТЕТЫ — читатели назвали это прямо")
EPI = ["неспешн", "крупнейш", "особенно", "весьма", "непременно", "почти", "словно",
       "именно", "по-настоящему", "тот самый", "та самая", "то самое", "редк",
       "знаменит", "известн", "один из самых", "одна из самых", "лёгк", "легк",
       "интеллигентн", "меланхол", "изысканн", "элегантн", "атмосфер"]
cnt = {e: len(re.findall(e, text, re.I)) for e in EPI}
for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
    if v:
        print(f"  {k:20s} {v:3d}")
print(f"\n  ИТОГО вхождений «дежурных» эпитетов: {sum(cnt.values())} на {len(words)} слов "
      f"= {sum(cnt.values())/len(words)*1000:.1f} на 1000 слов")

print("\n" + "=" * 120)
print("ДЕФЕКТ 2. «ВЫЧУРНЫЙ СЛОВЕСНЫЙ КРЕНДЕЛЬ» — оценочные обороты вокруг факта")
ORN = [r"выглядят? весьма подходящим", r"не кажется неуместн", r"почти образцовый",
       r"почти безошибочн", r"как это часто бывает", r"как водится", r"тот редкий час",
       r"почти не нуждаются", r"не менее интересно", r"особенно хорошо",
       r"удивительно цельн", r"почти физическ", r"почти историческ",
       r"словно нарочно", r"отчего-то", r"непременно найдётся"]
for o in ORN:
    for mm in re.finditer(o, text, re.I):
        s = max(0, mm.start() - 60)
        print(f"  …{text[s:mm.end()+60]}…".replace("\n", " "))

print("\n" + "=" * 120)
print("ДЕФЕКТ 3. САМЫЕ ДЛИННЫЕ ПРЕДЛОЖЕНИЯ (кандидаты на разрезание)")
pairs = sorted(zip(slen, sents), reverse=True)[:8]
for n, s in pairs:
    print(f"  [{n} слов] {s.strip()[:230]}")

print("\n" + "=" * 120)
print("ДЕФЕКТ 4. СКОЛЬКО СЛОВ НА ОДНО СОБЫТИЕ")
ev = [(len(WORD.findall(p)), p[:70]) for p in body[:-1]]
print(f"  медиана слов на событие: {np.median([x[0] for x in ev]):.0f}, "
      f"диапазон {min(x[0] for x in ev)}–{max(x[0] for x in ev)}")
print("  самые раздутые события:")
for n, s in sorted(ev, reverse=True)[:8]:
    print(f"    [{n} слов] {s}")
print("  самые компактные:")
for n, s in sorted(ev)[:5]:
    print(f"    [{n} слов] {s}")

print("\n" + "=" * 120)
print("ДЕФЕКТ 5. ЧТО СТОИТ ПЕРВЫМ И ПОСЛЕДНИМ")
print(f"  ЛИД: {lead[:400]}")
print(f"\n  ПЕРВОЕ СОБЫТИЕ: {body[0][:250]}")
print(f"\n  ПОСЛЕДНЕЕ СОБЫТИЕ: {body[-2][:250]}")
print(f"\n  ФИНАЛ: {body[-1][:400]}")

print("\n" + "=" * 120)
print("ДЕФЕКТ 6. ЕСТЬ ЛИ В ТЕКСТЕ ХОТЬ ОДНО ПРАВИЛО ЭТИКЕТА (тема канала)")
ET = [r"этикет", r"правил", r"принято", r"не принято", r"уместн", r"дресс-код",
      r"как себя вест", r"моветон", r"дурной тон"]
for e in ET:
    n = len(re.findall(e, text, re.I))
    if n:
        print(f"  {e:16s} {n}")
        for mm in list(re.finditer(e, text, re.I))[:2]:
            s = max(0, mm.start() - 70)
            print(f"      …{text[s:mm.end()+70]}…".replace("\n", " "))
