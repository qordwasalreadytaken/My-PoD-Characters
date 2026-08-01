import json
import os
import argparse

from build_index import build_index

SNAPSHOT_DIR = "snapshots"

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Edit an existing character snapshot."
    )

    parser.add_argument(
        "--character",
        required=True,
        help="Character name"
    )

    parser.add_argument(
        "--snapshot",
        required=True,
        help="Snapshot ID or slug"
    )

    parser.add_argument(
        "--key",
        help="New snapshot key/slug"
    )

    parser.add_argument(
        "--title",
        help="New title (leave blank to keep)"
    )

    parser.add_argument(
        "--description",
        help="New description (leave blank to keep)"
    )

    parser.add_argument(
        "--journal",
        help="New journal (leave blank to keep)"
    )

    parser.add_argument(
        "--tags",
        help="New tags (comma-separated, leave blank to keep)"
    )

    parser.add_argument(
        "--favorite",
        choices=["Leave", "Yes", "No", "true", "false"],
        default="Leave"
    )

    parser.add_argument(
        "--story",
        choices=["Leave", "Yes", "No", "true", "false"],
        default="Leave"
    )

    parser.add_argument(
        "--guide",
        help="New guide (leave blank to keep)"
    )

    parser.add_argument(
        "--clear-guide",
        choices=["true", "false"],
        default="false",
        help="Remove existing guide URL"
    )

    return parser.parse_args()
    
def find_character_file(character):
    target = character.casefold()

    for filename in os.listdir(SNAPSHOT_DIR):
        if not filename.endswith(".json"):
            continue

        name = os.path.splitext(filename)[0]

        if name.casefold() == target:
            return os.path.join(SNAPSHOT_DIR, filename)

    return None


def find_snapshot(snapshots, key):
    target = key.casefold()

    for snapshot in snapshots:
        snapshot_id = str(snapshot.get("id", ""))

        metadata = snapshot.get("metadata", {})
        slug = str(metadata.get("slug", ""))

        if (
            snapshot_id.casefold() == target
            or slug.casefold() == target
        ):
            return snapshot

    return None


def parse_tags(value):
    if not value:
        return None

    return [
        tag.strip()
        for tag in value.split(",")
        if tag.strip()
    ]


def main():

    args = parse_args()

    path = find_character_file(args.character)

    if not path:
        print(f"Character not found: {args.character}")
        return


    with open(path, "r", encoding="utf-8") as f:
        archive = json.load(f)

    print(f"Loaded archive: {path}")
    print(f"Archive type: {type(archive)}")
    print(f"Archive keys: {archive.keys() if isinstance(archive, dict) else 'not dict'}")

    snapshots = archive.get("snapshots", [])

    print(f"Found {len(snapshots)} snapshots")

    for s in snapshots[:5]:
        print(
            "Snapshot:",
            "id=", s.get("id"),
            "slug=", s.get("metadata", {}).get("slug")
        )
        
        snapshot = find_snapshot(
        snapshots,
        args.snapshot
    )

    if snapshot is None:
        print(
            f"Snapshot '{args.snapshot}' not found "
            f"for {args.character}"
        )

        print("Available IDs:")
        for s in snapshots:
            print(" -", s.get("id"))

        return


    metadata = snapshot.setdefault("metadata", {})


    changed = False


    if args.title:
        metadata["title"] = args.title
        changed = True

    if args.key:
        metadata["slug"] = args.key
        changed = True

    if args.description:
        metadata["description"] = args.description
        changed = True


    if args.journal:
        metadata["journal"] = (
            args.journal.replace("\\n", "\n")
        )
        changed = True

    if args.clear_guide == "true":
        if "guide" in metadata:
            del metadata["guide"]
            changed = True

    elif args.guide:
        metadata["guide"] = args.guide
        changed = True

    tags = parse_tags(args.tags)

    if tags is not None:
        metadata["tags"] = tags
        changed = True


    if args.favorite != "Leave":
        metadata["favorite"] = args.favorite.lower() in ("yes", "true")
        changed = True


    if args.story != "Leave":
        metadata["story"] = args.story.lower() in ("yes", "true")
        changed = True

    if not changed:
        print("No changes requested.")
        return


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            archive,
            f,
            indent=2,
            ensure_ascii=False
        )
        f.write("\n")


    print(
        f"Updated {args.character} "
        f"snapshot {args.snapshot}"
    )

    build_index()

if __name__ == "__main__":
    main()