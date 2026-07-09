import json
import os
from datetime import datetime

SNAPSHOT_DIR = "snapshots"


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_index():

    config = load_config()

    index = {
        "version": 1,
        "generated": datetime.utcnow().isoformat() + "Z",
        "site": config["site"],
        "characters": []
    }

    for filename in sorted(os.listdir(SNAPSHOT_DIR)):

        if not filename.endswith(".json"):
            continue

        with open(os.path.join(SNAPSHOT_DIR, filename), encoding="utf-8") as f:
            archive = json.load(f)

        summary = archive.get("summary", {})

        index["characters"].append({
            "name": archive["character"],
            **summary
        })

    with open("index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"Built index for {len(index['characters'])} characters.")


if __name__ == "__main__":
    build_index()