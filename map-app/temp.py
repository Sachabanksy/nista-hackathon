import os
import json
import csv
from io import StringIO

base_dir = r"C:\Users\SBanks\Downloads\NISTA_Hackathon_Dec_25\map-app"
data_dir = os.path.join(base_dir, "data", "blue_sky")
output_csv = os.path.join(base_dir, "blue_sky_top_posts.csv")

rows = []

# Read all monthly_summary_*.json files
for filename in os.listdir(data_dir):
    if not (filename.endswith(".json") and filename.startswith("monthly_summary_")):
        continue

    file_path = os.path.join(data_dir, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    year = data.get("year")
    month_label = data.get("month")  # e.g. "November 2025"
    top_posts = data.get("top_posts", {})

    # top_posts is a dict: { "HS2": [ {...}, {...} ], "Sizewell C": [ ... ], ... }
    for topic, posts in top_posts.items():
        for post in posts:
            row = {
                "year": year,
                "month": month_label,
                "topic": topic,
                "author": post.get("author"),
                "text": post.get("text"),
                "likes": post.get("likes"),
                "reposts": post.get("reposts"),
                "replies": post.get("replies"),
                "created_at": post.get("created_at"),
            }
            rows.append(row)

# Sort rows by created_at (string sort works for ISO timestamps)
rows.sort(key=lambda r: r["created_at"] or "")

fieldnames = [
    "year",
    "month",
    "topic",
    "author",
    "text",
    "likes",
    "reposts",
    "replies",
    "created_at",
]

# Write one big CSV to disk
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Wrote {len(rows)} rows to {output_csv}")
