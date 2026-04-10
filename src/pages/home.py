from collections import defaultdict
from nicegui import ui
from src.content import Post


def render(posts: list[Post]) -> None:
    # Group by category → slug → lang
    by_category: dict[str, dict[str, dict[str, Post]]] = defaultdict(lambda: defaultdict(dict))
    for post in posts:
        by_category[post.category][post.slug][post.lang] = post

    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-6"):
        ui.label("Portfolio").classes("text-3xl font-bold")

        for category, slugs in sorted(by_category.items()):
            with ui.card().classes("w-full"):
                ui.label(category).classes("text-xl font-semibold mb-2")
                with ui.column().classes("gap-2"):
                    for slug, langs in sorted(slugs.items()):
                        en_post = langs.get("en")
                        kr_post = langs.get("kr")
                        display = en_post or kr_post
                        with ui.row().classes("items-center gap-4"):
                            ui.label(display.title).classes("flex-1")
                            ui.label(display.date).classes("text-sm text-gray-500")
                            if en_post:
                                ui.link("EN", f"/posts/{category}/{slug}?lang=en").classes("text-blue-500")
                            if kr_post:
                                ui.link("KR", f"/posts/{category}/{slug}?lang=kr").classes("text-blue-500")
