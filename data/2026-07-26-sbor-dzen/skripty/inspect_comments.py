import json

d = json.load(open("raw/comments_v0.json", encoding="utf-8"))
print("KEYS:", list(d.keys()))
print("\nMETA:", json.dumps(d.get("meta"), ensure_ascii=False)[:1200])
print("\nSORT TYPES:", json.dumps(d.get("sortTypes"), ensure_ascii=False)[:400])
print("\nitems:", len(d.get("items") or []))
it = d["items"]
print("\nFIRST ITEM:")
print(json.dumps(it[0], ensure_ascii=False, indent=1)[:2500])
print("\nITEM KEYS UNION:")
ks = set()
for x in it:
    ks |= set(x.keys())
print(sorted(ks))
print("\nmetaByCommentId sample:")
mb = d.get("metaByCommentId") or {}
k = list(mb)[:2]
for kk in k:
    print(kk, json.dumps(mb[kk], ensure_ascii=False)[:400])
print("\nsubthreadByCommentId sample:")
sb = d.get("subthreadByCommentId") or {}
for kk in list(sb)[:2]:
    print(kk, json.dumps(sb[kk], ensure_ascii=False)[:600])
print("\nusersById sample:")
ub = d.get("usersById") or {}
for kk in list(ub)[:1]:
    print(kk, json.dumps(ub[kk], ensure_ascii=False)[:700])
print("\nconfig:", json.dumps(d.get("config"), ensure_ascii=False)[:600])
