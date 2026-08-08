# Bookmark Everything

Karakeep-style bookmarking with zero infrastructure: **no server, no UI, no external API.** Just markdown files and a stdlib-only Python CLI.

Drop a link in chat → it gets saved with AI-generated tags and a summary. Ask for it later → instant retrieval.

## How it works

- **Store:** `~/.hermes/bookmarks/` — one markdown file per bookmark (YAML frontmatter: title, url, date, tags, category, summary)
- **CLI:** `scripts/bm.py` — add / search / list / tags / categories / get / rm / export
- **Agent integration:** Hermes skill (`SKILL.md`) that tells the agent how to save and retrieve on command

## Usage

```bash
# save
python3 scripts/bm.py add "https://github.com/karakeep-app/karakeep" \
  --title "Karakeep — The Bookmark Everything App" \
  --tags "bookmarks,self-hosted,ai-tagging" \
  --category "tools" \
  --summary "Self-hostable bookmark app with AI tagging."

# search
python3 scripts/bm.py search "self-hosted bookmarks"
python3 scripts/bm.py list --tag "ai"
python3 scripts/bm.py tags

# full dump (backup / porting)
python3 scripts/bm.py export --format json
```

## Features

- ✨ No dependencies (Python stdlib only)
- 🏷️ Tags + categories, ranked search across all fields
- 📝 Human-readable markdown store — greppable, diffable, portable
- 🤖 Agent-friendly: `--json` output for programmatic use

## Install as a Hermes skill

```bash
ln -s ~/bookmark-everything ~/.hermes/skills/bookmark-everything
```

## Layout

```
SKILL.md          # the Hermes skill (agent instructions)
scripts/bm.py     # the CLI
```

Data lives in `~/.hermes/bookmarks/`, never in this repo.
