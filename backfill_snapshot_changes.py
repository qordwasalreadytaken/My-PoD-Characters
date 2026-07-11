import argparse
import os

from archive import CharacterArchive
from build_index import build_index


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill/recompute snapshot changes for character archives."
    )
    parser.add_argument(
        "--character",
        help="Character name to process (defaults to all snapshot files)."
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only fill missing or malformed changes payloads; do not overwrite valid ones."
    )
    parser.add_argument(
        "--snapshot-dir",
        default="snapshots",
        help="Snapshot directory path."
    )
    return parser.parse_args()


def list_characters(snapshot_dir):
    if not os.path.isdir(snapshot_dir):
        return []

    names = []
    for filename in sorted(os.listdir(snapshot_dir)):
        if not filename.endswith(".json"):
            continue
        names.append(os.path.splitext(filename)[0])

    return names


def main():
    args = parse_args()

    archive = CharacterArchive(archive_dir=args.snapshot_dir)

    if args.character:
        characters = [args.character.strip()]
    else:
        characters = list_characters(args.snapshot_dir)

    characters = [name for name in characters if name]

    if not characters:
        print("No snapshot files found.")
        return

    changed_files = 0
    updated_snapshots = 0

    for character in characters:
        payload = archive.load(character)
        updated = archive.refresh_snapshot_changes(payload, only_missing=args.only_missing)

        if updated > 0:
            archive.save(payload)
            changed_files += 1
            updated_snapshots += updated
            print(f"Updated {character}: {updated} snapshot(s).")
        else:
            print(f"No changes needed for {character}.")

    if changed_files > 0:
        build_index()

    print(
        f"Done. Updated {updated_snapshots} snapshot(s) across {changed_files} archive file(s)."
    )


if __name__ == "__main__":
    main()
