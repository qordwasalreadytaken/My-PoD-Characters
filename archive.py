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
            payload = json.load(f)

        # Backward compatibility: older files stored a raw snapshot array.
        if isinstance(payload, list):
            return {
                "version": ARCHIVE_VERSION,
                "character": character,
                "snapshots": payload
            }

        if isinstance(payload, dict):
            payload.setdefault("version", ARCHIVE_VERSION)
            payload.setdefault("character", character)
            payload.setdefault("snapshots", [])
            return payload

        # Fallback for corrupted/unknown payload types.
        return {
            "version": ARCHIVE_VERSION,
            "character": character,
            "snapshots": []
        }


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

        latest = snapshots[-1] if isinstance(snapshots[-1], dict) else {}
        latest_data = latest.get("data", {})
        latest_stats = latest_data.get("Stats", {})

        archive["summary"] = {
            "class": latest_data.get("Class"),
            "level": latest_stats.get("Level", 0),
            "latestSnapshot": latest.get("id"),
            "snapshotCount": len(snapshots),
            "milestoneCount": sum(
                1 for s in snapshots
                if not s.get("metadata", {}).get("automatic", True)
            ),
            "lastUpdated": latest.get("timestamp")
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

    def _empty_changes(self):
        return {
            "skill_change": False,
            "equipped_change": False,
            "skills_added": [],
            "skills_removed": [],
            "skills_updated": [],
            "equipped_added": [],
            "equipped_removed": []
        }

    def _has_changes_payload(self, changes):
        if not isinstance(changes, dict):
            return False

        required = {
            "skill_change",
            "equipped_change",
            "skills_added",
            "skills_removed",
            "skills_updated",
            "equipped_added",
            "equipped_removed"
        }

        return required.issubset(changes.keys())

    def calculate_changes(self, previous_snapshot, current_snapshot):
        if not previous_snapshot or not current_snapshot:
            return self._empty_changes()

        previous_data = previous_snapshot.get("data") if isinstance(previous_snapshot, dict) else {}
        current_data = current_snapshot.get("data") if isinstance(current_snapshot, dict) else {}

        _, changes = self.compare(current_data or {}, previous_data or {})
        return changes

    def refresh_snapshot_changes(self, archive, only_missing=False):
        snapshots = archive.get("snapshots", [])
        updated = 0

        for index, snapshot in enumerate(snapshots):
            if not isinstance(snapshot, dict):
                continue

            existing = snapshot.get("changes")
            if only_missing and self._has_changes_payload(existing):
                continue

            if index == 0:
                snapshot["changes"] = self._empty_changes()
            else:
                snapshot["changes"] = self.calculate_changes(snapshots[index - 1], snapshot)

            updated += 1

        return updated

    def add_snapshot(
        self,
        archive,
        character_data,
        automatic=True,
        title=None,
        description=None,
        journal=None,
        tags=None,
        slug=None,
        favorite=False,
        always_create=False
    ):
        last = self.latest_snapshot(archive)

        if last:
            changed, changes = self.compare(
                character_data,
                last["data"]
            )

            if not changed and not always_create:
                return False

        else:
            changes = self._empty_changes()

        snapshot = {
            "id": uuid.uuid4().hex[:8],
            "timestamp": datetime.utcnow().isoformat() + "Z",

            "metadata": {
                "automatic": automatic,
                "title": title,
                "description": description,
                "journal": journal,
                "tags": tags or [],
                "slug": slug,
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