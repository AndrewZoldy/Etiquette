# -*- coding: utf-8 -*-
import json, statistics, sys, re
sys.stdout.reconfigure(encoding='utf-8')
p = r"C:\Users\andre\AppData\Local\Temp\claude\d--Work-Etiquette-Etiquette\cb7faf60-9cf2-48cf-8e9b-78a1a01a6376\scratchpad\out\themes\отношения_общение.json"
arts = json.load(open(p, encoding='utf-8'))["статьи"]
def med(v): return int(statistics.median(v)) if v else None

print("### ПОРОГ x ЭПОХА")
for pr in sorted(set(a["порог"] for a in arts)):
    for ep in ["1_до_спада","2_склон","3_дно"]:
        s=[a for a in arts if a["порог"]==pr and a["эпоха"]==ep]
        if s: print("%-10s %-10s n=%2d мед.показы=%9s мед.дочит=%7s"%(pr,ep,len(s),med([a["показы"] for a in s]),med([a["дочитывания"] for a in s])))

print("\n### ДНО: спорная норма/разбор vs польза-справка")
e3=[a for a in arts if a["эпоха"]=="3_дно"]
sporn=[a for a in e3 if a["функция"] in ("разбор_чужого_поведения","разъяснение_нормы")]
polza=[a for a in e3 if a["функция"]=="польза"]
print("спорн/разбор n=%d мед.показы=%s мед.дочит=%s мед.комм=%s"%(len(sporn),med([a["показы"] for a in sporn]),med([a["дочитывания"] for a in sporn]),med([a["комментарии"] for a in sporn])))
print("польза       n=%d мед.показы=%s мед.дочит=%s мед.комм=%s"%(len(polza),med([a["показы"] for a in polza]),med([a["дочитывания"] for a in polza]),med([a["комментарии"] for a in polza])))

print("\n### ДНО: конфликтный/оценочный заголовок vs нейтральный")
conf = re.compile(r'(лицемер|раздража|обидн|перебива|тарелочниц|спасибо|не пропустит|не стоит|нужно ли|опасн|отказать|можно ли|почему)', re.I)
a1=[a for a in e3 if conf.search(a["заголовок"])]
a2=[a for a in e3 if not conf.search(a["заголовок"])]
print("оценочные n=%d мед.показы=%s мед.дочит=%s"%(len(a1),med([a["показы"] for a in a1]),med([a["дочитывания"] for a in a1])))
for a in a1: print("   ", a["показы"], a["заголовок"])
print("нейтральные n=%d мед.показы=%s мед.дочит=%s"%(len(a2),med([a["показы"] for a in a2]),med([a["дочитывания"] for a in a2])))

print("\n### ВСЯ СЦЕНА: заголовки с 'Как ...' vs вопрос о норме")
kak=[a for a in arts if a["заголовок"].lower().startswith("как ")]
print("'Как...' n=%d мед.показы=%s"%(len(kak),med([a["показы"] for a in kak])))
e3kak=[a for a in kak if a["эпоха"]=="3_дно"]
print("'Как...' на дне n=%d мед.показы=%s мед.дочит=%s"%(len(e3kak),med([a["показы"] for a in e3kak]),med([a["дочитывания"] for a in e3kak])))
e3nk=[a for a in e3 if not a["заголовок"].lower().startswith("как ")]
print("не-'Как' на дне n=%d мед.показы=%s мед.дочит=%s"%(len(e3nk),med([a["показы"] for a in e3nk]),med([a["дочитывания"] for a in e3nk])))

print("\n### ТОП-15 по комментариям (вся сцена)")
for a in sorted(arts,key=lambda x:-x["комментарии"])[:15]:
    print("%5d комм | %9d показ | %s | %s"%(a["комментарии"],a["показы"],a["эпоха"],a["заголовок"]))

print("\n### 2025 год+ : ЭПОХА 2 подробно")
for a in sorted([a for a in arts if a["эпоха"]=="2_склон"],key=lambda x:-x["показы"]):
    print("%9d %7d %5d %s | %-24s| %s"%(a["показы"],a["дочитывания"],a["комментарии"],a["дата"],a["функция"],a["заголовок"]))

print("\n### Дочитываемость (дочит/показы) — медиана по эпохам")
for ep in ["1_до_спада","2_склон","3_дно"]:
    s=[a for a in arts if a["эпоха"]==ep]
    print(ep, round(statistics.median([a["дочитывания"]/a["показы"] for a in s]),4))
