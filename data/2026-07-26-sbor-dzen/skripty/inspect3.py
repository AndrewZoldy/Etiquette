import json

d = json.load(open("raw/launcher_export.txt", encoding="utf-8"))
it = [x for x in d["items"] if x.get("item_type") == "native"][0]

for k in ("comments_link", "all_comments_link", "one_comment_link", "comments_document_id",
          "comments_token", "share_link", "publication_id", "publication_object_id",
          "stats", "views", "socialInfo", "interests", "card_type", "creation_time",
          "publication_date", "timeToReadSeconds"):
    print(f"### {k}:")
    print(json.dumps(it.get(k), ensure_ascii=False)[:900])
    print()

print("### image:")
print(json.dumps(it.get("image"), ensure_ascii=False)[:1200])
print("\n### common_image:")
print(json.dumps(it.get("common_image"), ensure_ascii=False)[:800])
print("\n### image_squared:")
print(json.dumps(it.get("image_squared"), ensure_ascii=False)[:400])
print("\n### more:")
print(json.dumps(it.get("more"), ensure_ascii=False)[:600])
