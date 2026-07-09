import json

from archive import CharacterArchive
from fetch import fetch_character
from build_index import build_index


def load_config():
    with open("config.json", encoding="utf-8") as f:
        return json.load(f)


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


def main():

    config = load_config()

    character = choose_character(config["characters"])

    print()

    title = input("Title: ").strip() or None

    description = input("Description: ").strip() or None

    journal = multiline_input("Journal")

    if journal == "":
        journal = None

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
        always_create=True
    )

    archive.save(character_archive)

    build_index()

    print()
    print("Milestone snapshot created.")


if __name__ == "__main__":
    main()