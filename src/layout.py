from nicegui import app, ui

# Pretendard: best variable font for Korean + Latin portfolio sites
PRETENDARD_CSS = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css"
FONT_STYLE = (
    "<style>"
    "*, *::before, *::after { box-sizing: border-box; }"
    "body, .q-app { font-family: 'Pretendard Variable', Pretendard, "
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important; }"
    "</style>"
)

KATEX_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
KATEX_AUTO = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
HLJS_CSS_LIGHT = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css"
HLJS_CSS_DARK = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css"
HLJS_JS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"


def page_header(with_code_math: bool = False) -> None:
    """Render common page header with nav and dark mode toggle.

    Args:
        with_code_math: inject KaTeX + highlight.js (for post pages).
    """
    # Read preference server-side so dark.value is set before HTML is sent to browser.
    # This eliminates the flash: Quasar initialises with the correct state from the start.
    is_dark: bool = app.storage.user.get("dark_mode", True)
    dark = ui.dark_mode(value=is_dark)

    # Load Pretendard font (Korean + Latin) on every page
    ui.add_head_html(f'<link rel="stylesheet" href="{PRETENDARD_CSS}">')
    ui.add_head_html(FONT_STYLE)

    if with_code_math:
        ui.add_head_html(f'<link rel="stylesheet" href="{KATEX_CSS}">')
        # Load synchronously (no defer) so scripts are available when timer fires
        ui.add_head_html(f'<script src="{KATEX_JS}"></script>')
        ui.add_head_html(f'<script src="{KATEX_AUTO}"></script>')
        hljs_css_init = HLJS_CSS_DARK if is_dark else HLJS_CSS_LIGHT
        ui.add_head_html(f'<link id="hljs-css" rel="stylesheet" href="{hljs_css_init}">')
        ui.add_head_html(f'<script src="{HLJS_JS}"></script>')

    async def _on_page_load() -> None:
        if with_code_math:
            try:
                await ui.run_javascript(
                    'if (typeof hljs !== "undefined") { hljs.highlightAll(); }',
                    timeout=5.0,
                )
                # NiceGUI injects markdown via WebSocket after DOMContentLoaded,
                # so KaTeX auto-render must be triggered manually here
                await ui.run_javascript(
                    'if (typeof renderMathInElement !== "undefined") {'
                    '  renderMathInElement(document.body, {'
                    '    delimiters: ['
                    '      {left: "$$", right: "$$", display: true},'
                    '      {left: "$",  right: "$",  display: false}'
                    '    ],'
                    '    throwOnError: false'
                    '  });'
                    '}',
                    timeout=5.0,
                )
            except TimeoutError:
                pass  # client disconnected or navigated away before scripts loaded

    # Timer is now only needed for hljs + KaTeX (dark mode no longer requires it)
    if with_code_math:
        ui.timer(0.5, _on_page_load, once=True)

    async def _toggle_dark() -> None:
        dark.toggle()
        is_dark = dark.value
        app.storage.user["dark_mode"] = is_dark
        hljs_css = HLJS_CSS_DARK if is_dark else HLJS_CSS_LIGHT
        await ui.run_javascript(
            f'var el = document.getElementById("hljs-css");'
            f'if (el) {{ el.href = "{hljs_css}"; }}'
            f'if (typeof hljs !== "undefined") {{ hljs.highlightAll(); }}'
        )

    with ui.header().classes("items-center justify-between px-6 py-3 bg-blue-700"):
        ui.link("Portfolio", "/").classes(
            "text-xl font-bold text-white no-underline hover:text-blue-200 transition-colors"
        )
        ui.button(icon="dark_mode", on_click=_toggle_dark).props(
            "flat round color=white"
        ).tooltip("Toggle dark mode")
