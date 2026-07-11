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
WATCHLIST_FILE = "watched_characters.json"


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


def load_characters_from_watchlist(path=WATCHLIST_FILE):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"{path} is invalid JSON: {exc}")
        return []

    if not isinstance(payload, list):
        print(f"{path} must contain a JSON list of character names.")
        return []

    names = []
    for item in payload:
        value = str(item).strip()
        if value:
            names.append(value)

    return names


def save_watchlist(characters, path=WATCHLIST_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2)
        f.write("\n")


def dedupe_names(names):
    deduped = []
    seen = set()

    for raw in names:
        name = str(raw).strip()
        if not name:
            continue

        key = name.lower()
        if key in seen:
            continue

        seen.add(key)
        deduped.append(name)

    return deduped


def parse_character_tokens(values):
    names = []
    for value in values:
        for token in str(value).split(","):
            cleaned = token.strip()
            if cleaned:
                names.append(cleaned)
    return names


def load_names_from_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"Watchlist import file not found: {path}")
        return []

    stripped = raw.strip()
    if not stripped:
        return []

    try:
        payload = json.loads(stripped)
        if isinstance(payload, list):
            return [str(item).strip() for item in payload if str(item).strip()]
    except json.JSONDecodeError:
        pass

    return [line.strip() for line in stripped.splitlines() if line.strip() and not line.strip().startswith("#")]


def handle_watchlist_commands(args):
    managed = False

    names_to_add = []
    if args.add_watched:
        names_to_add.extend(parse_character_tokens(args.add_watched))

    if args.add_watched_file:
        names_to_add.extend(load_names_from_file(args.add_watched_file))

    if names_to_add:
        managed = True
        existing = load_characters_from_watchlist(args.watchlist_file)
        merged = dedupe_names(existing + names_to_add)
        save_watchlist(merged, args.watchlist_file)
        print(f"Saved {len(merged)} watched character(s) to {args.watchlist_file}.")

        added_keys = {name.lower() for name in existing}
        newly_added = [name for name in merged if name.lower() not in added_keys]
        if newly_added:
            print(f"Newly added: {', '.join(newly_added)}")

    if args.list_watched:
        managed = True
        watched = load_characters_from_watchlist(args.watchlist_file)
        if not watched:
            print(f"No watched characters found in {args.watchlist_file}.")
        else:
            print(f"Watched characters ({len(watched)}):")
            for name in dedupe_names(watched):
                print(f" - {name}")

    return managed


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch latest character snapshots.")
    parser.add_argument(
        "--source",
        choices=["config", "snapshots", "watched", "combined"],
        default="config",
        help="Character source: config list, existing snapshots, watched list, or combined snapshots+watched.",
    )
    parser.add_argument(
        "--watchlist-file",
        default=WATCHLIST_FILE,
        help="Path to watched character JSON list.",
    )
    parser.add_argument(
        "--add-watched",
        nargs="+",
        help="Add character names to watched list (supports comma-separated values).",
    )
    parser.add_argument(
        "--add-watched-file",
        help="Import watched names from a file (JSON list or one-name-per-line text).",
    )
    parser.add_argument(
        "--list-watched",
        action="store_true",
        help="List watched characters and exit unless --run is also provided.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run snapshot fetch after watchlist add/list operations.",
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

    managed = handle_watchlist_commands(args)
    if managed and not args.run:
        return

    if args.source == "snapshots":
        characters = load_characters_from_snapshots()
        if not characters:
            print("No character snapshot files found in snapshots/.")
            return
    elif args.source == "watched":
        characters = load_characters_from_watchlist(args.watchlist_file)
        if not characters:
            print(f"No watched characters found in {args.watchlist_file}.")
            return
    elif args.source == "combined":
        snapshot_characters = load_characters_from_snapshots()
        watched_characters = load_characters_from_watchlist(args.watchlist_file)
        characters = dedupe_names(snapshot_characters + watched_characters)
        if not characters:
            print("No characters found in snapshots/ or watched list.")
            return
    else:
        config = load_config()
        if not config:
            return

        characters = config.get("characters")
        if not isinstance(characters, list) or not characters:
            print("config.json must define a non-empty 'characters' list.")
            return

    characters = dedupe_names(characters)

    archive = CharacterArchive()
    snapshots_added = 0

    for character in characters:

        print(f"Checking {character}...")

        data = fetch_character(character)

        if not data:
            continue

        char_archive = archive.load(character)
        archive.refresh_snapshot_changes(char_archive, only_missing=True)

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
