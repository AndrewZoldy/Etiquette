import json, re

b = open("raw/big_script.js", encoding="utf-8").read()
print("len", len(b))

i = b.find("ничего не нужно")
# walk backwards to find the start of the embedded JSON string literal
seg = b[max(0, i - 8000):i]
print("---- 3000 chars before content ----")
print(seg[-3000:])
