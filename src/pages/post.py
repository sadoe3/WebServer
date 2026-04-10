from fastapi import Request
from nicegui import ui
from src.content import Post, get_body


def render(request: Request, posts: list[Post]) -> None:
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

    with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
        if post is None:
            ui.label("404 - Post not found").classes("text-2xl text-red-500")
            ui.link("← Back to home", "/").classes("text-blue-500")
            return

        # Language toggle links
        en_post = lookup.get((category, slug, "en"))
        kr_post = lookup.get((category, slug, "kr"))
        with ui.row().classes("gap-4 mb-4"):
            ui.link("← Back", "/").classes("text-blue-500")
            if en_post:
                ui.link("EN", f"/posts/{category}/{slug}?lang=en").classes("text-blue-500")
            if kr_post:
                ui.link("KR", f"/posts/{category}/{slug}?lang=kr").classes("text-blue-500")

        ui.label(post.title).classes("text-3xl font-bold mb-1")
        ui.label(post.date).classes("text-sm text-gray-500 mb-4")
        ui.markdown(get_body(post))
