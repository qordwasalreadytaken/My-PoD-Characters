import argparse
import os
import json

from build_index import build_index

SNAPSHOT_DIR = "snapshots"
WATCHLIST_FILE = "watched_characters.json"


def remove_from_watchlist(character):
    if not os.path.exists(WATCHLIST_FILE):
        return False

    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        watched = json.load(f)

    if not isinstance(watched, list):
        print(f"{WATCHLIST_FILE} is not a JSON list.")
        return False

    target = character.casefold()

    updated = [
        name
        for name in watched
        if str(name).casefold() != target
    ]

    if len(updated) == len(watched):
        return False

    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)
        f.write("\n")

    return True

def parse_args():
    parser = argparse.ArgumentParser(description="Delete archived characters.")
    parser.add_argument(
        "--character",
        required=True,
        help="Character name to delete"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    import os

    target = args.character.casefold()
    filename = None

    for entry in os.listdir(SNAPSHOT_DIR):
        if not entry.endswith(".json"):
            continue

        if os.path.splitext(entry)[0].casefold() == target:
            filename = os.path.join(SNAPSHOT_DIR, entry)
            break

    if filename is None:
        print(f"{args.character} does not exist.")
        return

    os.remove(filename)

    print(f"Deleted {os.path.splitext(os.path.basename(filename))[0]}")

    if remove_from_watchlist(os.path.splitext(os.path.basename(filename))[0]):
        print("Removed from watchlist.")
        
    build_index()


if __name__ == "__main__":
    main()

