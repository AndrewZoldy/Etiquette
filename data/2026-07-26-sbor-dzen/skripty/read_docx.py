"""Прочитать .docx без внешних библиотек: это zip с XML."""
import re, sys, zipfile

p = r"C:\Users\andre\.claude\uploads\cb7faf60-9cf2-48cf-8e9b-78a1a01a6376\6981a7cc-__________________________27______2________.docx"
z = zipfile.ZipFile(p)
print("файлы внутри:", [n for n in z.namelist() if n.endswith(".xml")][:12])

xml = z.read("word/document.xml").decode("utf-8", "replace")

# разбиваем по абзацам, внутри абзаца склеиваем все текстовые прогоны
paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
out = []
for pr in paras:
    # стиль абзаца (заголовок или обычный)
    st = re.search(r'w:pStyle w:val="([^"]+)"', pr)
    txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", pr, re.S))
    txt = (txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
              .replace("&quot;", '"').replace("&apos;", "'"))
    if txt.strip():
        out.append((st.group(1) if st else "", txt.strip()))

print(f"\nабзацев с текстом: {len(out)}")
words = sum(len(t.split()) for _, t in out)
chars = sum(len(t) for _, t in out)
print(f"слов: {words}, знаков: {chars}")
print("\n" + "=" * 100)
for i, (st, t) in enumerate(out):
    tag = f"[{st}]" if st else ""
    print(f"{i:3d} {tag} {t}")

# изображения внутри
imgs = [n for n in z.namelist() if n.startswith("word/media/")]
print(f"\nизображений в документе: {len(imgs)}")
for n in imgs[:20]:
    print("  ", n, z.getinfo(n).file_size, "байт")
