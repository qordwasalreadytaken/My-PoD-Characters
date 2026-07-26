import argparse
import os

from build_index import build_index

SNAPSHOT_DIR = "snapshots"


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

    build_index()


if __name__ == "__main__":
    main()