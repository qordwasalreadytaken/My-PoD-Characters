import argparse
import json
import os

from build_index import build_index


SNAPSHOT_DIR = "snapshots"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Edit an existing character snapshot."
    )

    parser.add_argument("--character", required=True)
    parser.add_argument("--snapshot", required=True)

    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--journal")
    parser.add_argument("--tags")

    parser.add_argument(
        "--favorite",
        choices=["Leave", "Yes", "No"],
        default="Leave"
    )

    parser.add_argument(
        "--story",
        choices=["Leave", "Yes,No"],
        default="Leave"
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


def parse_tags(value):

    if not value:
        return None

    return [
        tag.strip()
        for tag in value.split(",")
        if tag.strip()
    ]


def update_bool(current, value):

    if value == "Yes":
        return True

    if value == "No":
        return False

    return current


def main():

    args = parse_args()

    path = find_character_file(args.character)

    if not path:
        print(f"Character not found: {args.character}")
        return


    with open(path, "r", encoding="utf-8") as f:
        archive = json.load(f)


    snapshots = archive.get("snapshots", [])

    target = None

    for snapshot in snapshots:

        key = str(snapshot.get("key", ""))

        if key.casefold() == args.snapshot.casefold():
            target = snapshot
            break


    if target is None:
        print(
            f"Snapshot '{args.snapshot}' not found for {args.character}"
        )
        return


    changed = False


    if args.title:
        target["title"] = args.title
        changed = True


    if args.description:
        target["description"] = args.description
        changed = True


    if args.journal:
        target["journal"] = args.journal.replace("\\n", "\n")
        changed = True


    tags = parse_tags(args.tags)

    if tags is not None:
        target["tags"] = tags
        changed = True


    if args.favorite != "Leave":
        target["favorite"] = args.favorite == "Yes"
        changed = True


    if args.story != "Leave":
        target["story"] = args.story == "Yes"
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


    print(f"Updated {args.character} snapshot {args.snapshot}")

    build_index()


if __name__ == "__main__":
    main()