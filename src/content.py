import html as _html
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


def _strip_md_inline(text: str) -> str:
    """Strip inline markdown formatting (**bold**, *italic*, `code`) from text."""
    text = re.sub(r'\*{1,3}([^*]*)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]*)_{1,3}', r'\1', text)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    return text.strip()


def _heading_anchor(text: str) -> str:
    """GitHub-style anchor id from plain heading text (no HTML, no markdown)."""
    anchor = text.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)   # strip punctuation/special chars
    anchor = re.sub(r'\s+', '-', anchor.strip())  # spaces → dashes
    anchor = re.sub(r'-+', '-', anchor)           # collapse consecutive dashes
    return anchor


def extract_headings(body: str) -> list[tuple[int, str, str]]:
    """Return list of (level, display_text, anchor_id) for h2/h3/h4 headings in raw markdown."""
    headings: list[tuple[int, str, str]] = []
    for line in body.split('\n'):
        m = re.match(r'^(#{2,4})\s+(.+)', line)
        if m:
            level = len(m.group(1))
            display = _strip_md_inline(m.group(2).strip())
            headings.append((level, display, _heading_anchor(display)))
    return headings


def _inject_heading_ids(html_str: str) -> str:
    """Add id attributes to h2/h3/h4 elements so ToC anchor links work.

    Must produce anchors identical to extract_headings so links resolve correctly.
    markdown2 HTML-encodes special chars (& → &amp;), so we unescape before anchoring.
    """
    def _replace(m: re.Match) -> str:
        tag = m.group(1)
        inner = m.group(2)
        text = re.sub(r'<[^>]+>', '', inner)   # strip inner HTML tags
        text = _html.unescape(text)             # decode &amp; → & etc.
        text = _strip_md_inline(text)           # strip any residual ** markup
        anchor = _heading_anchor(text)
        return f'<{tag} id="{anchor}">{inner}</{tag}>'
    return re.sub(r'<(h[2-4])>(.*?)</\1>', _replace, html_str, flags=re.DOTALL)


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


def _fix_cjk_bold(text: str) -> str:
    """Insert zero-width spaces around ** / * markers that touch Korean/CJK characters.

    markdown2 uses (?<!\w) / (?!\w) word-boundary assertions.  Python's `re`
    treats Hangul (가-힣) and CJK as \\w under Unicode mode, so bold markers
    directly adjacent to Korean text silently fail to render.
    Inserting U+200B (zero-width space) makes markdown2 see a non-word boundary
    while remaining invisible in the final HTML output.

    This fix runs line-by-line and skips fenced code blocks.
    """
    ZWS = '\u200b'  # zero-width space — must be a real char, not r'\u200b'
    _CJK = r'[가-힣\u3040-\u30ff\u4e00-\u9fff]'
    lines = text.split('\n')
    out: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith('```'):
            in_fence = not in_fence
        if not in_fence and '*' in line:
            # Korean immediately BEFORE **: 한**bold** → 한<ZWS>**bold**
            line = re.sub(rf'({_CJK})\*\*', lambda m: m.group(1) + ZWS + '**', line)
            # closing ** immediately BEFORE Korean: **bold**가 → **bold**<ZWS>가
            line = re.sub(rf'\*\*({_CJK})', lambda m: '**' + ZWS + m.group(1), line)
            # same for single * (italic), skip ** cases
            line = re.sub(rf'({_CJK})\*(?!\*)', lambda m: m.group(1) + ZWS + '*', line)
            line = re.sub(rf'\*(?!\*)({_CJK})', lambda m: '*' + ZWS + m.group(1), line)
        out.append(line)
    return '\n'.join(out)


def render_body(post: Post) -> str:
    """Return post body rendered to HTML.

    Math regions ($...$  and  $$...$$) are extracted before markdown2 runs so
    that ampersands and backslashes inside LaTeX are not HTML-encoded.  They are
    restored verbatim afterwards so KaTeX can process them client-side.
    """
    body = get_body(post)

    # Fix ordered/unordered lists that follow a paragraph without a blank line
    body = _ensure_list_blank_lines(body)

    # Fix Korean/CJK word-boundary issue with markdown2 bold/italic parsing
    body = _fix_cjk_bold(body)

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

    html = _inject_heading_ids(html)
    return html
