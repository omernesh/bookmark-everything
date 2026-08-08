---
name: bookmark-everything
description: Save, organize, and retrieve the user's bookmarks/links as markdown files. Use when the user sends a URL to save, asks to find a previously saved link, or wants his link library searched.
metadata:
  tags: [bookmarks, links, save, organize, read-it-later, search]
  home_channels: [telegram]
  instructions: When the user sends a URL in any chat, browse it to understand what it is, then save it to the bookmark store with AI-generated tags. When the user asks to find a saved link, search the store and reply with the matches.
---

# Bookmark Everything

Karakeep-style bookmarking with zero infrastructure: no server, no UI, no external API. Just markdown files + a stdlib Python CLI. When the user drops a link in chat, Sammie saves it. When he asks for something, Sammie searches and returns it.

## Storage

- **Location:** `~/.hermes/bookmarks/` — one markdown file per bookmark
- **Filename:** `<YYYYMMDD>-<slug>.md`
- **Format:** YAML frontmatter + summary body:

```markdown
---
id: 20260808-karakeep
title: Karakeep — The Bookmark Everything App
url: https://github.com/karakeep-app/karakeep
date: 2026-08-08T19:00:00+03:00
tags: [bookmarks, self-hosted, ai-tagging]
category: tools
---

## Summary

Self-hostable bookmark app: links, notes, images, AI tagging, full-text search.
```

- **CLI:** `python3 ~/bookmark-everything/scripts/bm.py <cmd>` (alias: `bm`)

## Workflow: Save a Link (the user sends a URL)

1. **Browse the URL first** — understand what it actually is (web_extract or browser).
2. **Title:** use the real page/repo title, not the raw URL.
3. **Summary:** 1–3 sentences, concrete. What it does, why it matters, any key tech.
4. **Tags (3–6):** lowercase, short, descriptive. Mix of domain (`ai`, `dev`, `self-hosted`, `crypto`, `sports`) and project-specific (`grouppics`, `chatlytics`, `supabase`). Project names and proper nouns keep their case (`karakeep`, `openrouter`).
5. **Category:** one of: `tools`, `dev`, `ai`, `read-later`, `project`, `business`, `sports`, `personal`, `misc`. Choose the best fit.
6. Save:
   ```bash
   bm add "<url>" --title "..." --tags "tag1,tag2,tag3" --category "tools" --summary "..."
   ```
7. Confirm to the user: id + title + tags. Keep it short.

## Workflow: Retrieve (the user asks for a saved link)

```bash
bm search "<query>"            # ranked by title/tags/category/summary/url
bm search "<query>" --json     # machine-readable, for parsing in replies
bm list --tag "ai"             # browse by tag
bm list --category "tools"     # browse by category
bm tags                        # tag cloud with counts
bm get <id>                    # full bookmark (frontmatter + summary)
```

Then reply with the best match(es): title, url, tags. If nothing matches, say so plainly — do not invent links.

## Conventions

- **Never delete** a bookmark unless the user explicitly asks.
- **Never store secrets** in summaries or tags (API keys, tokens, passwords).
- **Keep tags consistent** — reuse existing tags (check `bm tags`) before inventing new ones.
- If a URL fails to load, save it anyway with what you know (title from search results if available) and note `[unverified]` in the summary.

## Maintenance

- `bm export --format md` → full dump (for backup/porting)
- `bm export --format json` → machine-readable dump
- Store lives outside the repo — the repo is the skill, not the data. Backups of the store are the user's call (suggest occasionally).
