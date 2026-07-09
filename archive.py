import copy
import json
import os
import uuid
from datetime import datetime
from collections import Counter


ARCHIVE_VERSION = 1


class CharacterArchive:
    def __init__(self, archive_dir="snapshots"):
        self.archive_dir = archive_dir
        os.makedirs(self.archive_dir, exist_ok=True)

    def _path(self, character):
        return os.path.join(self.archive_dir, f"{character.lower()}.json")

    def load(self, character):
        path = self._path(character)

        if not os.path.exists(path):
            return {
                "version": ARCHIVE_VERSION,
                "character": character,
                "snapshots": []
            }

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


    def update_summary(self, archive):
        snapshots = archive["snapshots"]

        if not snapshots:
            archive["summary"] = {
                "class": None,
                "level": 0,
                "latestSnapshot": None,
                "snapshotCount": 0,
                "milestoneCount": 0,
                "lastUpdated": None
            }
            return

        latest = snapshots[-1]

        archive["summary"] = {
            "class": latest["data"].get("Class"),
            "level": latest["data"]["Stats"].get("Level"),
            "latestSnapshot": latest["id"],
            "snapshotCount": len(snapshots),
            "milestoneCount": sum(
                1 for s in snapshots
                if not s["metadata"]["automatic"]
            ),
            "lastUpdated": latest["timestamp"]
        }

    def save(self, archive):

        self.update_summary(archive)

        path = self._path(archive["character"])

        with open(path, "w", encoding="utf-8") as f:
            json.dump(archive, f, indent=2)

    def latest_snapshot(self, archive):
        if not archive["snapshots"]:
            return None

        return archive["snapshots"][-1]

    def add_snapshot(
        self,
        archive,
        character_data,
        automatic=True,
        title=None,
        description=None,
        journal=None,
        tags=None,
        favorite=False,
        always_create=False
    ):
        last = self.latest_snapshot(archive)

        if last and not always_create:
            changed, changes = self.compare(
                last["data"],
                character_data
            )

            if not changed:
                return False

        else:
            changes = {
                "skill_change": False,
                "equipped_change": False,
                "skills_added": [],
                "skills_removed": [],
                "skills_updated": [],
                "equipped_added": [],
                "equipped_removed": []
            }

        snapshot = {
            "id": uuid.uuid4().hex[:8],
            "timestamp": datetime.utcnow().isoformat() + "Z",

            "metadata": {
                "automatic": automatic,
                "title": title,
                "description": description,
                "journal": journal,
                "tags": tags or [],
                "favorite": favorite
            },

            "changes": changes,

            "data": copy.deepcopy(character_data)
        }

        archive["snapshots"].append(snapshot)

        return True

    def compare(self, new_data, old_data):

        def skills(data):
            result = {}

            for tab in data.get("SkillTabs", []):
                for skill in tab.get("Skills", []):
                    result[skill["Name"]] = skill["Level"]

            return result

        def equipment(data):
            equipped = []

            for item in data.get("Equipped", []):
                equipped.append(item.get("Title", ""))

            return Counter(sorted(equipped))

        new_skills = skills(new_data)
        old_skills = skills(old_data)

        new_items = equipment(new_data)
        old_items = equipment(old_data)

        changes = {
            "skill_change": new_skills != old_skills,
            "equipped_change": new_items != old_items,

            "skills_added": [],
            "skills_removed": [],
            "skills_updated": [],

            "equipped_added": [],
            "equipped_removed": []
        }

        for skill in sorted(new_skills.keys() - old_skills.keys()):
            changes["skills_added"].append(skill)

        for skill in sorted(old_skills.keys() - new_skills.keys()):
            changes["skills_removed"].append(skill)

        for skill in sorted(new_skills.keys() & old_skills.keys()):
            if new_skills[skill] != old_skills[skill]:
                changes["skills_updated"].append({
                    "name": skill,
                    "from": old_skills[skill],
                    "to": new_skills[skill]
                })

        for item, count in (new_items - old_items).items():
            changes["equipped_added"] += [item] * count

        for item, count in (old_items - new_items).items():
            changes["equipped_removed"] += [item] * count

        changed = (
            changes["skill_change"] or
            changes["equipped_change"]
        )

        return changed, changes