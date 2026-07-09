import json
import os
import re
from datetime import datetime
from urllib.parse import urlencode

SNAPSHOT_DIR = "snapshots"


def slugify(value):
    if not isinstance(value, str):
        return ""

    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def make_share_url(base_url, character_name, key):
    query = urlencode({"c": character_name, "t": key})

    if base_url:
        trimmed = base_url.rstrip("/")
        return f"{trimmed}/character.html?{query}"

    return f"character.html?{query}"


def compute_summary(archive):
    summary = archive.get("summary")
    if isinstance(summary, dict) and summary:
        return summary

    snapshots = archive.get("snapshots", [])
    if not snapshots:
        return {
            "class": None,
            "level": 0,
            "latestSnapshot": None,
            "snapshotCount": 0,
            "milestoneCount": 0,
            "lastUpdated": None,
        }

    latest = snapshots[-1]
    latest_data = latest.get("data", {}) if isinstance(latest, dict) else {}
    latest_stats = latest_data.get("Stats", {}) if isinstance(latest_data, dict) else {}

    milestone_count = 0
    for snap in snapshots:
        if not isinstance(snap, dict):
            continue
        metadata = snap.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("automatic") is False:
            milestone_count += 1

    return {
        "class": latest_data.get("Class"),
        "level": latest_stats.get("Level", 0),
        "latestSnapshot": latest.get("id") if isinstance(latest, dict) else None,
        "snapshotCount": len(snapshots),
        "milestoneCount": milestone_count,
        "lastUpdated": latest.get("timestamp") if isinstance(latest, dict) else None,
    }


def build_snapshot_links(archive, character_name, site_base_url):
    snapshots = archive.get("snapshots", [])
    links = []
    used_keys = set()

    for snap in snapshots:
        if not isinstance(snap, dict):
            continue

        metadata = snap.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        timestamp = snap.get("timestamp")
        snap_id = snap.get("id")

        raw_key = ""
        if isinstance(metadata.get("slug"), str) and metadata.get("slug").strip():
            raw_key = slugify(metadata.get("slug"))
        elif isinstance(metadata.get("title"), str) and metadata.get("title").strip():
            raw_key = slugify(metadata.get("title"))
        elif isinstance(snap_id, str) and snap_id.strip():
            raw_key = snap_id.strip()
        elif isinstance(timestamp, str) and timestamp.strip():
            raw_key = timestamp.strip()

        if not raw_key:
            continue

        key = raw_key
        suffix = 2
        while key in used_keys:
            key = f"{raw_key}-{suffix}"
            suffix += 1
        used_keys.add(key)

        label = metadata.get("title") or timestamp or key
        is_milestone = metadata.get("automatic") is False
        canonical_key = timestamp or key
        tags = metadata.get("tags")
        if isinstance(tags, list):
            tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        elif isinstance(tags, str) and tags.strip():
            tags = [part.strip() for part in tags.split(",") if part.strip()]
        else:
            tags = []

        links.append({
            "label": label,
            "key": key,
            "timestamp": timestamp,
            "id": snap_id,
            "title": metadata.get("title"),
            "tags": tags,
            "automatic": not is_milestone,
            "url": make_share_url(site_base_url, character_name, key),
            "canonicalUrl": make_share_url(site_base_url, character_name, canonical_key),
        })

    links.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return links


def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        print(f"Warning: config.json is invalid JSON ({exc}); using defaults.")
        return {}


def build_index():

    config = load_config()

    index = {
        "version": 1,
        "generated": datetime.utcnow().isoformat() + "Z",
        "site": config.get("site", {}),
        "linksGenerated": True,
        "characters": []
    }

    site_config = config.get("site", {})
    site_base_url = site_config.get("baseUrl") if isinstance(site_config, dict) else None

    if not os.path.isdir(SNAPSHOT_DIR):
        with open("index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
        print("Built index for 0 characters.")
        return

    for filename in sorted(os.listdir(SNAPSHOT_DIR)):

        if not filename.endswith(".json"):
            continue

        with open(os.path.join(SNAPSHOT_DIR, filename), encoding="utf-8") as f:
            payload = json.load(f)

        if isinstance(payload, dict):
            archive = payload
        elif isinstance(payload, list):
            # Backward compatibility for legacy snapshot array files.
            character_name = os.path.splitext(filename)[0]
            archive = {
                "character": character_name,
                "summary": {},
                "snapshots": payload
            }
        else:
            continue

        summary = archive.get("summary", {})
        character_name = archive.get("character", os.path.splitext(filename)[0])

        summary = compute_summary(archive)
        snapshot_links = build_snapshot_links(archive, character_name, site_base_url)

        index["characters"].append({
            "name": character_name,
            **summary,
            "snapshotLinks": snapshot_links,
        })

    index["characters"].sort(key=lambda char: str(char.get("name", "")).lower())

    with open("index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"Built index for {len(index['characters'])} characters.")


if __name__ == "__main__":
    build_index()