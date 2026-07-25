import json, urllib.parse
from dzenlib import Dzen

d = Dzen(referer="https://dzen.ru/a/amNAZ54XI3753Qr_")
d.op.addheaders += [("X-Zen-Comments-Clid", "300"), ("X-Zen-Comments-Place", "article"),
                    ("X-Zen-Comments-Product", "zen")]
BASE = "https://dzen.ru/api/comments/v2/"
OID = "6a6340679e17237ef9dd0aff"
PUB = "63dd27aac30ab522dcce48b3"


def call(method, params):
    return d.get_json(BASE + method + "?" + urllib.parse.urlencode(params))


r = call("root-comments", dict(documentId=f"native:{OID}", publicationPublisherId=PUB,
                               sorting="oldest", batchSize="50", withConfig="true"))
mb = r["metaByCommentId"]
print("meta:", json.dumps(r["meta"], ensure_ascii=False))
print("roots:", len(r["items"]))
tot_children = 0
for x in r["items"]:
    ed = x["entityData"]
    cid = str(ed["id"])
    m = mb.get(cid, {})
    n = m.get("childrenCount", 0)
    tot_children += n
    print(f"  {cid} children={n:4d} likes={m.get('likes'):4} state={m.get('state')} :: {ed['text'][:60]!r}")
print("sum childrenCount:", tot_children)

# take the root with most children
best = max(r["items"], key=lambda x: mb.get(str(x["entityData"]["id"]), {}).get("childrenCount", 0))
bid = str(best["entityData"]["id"])
print("\nbiggest root:", bid, mb[bid]["childrenCount"])
c = call("child-comments", dict(rootCommentId=bid, documentId=f"native:{OID}",
                                publicationPublisherId=PUB, withConfig="true", batchSize="20"))
print("child items:", len(c["items"]), "more:", repr(c.get("moreItemsQueryString"))[:200])
print("child meta:", json.dumps(c.get("meta"), ensure_ascii=False))
for ci in c["items"][:5]:
    ed = ci["entityData"]
    print("   -", ed.get("id"), "root=", ed.get("rootCommentId"), "parent=", ed.get("parentCommentId"),
          repr(ed["text"][:70]))
