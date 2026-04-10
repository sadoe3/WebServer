import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import markdown2
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
    """Return raw markdown body (frontmatter stripped, asset paths rewritten)."""
    text = post.path.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(text)
    body = re.sub(r'(src|href)="(/assets/[^"]+)"', rf'\1="{GITHUB_PAGES_BASE}\2"', body)
    return body


def _ensure_list_blank_lines(text: str) -> str:
    """Insert a blank line before list items that directly follow paragraph text.

    markdown2 requires a blank line separator between a paragraph and a list;
    without it, list items are rendered as inline text.
    """
    lines = text.split('\n')
    result: list[str] = []
    list_marker = re.compile(r'^\s*(\d+[\.\)]\s+|[*\-+]\s)')
    for i, line in enumerate(lines):
        if result and list_marker.match(line):
            prev = result[-1]
            # If previous line is non-empty text that is not itself a list item,
            # insert a blank line so markdown2 recognises the block as a list.
            if prev.strip() and not list_marker.match(prev):
                result.append('')
        result.append(line)
    return '\n'.join(result)


def render_body(post: Post) -> str:
    """Return post body rendered to HTML.

    Math regions ($...$  and  $$...$$) are extracted before markdown2 runs so
    that ampersands and backslashes inside LaTeX are not HTML-encoded.  They are
    restored verbatim afterwards so KaTeX can process them client-side.
    """
    body = get_body(post)

    # Fix ordered/unordered lists that follow a paragraph without a blank line
    body = _ensure_list_blank_lines(body)

    # Stash math regions so markdown2 cannot corrupt their content
    stash: list[str] = []

    def _protect(m: re.Match) -> str:
        stash.append(m.group(0))
        return f'\x02M{len(stash) - 1}\x03'

    # $$...$$ must be matched before $...$ to avoid partial matches
    body = re.sub(r'\$\$[\s\S]+?\$\$', _protect, body)
    body = re.sub(r'\$[^\n$]+?\$', _protect, body)

    html = markdown2.markdown(body, extras=['fenced-code-blocks', 'tables'])

    # Restore math regions exactly as they appeared in the source
    for i, math in enumerate(stash):
        html = html.replace(f'\x02M{i}\x03', math)

    return html
