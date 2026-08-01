# The Journaling Nephalem

Capture your Path of Diablo journey one snapshot at a time.

The Journaling Nephalem is a character archive that automatically records snapshots of your Path of Diablo characters. Track equipment upgrades, level progression, skills, and personal milestones throughout a season, then preserve your character's history long after the ladder resets.

Unlike a traditional armory, The Journaling Nephalem lets you tell the story of your character. Add journal entries, tag memorable moments, mark favorite snapshots, and browse exactly how your build evolved over time.

> Every hero has a story. Don't let yours disappear at ladder reset.

---


## Features

- Automatic character snapshots
- Journal entries for memorable moments
- Favorite important snapshots
- Custom tags for organization
- Interactive armory viewer
- Browse every snapshot from a searchable timeline
- Track equipment and skill changes between snapshots
- Story mode for navigating milestone snapshots
- JSON-based archive that's easy to back up or modify


## Screenshots

### Dashboard

![Dashboard View](image.png)

### Armory

![Armory Pages](image-1.png)

### Story Navigation

![Tell a story through snapshots](image-2.png)


## Why?

Every Path of Diablo ladder eventually ends.

Characters disappear from the official armory, memories fade, and record of that perfect gear progression is gone forever.

The Journaling Nephalem solves that problem by keeping your own permanent archive. Every snapshot becomes part of your character's history, allowing you to look back at your journey months or even years later.


## Quick Start

1. Fork this repo.
2. Enable GitHub Actions.
3. Add your character names.
4. Run the initial snapshot workflow.
5. Enable the scheduled workflow.
6. Visit your GitHub Pages site.

That's it.


## How It Works

The Journaling Nephalem is entirely powered by GitHub.

GitHub Actions periodically query the Path of Diablo API and save snapshots of your characters. Those snapshots are committed back into your repository, and GitHub Pages automatically publishes a static website for browsing your character history.

Because everything is stored in your own repository:

- Your archive is permanent.
- No database or web server is required.
- The entire site can be hosted for free using GitHub Pages.


## Creating Milestones

Automatic snapshots are great for recording your character's progression, but not every moment is equally memorable.

Milestone snapshots let you capture the moments that matter.

Examples include:

- Capturing a moment in time to feature in a build guide
- Finding your first high rune
- Completing your endgame build
- Defeating Diablo Clone
- Reaching level 99
- Beginning a new build
- Regrettable Respec's

Milestones can include:

- Custom title
- Description
- Journal entry
- Tags
- Favorite status
- Story marker


## Story Snapshots

Mark any milestone as part of your character's story.

The armory includes Story Navigation, allowing you to jump directly between important milestones while skipping routine automatic snapshots.

This creates a curated timeline of your character's journey.


## Github Actions

| Workflow                  | Purpose                            |
| ------------------------- | ---------------------------------- |
| Create Milestone Snapshot | Capture a manual snapshot/Milestone         |
| Edit Snapshot             | Edit an existing snapshot                    |
| Delete Character          | Remove a character                 |
| Daily All Characters Snapshot      | Automatically creates daily snapshots for all characters added    |

