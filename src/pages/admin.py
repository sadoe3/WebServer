from nicegui import ui
from fastapi import Request
from fastapi.responses import RedirectResponse
from src.auth import get_session_user, delete_session
from src import layout


def render(request: Request) -> RedirectResponse | None:
    session_token = request.cookies.get("session_id")
    user = get_session_user(session_token) if session_token else None

    if user is None:
        return RedirectResponse("/login")

    layout.page_header()

    with ui.column().classes("w-full max-w-2xl mx-auto mt-16 p-6 gap-4"):
        ui.label("Admin").classes("text-2xl font-bold")
        ui.label(f"Logged in as: {user['email']}").classes("text-gray-600")

        async def on_logout():
            delete_session(session_token)
            ui.navigate.to("/login")

        ui.button("Logout", on_click=on_logout).classes("bg-red-500 text-white")
