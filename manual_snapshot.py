import json
import argparse

from archive import CharacterArchive
from fetch import fetch_character
from build_index import build_index


def load_config():
    try:
        with open("config.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found. Create config.json with a 'characters' list first.")
        return None
    except json.JSONDecodeError as exc:
        print(f"config.json is invalid JSON: {exc}")
        return None


def choose_character(characters):

    print()
    print("Characters")
    print("----------")

    for i, character in enumerate(characters, start=1):
        print(f"{i}) {character}")

    print()

    while True:

        choice = input("Select character: ").strip()

        try:
            choice = int(choice)

            if 1 <= choice <= len(characters):
                return characters[choice - 1]

        except ValueError:
            pass

        print("Invalid selection.")


def multiline_input(prompt):

    print()
    print(prompt)
    print("(Finish with a blank line)")
    print()

    lines = []

    while True:

        line = input()

        if line == "":
            break

        lines.append(line)

    return "\n".join(lines)


def parse_tags(tags_raw):
    if not tags_raw:
        return []

    return [part.strip() for part in tags_raw.split(",") if part.strip()]


def parse_bool(raw_value):
    if isinstance(raw_value, bool):
        return raw_value

    lowered = str(raw_value).strip().lower()
    return lowered in {"1", "true", "yes", "y", "on"}


def parse_args():
    parser = argparse.ArgumentParser(description="Create a manual milestone snapshot for one character.")
    parser.add_argument("--character", help="Character name to snapshot (skips interactive picker)")
    parser.add_argument("--title", help="Milestone title")
    parser.add_argument("--description", help="Milestone description")
    parser.add_argument("--journal", help="Milestone journal text")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--slug", help="Optional URL-friendly snapshot key")
    parser.add_argument("--favorite", default="false", help="Mark snapshot as favorite (true/false)")
    return parser.parse_args()


def main():
    args = parse_args()

    config = load_config()
    characters = config.get("characters", []) if config else []

    if args.character:
        character = args.character.strip()
        if not character:
            print("--character cannot be blank.")
            return

        title = args.title.strip() if args.title else None
        description = args.description.strip() if args.description else None
        journal = args.journal.strip() if args.journal else None
        tags = parse_tags(args.tags)
        slug = args.slug.strip() if args.slug else None
        favorite = parse_bool(args.favorite)
    else:
        if not isinstance(characters, list) or not characters:
            print("config.json must define a non-empty 'characters' list when running interactively.")
            return

        character = choose_character(characters)

        print()

        title = input("Title: ").strip() or None

        description = input("Description: ").strip() or None

        journal = multiline_input("Journal")
        journal = journal if journal != "" else None

        tags = parse_tags(input("Tags (comma-separated): ").strip())
        slug = input("Slug (optional): ").strip() or None
        favorite = parse_bool(input("Favorite? (y/N): ").strip() or "false")

    print()
    print("Fetching latest character...")

    data = fetch_character(character)

    if data is None:
        print("Unable to fetch character.")
        return

    archive = CharacterArchive()

    character_archive = archive.load(character)

    archive.add_snapshot(
        character_archive,
        data,
        automatic=False,
        title=title,
        description=description,
        journal=journal,
        tags=tags,
        slug=slug,
        favorite=favorite,
        always_create=True
    )

    archive.save(character_archive)

    build_index()

    print()
    print("Milestone snapshot created.")


if __name__ == "__main__":
    main()