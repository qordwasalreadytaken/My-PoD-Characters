import json
import requests

from archive import CharacterArchive


CHAR_URL = "https://beta.pathofdiablo.com/api/characters/{}/summary"


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_character(name):
    response = requests.get(CHAR_URL.format(name))

    if response.status_code != 200:
        print(f"Failed to fetch {name}")
        return None

    return response.json()


def main():

    config = load_config()

    archive = CharacterArchive()

    for character in config["characters"]:

        print(f"Checking {character}...")

        data = fetch_character(character)

        if not data:
            continue

        char_archive = archive.load(character)

        if archive.add_snapshot(char_archive, data):

            archive.save(char_archive)

            print("  New snapshot saved.")

        else:

            print("  No changes.")


if __name__ == "__main__":
    main()