"""Машинные языковые признаки по ВСЕМ статьям + выгрузка текстов партиями для субагентов."""
import glob, json, os, re
import numpy as np
import pandas as pd

OUT = "out"
BT = os.path.join(OUT, "batches_text")
os.makedirs(BT, exist_ok=True)

WORD = re.compile(r"[А-Яа-яЁёA-Za-z]+")
SENT = re.compile(r"[.!?…]+(?:\s|$)")

MARKERS = {
    "вопрос_к_читателю": r"(а вы |как вы (думаете|считаете|поступ)|что скажете|согласны ли|"
                         r"напишите в коммент|расскажите в коммент|поделитесь в коммент)",
    "обращение_вы": r"\b(вы|вас|вам|ваш|ваша|ваше|ваши|вами)\b",
    "первое_лицо": r"\b(я|мне|меня|мной|мой|моя|моё|мои)\b",
    "мы_совместное": r"\b(мы|нас|нам|наш|наша|наши)\b",
    "предписание": r"\b(нельзя|нужно|надо|должен|должна|должны|следует|обязан|запрещ)",
    "смягчение": r"\b(можно|допустимо|уместно|не возбраняется|вполне|ничего страшного)",
    "оценка_моветон": r"(моветон|дурной тон|дурным тоном|невоспитан|бестактн|неприлич|"
                      r"некрасиво|неуважительн)",
    "прямая_речь": r"[«\"][^»\"]{5,}[»\"]",
    "цифры": r"\b\d+\b",
    "история_случай": r"(однажды|как-то раз|недавно|на днях|помню|мне рассказ|одна моя|"
                      r"знакомая рассказ|случай из)",
    "императив": r"\b\w+(?:йте|ьте)\b",
    "противопоставление": r"\b(но|однако|зато|при этом|а вот|тогда как|в отличие)\b",
    "усиление": r"\b(никогда|всегда|ни в коем случае|категорически|абсолютно|совершенно)\b",
    "уступка": r"\b(конечно|разумеется|безусловно|действительно|справедливости ради)\b",
    "второе_мнение": r"(есть мнение|многие считают|кто-то скажет|принято считать|"
                     r"часто спрашивают|нередко)",
    "этикет_слово": r"\bэтикет",
    "историческая_отсылка": r"(в xix|в xviii|в советск|при дворе|в старину|раньше|в прошлом веке|"
                            r"в дореволюционн|викториан)",
    "заграница": r"(во франции|в англии|в японии|в италии|в америке|в европе|за рубежом|"
                 r"в китае|в германии|в сша)",
}
COMP = {k: re.compile(v, re.I) for k, v in MARKERS.items()}


def feats(text, paras, headers, title):
    w = WORD.findall(text)
    nw = max(len(w), 1)
    sents = [s for s in SENT.split(text) if s.strip()]
    slen = [len(WORD.findall(s)) for s in sents] or [0]
    low = text.lower()
    f = {
        "предложений": len(sents),
        "слов_в_предложении_мед": float(np.median(slen)),
        "слов_в_предложении_сред": round(float(np.mean(slen)), 1),
        "доля_коротких_предложений": round(float(np.mean([x < 8 for x in slen])), 3),
        "доля_длинных_предложений": round(float(np.mean([x > 20 for x in slen])), 3),
        "вопросов": text.count("?"),
        "восклицаний": text.count("!"),
        "многоточий": text.count("…") + text.count("..."),
        "тире": text.count("—"),
        "абзацев": len(paras),
        "слов_в_абзаце_мед": float(np.median([len(WORD.findall(p)) for p in paras] or [0])),
        "длина_первого_абзаца": len(WORD.findall(paras[0])) if paras else 0,
        "длина_последнего_абзаца": len(WORD.findall(paras[-1])) if paras else 0,
        "финал_вопрос": int(bool(paras) and paras[-1].rstrip().endswith("?")),
        "старт_вопрос": int(bool(paras) and "?" in paras[0]),
        "подзаголовков": len(headers),
        "лексразнообразие": round(len(set(x.lower() for x in w)) / nw, 3),
        "слов": nw,
    }
    for k, rx in COMP.items():
        n = len(rx.findall(low))
        f[k] = n
        f[k + "_на100слов"] = round(n / nw * 100, 2)
    # признаки заголовка
    t = title or ""
    f["загл_слов"] = len(WORD.findall(t))
    f["загл_знаков"] = len(t)
    f["загл_вопрос"] = int("?" in t)
    f["загл_цифра"] = int(bool(re.search(r"\d", t)))
    f["загл_двоеточие"] = int(":" in t)
    f["загл_кавычки"] = int("«" in t or '"' in t)
    f["загл_можно_ли"] = int(bool(re.search(r"^(можно ли|нужно ли|стоит ли|нормально ли|прилично ли)", t, re.I)))
    f["загл_как"] = int(bool(re.search(r"^как\b", t, re.I)))
    f["загл_почему"] = int(bool(re.search(r"^почему\b", t, re.I)))
    f["загл_что"] = int(bool(re.search(r"^(что|чего)\b", t, re.I)))
    f["загл_когда"] = int(bool(re.search(r"^когда\b", t, re.I)))
    f["загл_отрицание"] = int(bool(re.search(r"\b(не|нельзя|никогда|без)\b", t, re.I)))
    return f


rows, batch = [], []
for fn in sorted(glob.glob("out/pages/*.json")):
    d = json.load(open(fn, encoding="utf-8"))
    text = d.get("text") or ""
    if not text.strip():
        continue
    paras = d.get("paragraphs") or []
    r = {"oid": d["oid"]}
    r.update(feats(text, paras, d.get("headers") or [], d.get("title")))
    rows.append(r)
    batch.append({"oid": d["oid"], "заголовок": d.get("title"),
                  "слов": d.get("n_words"), "картинок": d.get("n_images"),
                  "подзаголовки": d.get("headers") or [],
                  "текст": text})

tf = pd.DataFrame(rows)
tf.to_pickle("out/text_feats.pkl")
print("языковых признаков посчитано по", len(tf), "статьям;", len(tf.columns) - 1, "признаков")

import hashlib
batch.sort(key=lambda x: hashlib.md5(x["oid"].encode()).hexdigest())
N = 14
size = -(-len(batch) // N)
for i in range(N):
    ch = batch[i * size:(i + 1) * size]
    if ch:
        json.dump(ch, open(f"{BT}/text_{i:02d}.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        sz = os.path.getsize(f"{BT}/text_{i:02d}.json") / 1024
print(f"текстовых партий {N} по ~{size} статей (~{sz:.0f} КБ каждая), каталог {os.path.abspath(BT)}")
print("\nпример признаков:")
print(tf.head(2).T.head(30).to_string())
