from fastapi import Request
from nicegui import ui
from src.content import Post, render_body
from src import layout


_POST_STYLES = """
<style>
.nicegui-markdown { font-size: 1.05rem; line-height: 1.85; }
.nicegui-markdown h1, .nicegui-markdown h2, .nicegui-markdown h3,
.nicegui-markdown h4, .nicegui-markdown h5, .nicegui-markdown h6 {
  margin-top: 1.5em; margin-bottom: 0.4em; font-weight: 700;
}
.nicegui-markdown p { margin-bottom: 1em; }
.nicegui-markdown ul, .nicegui-markdown ol { margin-bottom: 1em; padding-left: 1.5em; }
.nicegui-markdown li { margin-bottom: 0.3em; }
.nicegui-markdown code:not(pre code) {
  font-size: 0.88em; padding: 2px 6px; border-radius: 4px;
  background: rgba(0,0,0,0.07);
}
.body--dark .nicegui-markdown code:not(pre code) {
  background: rgba(255,255,255,0.12);
}
.nicegui-markdown pre { padding: 1em; border-radius: 6px; overflow-x: auto; margin-bottom: 1em; }
.nicegui-markdown blockquote {
  border-left: 4px solid #93c5fd; margin: 0 0 1em; padding: 0.4em 1em;
  color: #6b7280;
}
.nicegui-markdown img { max-width: 100%; border-radius: 6px; }
.nicegui-markdown a { color: #3b82f6; text-decoration: underline; }

/* Floating back-to-top button */
#back-to-top {
  position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 9999;
  display: none;
  width: 44px; height: 44px; border-radius: 50%;
  background: #1d4ed8; color: white; border: none; cursor: pointer;
  font-size: 1.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  transition: opacity 0.2s, transform 0.2s;
}
#back-to-top:hover { background: #1e40af; transform: translateY(-2px); }
.body--dark #back-to-top { background: #3b82f6; }
.body--dark #back-to-top:hover { background: #2563eb; }

/* Pill language toggle */
.lang-pill a {
  display: inline-block; padding: 4px 14px; font-size: 0.8rem; font-weight: 600;
  border-radius: 999px; text-decoration: none; transition: all 0.15s;
}
.lang-pill a.active {
  background: #1d4ed8; color: white;
}
.lang-pill a.inactive {
  color: #6b7280; border: 1px solid #d1d5db;
}
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
"""


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

    with ui.column().classes("w-full max-w-3xl mx-auto px-4 py-8 gap-4"):
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

        # ── Top breadcrumb row ──────────────────────────────────────────────
        with ui.row().classes("items-center gap-2 mb-2 flex-wrap"):
            ui.link("← Home", "/").classes("text-blue-500 hover:underline text-sm")
            ui.label("·").classes("text-gray-400 text-sm")
            ui.label(category).classes("text-gray-500 text-sm capitalize")
            ui.space()
            if has_en or has_kr:
                ui.html(_lang_toggle(lang))

        # ── Title block ─────────────────────────────────────────────────────
        ui.label(post.title).classes("text-3xl font-bold leading-tight")
        ui.label(post.date).classes("text-sm text-gray-500")
        ui.separator()

        # ── Post body ───────────────────────────────────────────────────────
        ui.html(render_body(post)).classes("nicegui-markdown")

        # ── Bottom navigation (saves user from scrolling back up) ───────────
        ui.separator()
        with ui.row().classes("items-center gap-3 pt-2 flex-wrap"):
            ui.link("← Back to Home", "/").classes("text-blue-500 hover:underline text-sm")
            ui.space()
            if has_en or has_kr:
                ui.html(_lang_toggle(lang))
