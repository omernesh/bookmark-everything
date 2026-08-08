#!/usr/bin/env python3
"""Bookmark Everything — local bookmark store (skill-based, no server, no UI).

Each bookmark is a markdown file with YAML frontmatter in ~/.hermes/bookmarks/.
Stdlib only. Works offline except for --fetch-title.

Usage:
  bm.py add <url> [--title T] [--tags a,b,c] [--category C] [--summary S]
  bm.py search <query> [--tag T] [--category C] [--limit N] [--json]
  bm.py list [--tag T] [--category C] [--limit N] [--json]
  bm.py tags
  bm.py categories
  bm.py get <id>
  bm.py rm <id>
  bm.py export [--format json|md]
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".hermes" / "bookmarks"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FIELD_WEIGHT = {"title": 3, "tags": 2, "category": 2, "summary": 1, "url": 1}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str, maxlen: int = 40) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:maxlen].rstrip("-") or "bookmark"


def fetch_title(url: str) -> str | None:
    """Best-effort <title> extraction. Returns None on any failure."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read(200_000).decode("utf-8", errors="ignore")
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()
            return title[:200] or None
    except Exception:
        pass
    return None


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            val = [t.strip().strip('"\'') for t in val[1:-1].split(",") if t.strip()]
        meta[key] = val
    return meta


def write_frontmatter(meta: dict, body: str) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    return "\n".join(lines)


def add(args) -> int:
    url = args.url
    title = args.title or fetch_title(url) or url
    bid = f'{datetime.now().strftime("%Y%m%d")}-{slugify(title)}'
    path = DATA_DIR / f"{bid}.md"
    n = 2
    while path.exists():
        path = DATA_DIR / f"{bid}-{n}.md"
        n += 1
    tags = [t.strip().lower() for t in (args.tags or "").split(",") if t.strip()]
    meta = {
        "id": path.stem,
        "title": title,
        "url": url,
        "date": now_iso(),
        "tags": tags,
        "category": (args.category or "misc").strip().lower(),
    }
    body = f"## Summary\n\n{args.summary.strip() if args.summary else ''}\n"
    path.write_text(write_frontmatter(meta, body), encoding="utf-8")
    print(f"saved: {path}")
    print(f"id: {meta['id']}")
    return 0


def _search(query: str, tag: str | None, category: str | None) -> list[tuple[dict, Path, int]]:
    q = query.lower()
    results = []
    for path in sorted(DATA_DIR.glob("*.md"), reverse=True):
        meta = parse_frontmatter(path)
        if not meta:
            continue
        if tag and tag.lower() not in [t.lower() for t in (meta.get("tags") or [])]:
            continue
        if category and category.lower() != (meta.get("category") or "").lower():
            continue
        hay = {
            "title": str(meta.get("title", "")).lower(),
            "tags": " ".join(meta.get("tags") or []).lower(),
            "category": str(meta.get("category", "")).lower(),
            "summary": path.read_text(encoding="utf-8").lower(),
            "url": str(meta.get("url", "")).lower(),
        }
        score = 0
        for field, text in hay.items():
            if q and q in text:
                score += FIELD_WEIGHT[field]
        if score > 0:
            results.append((meta, path, score))
    results.sort(key=lambda r: r[2], reverse=True)
    return results


def search(args) -> int:
    results = _search(args.query or "", args.tag, args.category)
    if args.limit:
        results = results[: args.limit]
    if args.json:
        print(json.dumps([r[0] for r in results], ensure_ascii=False, indent=2))
        return 0
    for meta, path, score in results:
        print(f"[{score}] {meta['id']}")
        print(f"    {meta.get('title')}")
        print(f"    {meta.get('url')}")
        print(f"    tags: {', '.join(meta.get('tags') or [])} | category: {meta.get('category')}")
    print(f"\n{len(results)} result(s)")
    return 0


def list_all(args) -> int:
    metas = []
    for path in sorted(DATA_DIR.glob("*.md"), reverse=True):
        meta = parse_frontmatter(path)
        if not meta:
            continue
        if args.tag and args.tag.lower() not in [t.lower() for t in (meta.get("tags") or [])]:
            continue
        if args.category and args.category.lower() != (meta.get("category") or "").lower():
            continue
        metas.append(meta)
    if args.limit:
        metas = metas[: args.limit]
    if args.json:
        print(json.dumps(metas, ensure_ascii=False, indent=2))
        return 0
    for meta in metas:
        print(f"{meta['id']}  {meta.get('date')}")
        print(f"    {meta.get('title')}  |  tags: {', '.join(meta.get('tags') or [])}  |  {meta.get('category')}")
    print(f"\n{len(metas)} bookmark(s)")
    return 0


def tags(args) -> int:
    counts: dict[str, int] = {}
    for path in DATA_DIR.glob("*.md"):
        meta = parse_frontmatter(path)
        if not meta:
            continue
        for t in meta.get("tags") or []:
            counts[t] = counts.get(t, 0) + 1
    for t, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{c:3d}  {t}")
    return 0


def categories(args) -> int:
    counts: dict[str, int] = {}
    for path in DATA_DIR.glob("*.md"):
        meta = parse_frontmatter(path)
        if not meta:
            continue
        c = meta.get("category") or "misc"
        counts[c] = counts.get(c, 0) + 1
    for c, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{n:3d}  {c}")
    return 0


def get(args) -> int:
    path = DATA_DIR / f"{args.id}.md"
    if not path.exists():
        # allow id prefix match
        matches = [p for p in DATA_DIR.glob(f"{args.id}*.md")]
        if not matches:
            print(f"not found: {args.id}", file=sys.stderr)
            return 1
        path = matches[0]
    print(path.read_text(encoding="utf-8"))
    return 0


def rm(args) -> int:
    path = DATA_DIR / f"{args.id}.md"
    if not path.exists():
        matches = [p for p in DATA_DIR.glob(f"{args.id}*.md")]
        if not matches:
            print(f"not found: {args.id}", file=sys.stderr)
            return 1
        path = matches[0]
    path.unlink()
    print(f"deleted: {path.name}")
    return 0


def export(args) -> int:
    items = []
    for path in sorted(DATA_DIR.glob("*.md")):
        meta = parse_frontmatter(path)
        if not meta:
            continue
        body = path.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        items.append({**meta, "body": body})
    if args.format == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        for it in items:
            print(f"## {it.get('title')}")
            print(f"- url: {it.get('url')}")
            print(f"- date: {it.get('date')}")
            print(f"- tags: {', '.join(it.get('tags') or [])} | category: {it.get('category')}")
            print()
            print(it.get("body", ""))
            print()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="bm", description="Bookmark Everything CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="save a bookmark")
    pa.add_argument("url")
    pa.add_argument("--title")
    pa.add_argument("--tags", help="comma-separated")
    pa.add_argument("--category", default="misc")
    pa.add_argument("--summary")
    pa.set_defaults(fn=add)

    ps = sub.add_parser("search", help="search bookmarks")
    ps.add_argument("query", nargs="?", default="")
    ps.add_argument("--tag")
    ps.add_argument("--category")
    ps.add_argument("--limit", type=int)
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(fn=search)

    pl = sub.add_parser("list", help="list bookmarks")
    pl.add_argument("--tag")
    pl.add_argument("--category")
    pl.add_argument("--limit", type=int)
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(fn=list_all)

    pt = sub.add_parser("tags", help="tag counts")
    pt.set_defaults(fn=tags)

    pc = sub.add_parser("categories", help="category counts")
    pc.set_defaults(fn=categories)

    pg = sub.add_parser("get", help="show one bookmark")
    pg.add_argument("id")
    pg.set_defaults(fn=get)

    pr = sub.add_parser("rm", help="delete a bookmark")
    pr.add_argument("id")
    pr.set_defaults(fn=rm)

    pe = sub.add_parser("export", help="export all bookmarks")
    pe.add_argument("--format", choices=["json", "md"], default="md")
    pe.set_defaults(fn=export)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
