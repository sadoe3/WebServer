import os
from nicegui import ui
from src.auth import create_magic_token
from src.mail import send_magic_link
from src import layout


def render() -> None:
    layout.page_header()
    expire_minutes = int(os.getenv("TOKEN_EXPIRE_MINUTES", "15"))

    with ui.column().classes("w-full max-w-md mx-auto mt-16 p-6 gap-4"):
        ui.label("Login").classes("text-2xl font-bold")
        email_input = ui.input("Email").classes("w-full")
        status = ui.label("").classes("text-sm")

        async def on_submit():
            email = email_input.value.strip()
            if not email:
                return

            try:
                # Returns None for unregistered emails — same response shown either way
                token = create_magic_token(email, expire_minutes)
                if token:
                    await send_magic_link(email, token)
            except Exception as e:
                status.set_text(f"Error: {e}")
                return

            status.set_text("If this email is registered, a login link has been sent.")
            email_input.disable()

        ui.button("Send login link", on_click=on_submit).classes("w-full")
