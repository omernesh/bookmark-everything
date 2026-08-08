# Bookmark Everything

Karakeep-style bookmarking with zero infrastructure: **no server, no UI, no external API.** Just markdown files, a stdlib-only Python CLI, and an optional semantic layer powered by a local Supermemory instance.

Drop a link in chat → it gets saved with AI-generated tags and a summary. Ask for it later → instant retrieval, by keyword **or** by meaning.

## How it works

- **Store:** `~/.hermes/bookmarks/` — one markdown file per bookmark (YAML frontmatter: title, url, date, tags, category, summary)
- **CLI:** `scripts/bm.py` — add / search / semantic / list / tags / categories / get / rm / export / index
- **Semantic layer:** bookmarks auto-index into a local [Supermemory](https://supermemory.ai) instance (localhost:6767, container `hermes-memory`) for meaning-based search
- **Agent integration:** Hermes skill (`SKILL.md`) that tells the agent how to save and retrieve on command

```
you drop a link ──▶ agent browses it ──▶ bm add
                                          ├──▶ ~/.hermes/bookmarks/<id>.md   (source of truth)
                                          └──▶ Supermemory doc (semantic index)
you ask "find that thing about X" ──▶ bm semantic / bm search ──▶ matching bookmark
```

## Install as a Hermes skill

```bash
ln -s ~/bookmark-everything ~/.hermes/skills/bookmark-everything
```

## Usage

```bash
# save (auto-indexes into Supermemory for semantic search)
python3 scripts/bm.py add "https://github.com/karakeep-app/karakeep" \
  --title "Karakeep — The Bookmark Everything App" \
  --tags "bookmarks,self-hosted,ai-tagging" \
  --category "tools" \
  --summary "Self-hostable bookmark app with AI tagging."

# keyword search (ranked across title/tags/category/summary/url)
python3 scripts/bm.py search "self-hosted bookmarks"
python3 scripts/bm.py search "bookmark" --tag "ai" --limit 5
python3 scripts/bm.py search "bookmark" --json   # machine-readable

# semantic search (meaning-based, via Supermemory; auto-falls back to keyword)
python3 scripts/bm.py semantic "framework for agent-driven slides"

# browse
python3 scripts/bm.py list                 # newest first
python3 scripts/bm.py list --tag "ai"
python3 scripts/bm.py list --category "tools"
python3 scripts/bm.py tags                 # tag counts
python3 scripts/bm.py categories           # category counts
python3 scripts/bm.py get <id>             # full bookmark

# maintenance
python3 scripts/bm.py index                # index bookmarks missing from Supermemory
python3 scripts/bm.py index --force        # full reindex
python3 scripts/bm.py export --format md   # full dump (backup / porting)
python3 scripts/bm.py export --format json
python3 scripts/bm.py rm <id>              # delete a bookmark
```

## Command reference

| Command | Description |
|---|---|
| `add <url>` | Save a bookmark. Auto-fetches the page title if `--title` not given; auto-indexes to Supermemory |
| `search <query>` | Keyword search, ranked by title > tags > category > summary > url |
| `semantic <query>` | Meaning-based search via Supermemory embeddings; falls back to keyword if server is down |
| `list` | List bookmarks (newest first), filter with `--tag` / `--category` |
| `tags` / `categories` | Show tag/category usage counts |
| `get <id>` | Show one bookmark (frontmatter + summary) |
| `index` | Push missing bookmarks to Supermemory (`--force` reindexes everything) |
| `export` | Full dump as markdown or JSON (backup / porting) |
| `rm <id>` | Delete a bookmark |

Common flags: `--json` (machine-readable output), `--limit N`.

## Semantic layer (Supermemory)

Every bookmark saved with `bm add` is pushed to the local Supermemory instance as a document containing title, url, tags, category and summary, tagged with metadata `{type: bookmark, id, url}` so semantic hits map back to the local files.

- **Auto-indexing:** happens on every `add`, best-effort. If Supermemory is down, the bookmark stays local-only and keyword-searchable — nothing is lost.
- **Deduplication:** an index marker file (`~/.hermes/bookmarks/.supermemory-indexed`) tracks which ids are already indexed, so `bm index` never creates duplicates.
- **Failure mode:** `bm semantic` degrades gracefully to `bm search` with a note when Supermemory is unreachable.
- **No credentials in this repo:** Supermemory auto-applies its API key for localhost requests. The semantic layer is optional — the bookmark store works fine without it.

## Features

- ✨ No dependencies (Python stdlib only)
- 🏷️ Tags + categories, ranked keyword search across all fields
- 🧠 Semantic search via local Supermemory — find bookmarks by meaning, not just words
- 📝 Human-readable markdown store — greppable, diffable, portable
- 🔌 Agent-friendly: designed to be driven by an AI agent, `--json` output for programmatic use
- 🛟 Graceful degradation — never breaks when the semantic layer is unavailable

## Layout

```
SKILL.md          # the Hermes skill (agent instructions)
README.md         # this file
scripts/bm.py     # the CLI (stdlib only)
```

Data lives in `~/.hermes/bookmarks/`, never in this repo.
