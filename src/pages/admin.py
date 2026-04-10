from nicegui import ui
from fastapi import Request
from fastapi.responses import RedirectResponse
from src.auth import get_session_user, delete_session, create_magic_token
from src.db import list_users, add_user, update_user_role, delete_user, get_user_by_email
from src.mail import send_magic_link
from src import layout
import os


def _render_user_rows(container, users, current_user_id, refresh_fn):
    """Clear container and re-render all user rows inside it."""
    container.clear()
    with container:
        if not users:
            ui.label("No users found.")
            return

        for u in users:
            uid = u["id"]
            other_role = "admin" if u["role"] == "viewer" else "viewer"

            with ui.card().classes("w-full"):
                with ui.card_section():
                    ui.label(u["email"]).classes("font-medium")
                    ui.label(f"Role: {u['role']}  |  Created: {u['created_at'][:10]}")

                with ui.card_section():
                    with ui.row():
                        def make_toggle(uid=uid, other_role=other_role):
                            async def toggle():
                                update_user_role(uid, other_role)
                                refresh_fn()
                            return toggle

                        ui.button(f"→ {other_role}", on_click=make_toggle()).props("flat dense")

                        if uid != current_user_id:
                            def make_delete(uid=uid, email=u["email"]):
                                async def do_delete():
                                    delete_user(uid)
                                    ui.notify(f"{email} deleted.", color="positive")
                                    refresh_fn()
                                return do_delete

                            ui.button("Delete", on_click=make_delete()).props("flat dense color=negative")


def render(request: Request) -> RedirectResponse | None:
    session_token = request.cookies.get("session_id")
    user = get_session_user(session_token) if session_token else None

    if user is None:
        return RedirectResponse("/login")

    if user["role"] != "admin":
        return RedirectResponse("/")

    layout.page_header()

    with ui.column().classes("w-full max-w-3xl mx-auto mt-16 p-6 gap-6"):
        # Header
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Admin — User Management").classes("text-2xl font-bold")

            async def on_logout():
                delete_session(session_token)
                ui.navigate.to("/login")

            ui.button("Logout", on_click=on_logout).props("color=negative")

        ui.label(f"Logged in as: {user['email']} (admin)").classes("text-sm opacity-60")
        ui.separator()

        # --- Add user form ---
        ui.label("Add User").classes("text-lg font-semibold")
        with ui.row().classes("w-full items-center gap-3 flex-wrap"):
            new_email = ui.input("Email").classes("flex-1")
            new_role = ui.select(["viewer", "admin"], value="viewer", label="Role").classes("w-28")
            send_invite = ui.checkbox("Send invite", value=True)

            async def on_add_user():
                email = new_email.value.strip()
                if not email:
                    ui.notify("Email is required.", color="negative")
                    return
                if get_user_by_email(email):
                    ui.notify("User already exists.", color="warning")
                    return
                add_user(email, new_role.value)
                if send_invite.value:
                    expire_minutes = int(os.getenv("TOKEN_EXPIRE_MINUTES", "15"))
                    token = create_magic_token(email, expire_minutes)
                    if token:
                        await send_magic_link(email, token)
                ui.notify(f"User {email} added.", color="positive")
                new_email.value = ""
                _render_user_rows(user_list, list_users(), user["id"], do_refresh)

            ui.button("Add", on_click=on_add_user).props("color=primary")

        ui.separator()

        # --- User list ---
        ui.label("All Users").classes("text-lg font-semibold")

        user_list = ui.column().classes("w-full gap-2")

        def do_refresh():
            _render_user_rows(user_list, list_users(), user["id"], do_refresh)

        do_refresh()
