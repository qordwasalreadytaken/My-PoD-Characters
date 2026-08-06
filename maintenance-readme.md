## Backfilling Snapshot Tags

If you have older snapshots that are missing automatic tags, run the backfill script.

This script updates snapshot metadata tags to include:

- Class tag (`Asn`, `Ama`, `Barb`, `Druid`, `Necro`, `Pal`, `Sorc`) based on character class
- `story` when snapshot metadata has `story: true`
- `guide` when snapshot metadata has a non-empty guide value

It only adds missing tags and deduplicates tags case-insensitively.

Preview changes without writing files:

```bash
python3 backfill_snapshot_tags.py --dry-run
```

Apply changes to all character archives and rebuild `index.json`:

```bash
python3 backfill_snapshot_tags.py
```

Run against a single character:

```bash
python3 backfill_snapshot_tags.py --character SkillIssue
```

Use a custom snapshot directory:

```bash
python3 backfill_snapshot_tags.py --snapshot-dir snapshots
```

