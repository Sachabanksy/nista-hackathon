import os
import json

base_dir = r"C:\Users\SBanks\Downloads\NISTA_Hackathon_Dec_25\map-app"
data_dir = os.path.join(base_dir, "data", "blue_sky")

files = os.listdir(data_dir)

for file in files:
    if file.endswith(".json"):
        file_path = os.path.join(data_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Contents of {file}:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
