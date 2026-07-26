import json
import os

from build_index import build_index

SNAPSHOT_DIR = "snapshots"


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
        slug = str(snapshot.get("slug", ""))

        if slug.casefold() == target:
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


    snapshots = archive.get("snapshots", [])

    snapshot = find_snapshot(
        snapshots,
        args.snapshot
    )

    if snapshot is None:
        print(
            f"Snapshot '{args.snapshot}' not found "
            f"for {args.character}"
        )
        return


    metadata = snapshot.setdefault(
        "metadata",
        {}
    )


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


    tags = parse_tags(args.tags)

    if tags is not None:
        metadata["tags"] = tags
        changed = True


    if args.favorite != "Leave":
        metadata["favorite"] = (
            args.favorite == "Yes"
        )
        changed = True


    if args.story != "Leave":
        metadata["story"] = (
            args.story == "Yes"
        )
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