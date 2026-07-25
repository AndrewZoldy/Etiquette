import json, urllib.parse
from dzenlib import Dzen

d = Dzen(referer="https://dzen.ru/a/amNAZ54XI3753Qr_")
d.op.addheaders += [("X-Zen-Comments-Clid", "300"), ("X-Zen-Comments-Place", "article"),
                    ("X-Zen-Comments-Product", "zen")]

BASE = "https://dzen.ru/api/comments/v2/"
OID = "6a6340679e17237ef9dd0aff"
PUB = "63dd27aac30ab522dcce48b3"


def call(method, params=None, more=None):
    if more:
        url = BASE + method + "?" + more.lstrip("?&")
    else:
        url = BASE + method + "?" + urllib.parse.urlencode(params)
    return d.get_json(url)


r = call("root-comments", dict(documentId=f"native:{OID}", publicationPublisherId=PUB,
                               sorting="newest", batchSize="50", withConfig="true"))
print("meta:", json.dumps(r["meta"], ensure_ascii=False))
print("root items:", len(r["items"]))
print("moreItemsQueryString:", repr(r.get("moreItemsQueryString"))[:300])
print("other keys:", [k for k in r if k not in ("items", "usersById", "metaByCommentId")])

roots = [x["entityData"] for x in r["items"]]
mb = r["metaByCommentId"]
tot = 0
for rt in roots[:3]:
    cid = str(rt["id"])
    n = mb.get(cid, {}).get("childrenCount", 0)
    print(f"\nroot {cid} children={n} likes={mb.get(cid,{}).get('likes')} :: {rt['text'][:70]!r}")
    if n:
        c = call("child-comments", dict(rootCommentId=cid, documentId=f"native:{OID}",
                                        publicationPublisherId=PUB, withConfig="true"))
        print("   child items:", len(c["items"]), "more:", repr(c.get("moreItemsQueryString"))[:160])
        tot += len(c["items"])
        for ci in c["items"][:2]:
            ed = ci["entityData"]
            print("     -", ed.get("id"), ed.get("rootCommentId"), repr(ed["text"][:60]))
print("\nsample child total:", tot)
