import json
import argparse
import os
import requests

from archive import CharacterArchive
from build_index import build_index


CHAR_URL = "https://beta.pathofdiablo.com/api/characters/{}/summary"
REQUEST_TIMEOUT_SECONDS = 20
MAX_FETCH_ATTEMPTS = 3
SNAPSHOT_DIR = "snapshots"


def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found. Create config.json with a 'characters' list first.")
        return None
    except json.JSONDecodeError as exc:
        print(f"config.json is invalid JSON: {exc}")
        return None


def load_characters_from_snapshots(snapshot_dir=SNAPSHOT_DIR):
    if not os.path.isdir(snapshot_dir):
        return []

    names = []
    for filename in sorted(os.listdir(snapshot_dir)):
        if not filename.endswith(".json"):
            continue
        names.append(os.path.splitext(filename)[0])

    return names


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch latest character snapshots.")
    parser.add_argument(
        "--source",
        choices=["config", "snapshots"],
        default="config",
        help="Character source: config file list or existing snapshots directory.",
    )
    return parser.parse_args()


def fetch_character(name):
    url = CHAR_URL.format(name)

    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)

            if response.status_code == 200:
                return response.json()

            print(f"  Attempt {attempt}/{MAX_FETCH_ATTEMPTS} failed for {name}: HTTP {response.status_code}")
        except requests.RequestException as exc:
            print(f"  Attempt {attempt}/{MAX_FETCH_ATTEMPTS} failed for {name}: {exc}")

    print(f"Failed to fetch {name} after {MAX_FETCH_ATTEMPTS} attempts.")
    return None


def main():
    args = parse_args()

    if args.source == "snapshots":
        characters = load_characters_from_snapshots()
        if not characters:
            print("No character snapshot files found in snapshots/.")
            return
    else:
        config = load_config()
        if not config:
            return

        characters = config.get("characters")
        if not isinstance(characters, list) or not characters:
            print("config.json must define a non-empty 'characters' list.")
            return

    archive = CharacterArchive()
    snapshots_added = 0

    for character in characters:

        print(f"Checking {character}...")

        data = fetch_character(character)

        if not data:
            continue

        char_archive = archive.load(character)

        if archive.add_snapshot(char_archive, data):

            archive.save(char_archive)
            snapshots_added += 1

            print("  New snapshot saved.")

        else:

            print("  No changes.")

    build_index()
    print(f"\nDone. Added {snapshots_added} new snapshot(s).")


if __name__ == "__main__":
    main()
