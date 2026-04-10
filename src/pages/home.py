from collections import defaultdict
from nicegui import ui
from src.content import Post
from src import layout

_CATEGORY_ICONS: dict[str, str] = {
    "CV": "person",
    "ComputerGraphics": "monitor",
    "PhysicsEngine": "science",
    "PintOS": "memory",
}


def render(posts: list[Post]) -> None:
    layout.page_header()

    # Group by category → slug → lang
    by_category: dict[str, dict[str, dict[str, Post]]] = defaultdict(lambda: defaultdict(dict))
    for post in posts:
        by_category[post.category][post.slug][post.lang] = post

    with ui.column().classes("w-full max-w-4xl mx-auto px-4 py-8 gap-8"):
        with ui.row().classes("items-baseline gap-3"):
            ui.label("Posts").classes("text-3xl font-bold")
            ui.label(f"{len(posts)} articles").classes("text-gray-400 text-sm")

        for category, slugs in sorted(by_category.items()):
            icon = _CATEGORY_ICONS.get(category, "article")
            with ui.card().classes("w-full shadow-sm"):
                with ui.row().classes("items-center gap-2 mb-3"):
                    ui.icon(icon).classes("text-blue-600")
                    ui.label(category).classes("text-lg font-semibold")
                    ui.badge(str(len(slugs))).props("color=blue rounded")

                ui.separator().classes("mb-3")

                with ui.column().classes("gap-1 w-full"):
                    for slug, langs in sorted(slugs.items(), key=lambda kv: kv[1].get("en", kv[1].get("kr")).date, reverse=True):
                        en_post = langs.get("en")
                        kr_post = langs.get("kr")
                        display = en_post or kr_post

                        title_href = f"/posts/{category}/{slug}?lang=en" if en_post else f"/posts/{category}/{slug}?lang=kr"
                        with ui.row().classes("items-center gap-3 py-2 px-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 w-full"):
                            ui.link(display.title, title_href).classes("flex-1 text-sm font-medium text-inherit no-underline hover:text-blue-500 transition-colors")
                            ui.label(display.date).classes("text-xs text-gray-400 shrink-0")
                            with ui.row().classes("gap-1 shrink-0"):
                                if en_post:
                                    ui.link("EN", f"/posts/{category}/{slug}?lang=en").classes(
                                        "text-xs text-blue-500 hover:underline px-1"
                                    )
                                if kr_post:
                                    ui.link("KR", f"/posts/{category}/{slug}?lang=kr").classes(
                                        "text-xs text-blue-500 hover:underline px-1"
                                    )
