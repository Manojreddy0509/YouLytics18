import json

def save_comments(comments, filename="comments.txt"):
    if filename.endswith(".json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
    else:
        with open(filename, "w", encoding="utf-8") as f:
            for comment in comments:
                f.write(comment + "\n")

# Remove or comment out this line:
# save_comments(comments, "comments.txt")

print("✅ Comments saved to all_comments.txt")
