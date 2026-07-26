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

    filename = os.path.join(SNAPSHOT_DIR, f"{args.character}.json")

    if not os.path.exists(filename):
        print(f"{args.character} does not exist.")
        return

    os.remove(filename)

    print(f"Deleted {args.character}")

    build_index()


if __name__ == "__main__":
    main()