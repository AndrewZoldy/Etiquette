"""Достать результаты разведки из журнала воркфлоу и разложить по углам."""
import json, os

J = (r"C:\Users\andre\.claude\projects\d--Work-Etiquette-Etiquette"
     r"\cb7faf60-9cf2-48cf-8e9b-78a1a01a6376\subagents\workflows\wf_6e6b872b-c7a\journal.jsonl")
OUT = "out/recon"
os.makedirs(OUT, exist_ok=True)

recs = []
for line in open(J, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    o = json.loads(line)
    if o.get("type") == "result":
        recs.append(o.get("result"))

print("результатов:", len(recs))
findings, verdicts, other = [], [], []
for r in recs:
    if isinstance(r, dict) and "items" in r:
        findings.append(r)
    elif isinstance(r, dict) and "verdict" in r:
        verdicts.append(r)
    else:
        other.append(r)
print("углов разведки:", len(findings), "| проверок:", len(verdicts), "| прочее:", len(other))

for i, f in enumerate(findings):
    n = len(f.get("items") or [])
    print(f"\n=== угол {i}: находок {n} ===")
    print("SUMMARY:", (f.get("summary") or "")[:700])
    json.dump(f, open(f"{OUT}/angle_{i}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

json.dump({"findings": findings, "verdicts": verdicts},
          open(f"{OUT}/all.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sz = os.path.getsize(f"{OUT}/all.json") / 1024
print(f"\nсохранено {OUT}/all.json ({sz:.0f} КБ)")
print("проверки:")
for v in verdicts:
    print(" ", v.get("verdict"), "|", (v.get("reason") or "")[:200])
