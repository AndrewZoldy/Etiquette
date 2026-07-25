import re

b = open("raw/comments_bundle.js", encoding="utf-8").read()

for name in ("childCommentsEndpoint", "childRepliesEndpoint", "repliesEndpoint",
             "rootCommentsEndpoint", "popularCommentsEndpoint"):
    i = b.find(name)
    print("=" * 30, name, "at", i)
    if i > 0:
        print(b[i - 900:i + 1300])
        print()
