import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

CONTENT_DIR = Path(__file__).parent.parent / "content"
GITHUB_PAGES_BASE = "https://sadoe3.github.io"


@dataclass
class Post:
    slug: str
    title: str
    date: str
    category: str
    lang: str
    path: Path


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter and body. Returns (meta, body)."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    body = text[match.end():]
    return meta, body


def _slug_from_filename(name: str) -> tuple[str, str]:
    """Extract (slug, lang) from YYYY-MM-DD-slug[_kr].md filename."""
    stem = Path(name).stem  # e.g. "2025-05-01-post1_kr"
    # Remove date prefix
    slug_part = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    if slug_part.endswith("_kr"):
        return slug_part[:-3], "kr"
    return slug_part, "en"


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for md_file in sorted(CONTENT_DIR.rglob("*.md")):
        category = md_file.parent.name
        slug, lang = _slug_from_filename(md_file.name)
        text = md_file.read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(text)
        title = str(meta.get("title", slug))
        date = str(meta.get("date", ""))
        posts.append(Post(slug=slug, title=title, date=date,
                          category=category, lang=lang, path=md_file))
    return posts


def get_body(post: Post) -> str:
    """Return rendered body (frontmatter stripped, asset paths rewritten to GitHub Pages URLs)."""
    text = post.path.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(text)
    body = re.sub(r'(src|href)="(/assets/[^"]+)"', rf'\1="{GITHUB_PAGES_BASE}\2"', body)
    return body
