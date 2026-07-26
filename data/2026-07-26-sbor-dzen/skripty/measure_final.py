"""Замер правленого текста против целевых зон."""
import re
import numpy as np

P = r"d:\Work\Etiquette\Etiquette\data\2026-07-26-sbor-dzen\vestnik-27-07-pravlenyj.md"
t = open(P, encoding="utf-8").read()
# отрезаем служебную шапку до первой горизонтальной черты
idx = t.find("\n---\n")
body = t[idx + 5:] if idx > 0 else t

W = re.compile(r"[А-Яа-яЁёA-Za-z]+")
S = re.compile(r"[.!?…]+(?:\s|\Z)")
words = W.findall(body)
sents = [s for s in S.split(body) if s.strip()]
sl = [len(W.findall(s)) for s in sents]
paras = [x.strip() for x in body.split("\n\n")
         if x.strip() and not x.strip().startswith("#")]
pl = [len(W.findall(x)) for x in paras if len(W.findall(x)) > 8]

names = re.findall(r"\*\*[^*\n]{6,95}\*\*\n", body)
dates = re.findall(r"\n\*[^*\n]{4,75}\*\n", body)

print("=" * 90)
print("ПРАВЛЕНЫЙ ТЕКСТ — ЗАМЕР")
print(f"  слов:                  {len(words):>6}   целевая зона 505–917 (n=144, дочит. 52,4%)")
print(f"  знаков:                {len(body):>6}")
print(f"  разделов-подзаголовков:{body.count(chr(10) + '## '):>6}   медиана аналогов 5")
print(f"  названий событий:      {len(names):>6}   медиана аналогов 17")
print(f"  строк-дат курсивом:    {len(dates):>6}   у 11 из 11 аналогов дата отдельной строкой")
print(f"  вопросов:              {body.count('?'):>6}")
print(f"  обращений на «вы»:     {len(re.findall(r'(?i)\\b(вы|вас|вам|ваш\\w*)\\b', body)):>6}")
print(f"  медиана предложения:   {np.median(sl):>6.0f}   слов")
print(f"  медиана абзаца:        {np.median(pl):>6.0f}   диапазон рубрики 35–54, черновик 59,9")
print(f"  мест под иллюстрации:  {body.count('[ФОТО]'):>6}   медиана рубрики 5, аналогов 7")
EPI = ["почти", "весьма", "непременно", "словно", "особенно", "крупнейш", "редк",
       "интеллигентн", "меланхол", "неспешн"]
tot = sum(len(re.findall(e, body, re.I)) for e in EPI)
print(f"  дежурных эпитетов:     {tot:>6}   в черновике было 37")

print("\n" + "=" * 90)
print("СРАВНЕНИЕ ДО / ПОСЛЕ")
rows = [
    ("Слов", 2517, len(words), "505–917"),
    ("Знаков", 18698, len(body), "—"),
    ("События", 41, len(names), "17 у аналогов"),
    ("Разделов", 0, body.count("\n## "), "5 у аналогов"),
    ("Дата отдельной строкой", 0, len(dates), "11 из 11"),
    ("Вопросов", 0, body.count("?"), "—"),
    ("Обращений на «вы»", 0, len(re.findall(r"(?i)\b(вы|вас|вам|ваш\w*)\b", body)), "—"),
    ("Медиана абзаца, слов", 60, int(np.median(pl)), "35–54"),
    ("Медиана предложения", 18, int(np.median(sl)), "—"),
    ("Дежурных эпитетов", 37, tot, "—"),
    ("Иллюстраций", 0, body.count("[ФОТО]"), "5–7"),
]
print(f"{'признак':26s} {'было':>8s} {'стало':>8s}   норма")
for n, a, b, z in rows:
    print(f"{n:26s} {a:>8} {b:>8}   {z}")
