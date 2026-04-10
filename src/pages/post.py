from fastapi import Request
from nicegui import ui
from src.content import Post, render_body, get_body, extract_headings
from src import layout


_POST_STYLES = """
<style>
/* ── Post content typography ─────────────────────────────────────────── */
.nicegui-markdown { font-size: 1.1rem; line-height: 1.9; }

/* Base heading styles */
.nicegui-markdown h1, .nicegui-markdown h2, .nicegui-markdown h3,
.nicegui-markdown h4, .nicegui-markdown h5, .nicegui-markdown h6 {
  margin-bottom: 0.5em; font-weight: 700;
}

/* h2: section separator line + generous spacing */
.nicegui-markdown h2 {
  margin-top: 3em;
  padding-top: 1.6em;
  border-top: 1px solid #cbd5e1;
  font-size: 1.35rem;
}
/* First h2 — still show separator but tighter top */
.nicegui-markdown h2:first-of-type {
  margin-top: 1.2em;
}
.body--dark .nicegui-markdown h2 {
  border-top-color: #334155;
}

/* h3: subsection spacing, subtle left accent */
.nicegui-markdown h3 {
  margin-top: 2em;
  padding-left: 0.75em;
  border-left: 3px solid #93c5fd;
  font-size: 1.1rem;
}
.body--dark .nicegui-markdown h3 {
  border-left-color: #3b82f6;
}

/* h4: light left accent, compact */
.nicegui-markdown h4 {
  margin-top: 1.6em;
  padding-left: 0.6em;
  border-left: 2px solid #bfdbfe;
  font-size: 1rem;
}
.body--dark .nicegui-markdown h4 {
  border-left-color: #1d4ed8;
}

.nicegui-markdown p { margin-bottom: 1.1em; }
.nicegui-markdown ul, .nicegui-markdown ol { margin-bottom: 1.1em; padding-left: 1.5em; }
.nicegui-markdown li { margin-bottom: 0.35em; }
.nicegui-markdown code:not(pre code) {
  font-size: 0.88em; padding: 2px 6px; border-radius: 4px;
  background: rgba(0,0,0,0.07);
}
.body--dark .nicegui-markdown code:not(pre code) { background: rgba(255,255,255,0.12); }
.nicegui-markdown pre { padding: 1em; border-radius: 6px; overflow-x: auto; margin-bottom: 1.2em; }
.nicegui-markdown blockquote {
  border-left: 4px solid #93c5fd; margin: 0 0 1.2em; padding: 0.5em 1em; color: #6b7280;
}
.nicegui-markdown img { max-width: 100%; border-radius: 6px; }
.nicegui-markdown a { color: #3b82f6; text-decoration: underline; }

/* ── 2-column grid layout: 1(margin) 6(post) 0.5(gap) 2(toc) 0.5(margin) ── */
/* Right column is `auto` — takes its size from .toc-sidebar width,         */
/* so toggling .toc-wide automatically resizes the column with no JS needed. */
.post-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  column-gap: 4rem;          /* ~5% gap at 1280px viewport */
  row-gap: 0;
  width: 100%;
  padding: 2rem 1% 2rem 5%;     /* top | right(1%) | bottom | left(5%) */
  align-items: start;
  box-sizing: border-box;
}
@media (max-width: 1100px) {
  .post-layout { grid-template-columns: 1fr; padding: 2rem 5%; }
  .toc-sidebar { display: none !important; }
}

/* ── ToC sidebar ─────────────────────────────────────────────────────── */
.toc-sidebar {
  position: sticky;
  top: 5rem;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
  width: 305px;              /* ~2.4/10 of 1280px viewport */
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.1rem;
  transition: width 0.2s ease;
}
/* Expanded ToC when heading count > 10 */
.toc-sidebar.toc-wide {
  width: 355px;
}
.body--dark .toc-sidebar {
  background: #1e293b;
  border-color: #334155;
}
.toc-title {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #94a3b8; margin-bottom: 0.6rem;
}
.toc-link {
  display: block; font-size: 0.8rem; line-height: 1.6;
  color: #64748b; text-decoration: none;
  border-left: 2px solid transparent;
  padding: 2px 0 2px 10px;
  transition: color 0.15s, border-color 0.15s;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.toc-link.toc-h3 { padding-left: 20px; font-size: 0.76rem; }
.toc-link.toc-h4 { padding-left: 32px; font-size: 0.72rem; color: #94a3b8; }
.toc-link:hover { color: #1d4ed8; border-left-color: #93c5fd; }
.toc-link.toc-active { color: #1d4ed8; border-left-color: #1d4ed8; font-weight: 600; }
.body--dark .toc-link { color: #94a3b8; }
.body--dark .toc-link:hover { color: #60a5fa; border-left-color: #3b82f6; }
.body--dark .toc-link.toc-active { color: #60a5fa; border-left-color: #60a5fa; }

/* ── Floating back-to-top button ─────────────────────────────────────── */
#back-to-top {
  position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 9999; display: none;
  width: 44px; height: 44px; border-radius: 50%;
  background: #1d4ed8; color: white; border: none; cursor: pointer;
  font-size: 1.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  transition: opacity 0.2s, transform 0.2s;
}
#back-to-top:hover { background: #1e40af; transform: translateY(-2px); }
.body--dark #back-to-top { background: #3b82f6; }
.body--dark #back-to-top:hover { background: #2563eb; }

/* ── Pill language toggle ─────────────────────────────────────────────── */
.lang-pill a {
  display: inline-block; padding: 4px 14px; font-size: 0.8rem; font-weight: 600;
  border-radius: 999px; text-decoration: none; transition: all 0.15s;
}
.lang-pill a.active { background: #1d4ed8; color: white; }
.lang-pill a.inactive { color: #6b7280; border: 1px solid #d1d5db; }
.lang-pill a.inactive:hover { border-color: #93c5fd; color: #1d4ed8; }
.body--dark .lang-pill a.inactive { color: #9ca3af; border-color: #4b5563; }
.body--dark .lang-pill a.inactive:hover { border-color: #60a5fa; color: #60a5fa; }
</style>
<button id="back-to-top" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Back to top">↑</button>
<script>
window.addEventListener('scroll', function() {
  var btn = document.getElementById('back-to-top');
  if (btn) btn.style.display = window.scrollY > 300 ? 'block' : 'none';
});
</script>
<script>
(function() {
  function initToc() {
    var links = document.querySelectorAll('.toc-link');
    if (!links.length) return;

    var headingIds = Array.from(links).map(function(l) {
      return l.getAttribute('href').slice(1);
    });

    function getActiveId() {
      // The active heading is the last one whose top is above the viewport midpoint
      var scrollY = window.scrollY + window.innerHeight * 0.25;
      var active = null;
      for (var i = 0; i < headingIds.length; i++) {
        var el = document.getElementById(headingIds[i]);
        if (el && el.getBoundingClientRect().top + window.scrollY <= scrollY) {
          active = headingIds[i];
        }
      }
      return active;
    }

    function updateActive() {
      var activeId = getActiveId();
      links.forEach(function(link) {
        var id = link.getAttribute('href').slice(1);
        link.classList.toggle('toc-active', id === activeId);
      });
    }

    window.addEventListener('scroll', updateActive, { passive: true });
    updateActive();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToc);
  } else {
    setTimeout(initToc, 200);
  }
})();
</script>
"""


def _build_toc_html(headings: list[tuple[int, str, str]]) -> str:
    """Return HTML string for the ToC link list (h2/h3/h4)."""
    _cls = {2: "toc-link", 3: "toc-link toc-h3", 4: "toc-link toc-h4"}
    parts: list[str] = []
    for level, text, anchor in headings:
        cls = _cls.get(level, "toc-link toc-h4")
        parts.append(f'<a class="{cls}" href="#{anchor}" title="{text}">{text}</a>')
    return "\n".join(parts)


def render(request: Request, posts: list[Post]) -> None:
    layout.page_header(with_code_math=True)
    ui.add_head_html(_POST_STYLES)

    category = request.path_params.get("category", "")
    slug = request.path_params.get("slug", "")
    lang = request.query_params.get("lang", "en")

    # Build lookup: (category, slug, lang) -> Post
    lookup: dict[tuple[str, str, str], Post] = {
        (p.category, p.slug, p.lang): p for p in posts
    }

    post = lookup.get((category, slug, lang))

    # Fallback: KR requested but not found -> use EN
    if post is None and lang == "kr":
        post = lookup.get((category, slug, "en"))

    # Outer wrapper: CSS grid (post ~60% | ToC ~40%)
    with ui.element('div').classes("post-layout"):

        # ── Main content column ─────────────────────────────────────────────
        with ui.element('div').style("display:flex;flex-direction:column;gap:1rem;min-width:0;"):
            if post is None:
                ui.label("404 - Post not found").classes("text-2xl text-red-500")
                ui.link("← Back to home", "/").classes("text-blue-500 hover:underline")
                return

            en_post = lookup.get((category, slug, "en"))
            kr_post = lookup.get((category, slug, "kr"))
            has_kr = kr_post is not None
            has_en = en_post is not None

            def _lang_toggle(current: str) -> str:
                """Return HTML for the pill-style EN/KR toggle."""
                parts: list[str] = []
                if has_en:
                    cls = "active" if current == "en" else "inactive"
                    parts.append(f'<a href="/posts/{category}/{slug}?lang=en" class="{cls}">EN</a>')
                if has_kr:
                    cls = "active" if current == "kr" else "inactive"
                    parts.append(f'<a href="/posts/{category}/{slug}?lang=kr" class="{cls}">KR</a>')
                return f'<span class="lang-pill" style="display:inline-flex;gap:6px;">{"".join(parts)}</span>'

            # ── Top breadcrumb row ──────────────────────────────────────────
            with ui.row().classes("items-center gap-2 mb-2 flex-wrap"):
                ui.link("← Home", "/").classes("text-blue-500 hover:underline text-sm")
                ui.label("·").classes("text-gray-400 text-sm")
                ui.label(category).classes("text-gray-500 text-sm capitalize")
                ui.space()
                if has_en or has_kr:
                    ui.html(_lang_toggle(lang))

            # ── Title block ─────────────────────────────────────────────────
            ui.label(post.title).classes("text-3xl font-bold leading-tight")
            ui.label(post.date).classes("text-sm text-gray-500")
            ui.separator()

            # ── Post body ───────────────────────────────────────────────────
            ui.html(render_body(post)).classes("nicegui-markdown")

            # ── Bottom navigation ────────────────────────────────────────────
            ui.separator()
            with ui.row().classes("items-center gap-3 pt-2 flex-wrap"):
                ui.link("← Back to Home", "/").classes("text-blue-500 hover:underline text-sm")
                ui.space()
                if has_en or has_kr:
                    ui.html(_lang_toggle(lang))

        # ── ToC sidebar column ──────────────────────────────────────────────
        if post is not None:
            headings = extract_headings(get_body(post))
            if headings:
                # Expand ToC width when there are many headings (> 10)
                toc_cls = "toc-sidebar toc-wide" if len(headings) > 10 else "toc-sidebar"
                with ui.element('aside').classes(toc_cls):
                    ui.html(f'<div class="toc-title">On this page</div>\n{_build_toc_html(headings)}')
