import argparse
import os

from archive import CharacterArchive, class_to_tag, dedupe_tags
from build_index import build_index


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill missing snapshot metadata tags (class/story/guide)."
    )
    parser.add_argument(
        "--character",
        help="Character name to process (defaults to all snapshot files)."
    )
    parser.add_argument(
        "--snapshot-dir",
        default="snapshots",
        help="Snapshot directory path."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview updates without saving files."
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


def normalize_tags(raw_value):
    if isinstance(raw_value, list):
        return [str(tag).strip() for tag in raw_value if str(tag).strip()]

    if isinstance(raw_value, str) and raw_value.strip():
        return [part.strip() for part in raw_value.split(",") if part.strip()]

    return []


def backfill_snapshot_tags(snapshot):
    if not isinstance(snapshot, dict):
        return False, {"class": 0, "story": 0, "guide": 0}

    metadata = snapshot.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        snapshot["metadata"] = metadata

    tags = dedupe_tags(normalize_tags(metadata.get("tags")))
    existing_keys = {tag.lower() for tag in tags}

    added = {"class": 0, "story": 0, "guide": 0}

    data = snapshot.get("data") if isinstance(snapshot.get("data"), dict) else {}
    class_tag = class_to_tag(data.get("Class"))
    if class_tag and class_tag.lower() not in existing_keys:
        tags.append(class_tag)
        existing_keys.add(class_tag.lower())
        added["class"] = 1

    if metadata.get("story") is True and "story" not in existing_keys:
        tags.append("story")
        existing_keys.add("story")
        added["story"] = 1

    guide_value = metadata.get("guide")
    has_guide = bool(guide_value and str(guide_value).strip())
    if has_guide and "guide" not in existing_keys:
        tags.append("guide")
        existing_keys.add("guide")
        added["guide"] = 1

    normalized = dedupe_tags(tags)
    changed = normalized != normalize_tags(metadata.get("tags"))

    if changed:
        metadata["tags"] = normalized

    return changed, added


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
    changed_snapshots = 0
    class_added = 0
    story_added = 0
    guide_added = 0

    for character in characters:
        payload = archive.load(character)
        snapshots = payload.get("snapshots", []) if isinstance(payload, dict) else []

        file_changed = False
        file_snapshot_updates = 0

        for snapshot in snapshots:
            changed, added = backfill_snapshot_tags(snapshot)
            if not changed:
                continue

            file_changed = True
            file_snapshot_updates += 1
            class_added += added["class"]
            story_added += added["story"]
            guide_added += added["guide"]

        if not file_changed:
            print(f"No tag updates needed for {character}.")
            continue

        changed_files += 1
        changed_snapshots += file_snapshot_updates

        if args.dry_run:
            print(f"Would update {character}: {file_snapshot_updates} snapshot(s).")
        else:
            archive.save(payload)
            print(f"Updated {character}: {file_snapshot_updates} snapshot(s).")

    if changed_files > 0 and not args.dry_run:
        build_index()

    mode = "Dry run" if args.dry_run else "Done"
    print(
        f"{mode}. Updated {changed_snapshots} snapshot(s) across {changed_files} archive file(s). "
        f"Added tags: class={class_added}, story={story_added}, guide={guide_added}."
    )


if __name__ == "__main__":
    main()
