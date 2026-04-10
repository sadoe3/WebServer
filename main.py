import asyncio
import os
from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from src.db import init_db, seed_admin, cleanup_expired
from src.content import load_posts
from src.auth import verify_magic_token, get_session_user
from src.pages import home, post as post_page, login as login_page, admin as admin_page

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
SESSION_EXPIRE_DAYS = int(os.getenv("SESSION_EXPIRE_DAYS", "7"))
STORAGE_SECRET = os.getenv("STORAGE_SECRET", "changeme-storage-secret")

posts = load_posts()

# Paths that do not require authentication
_PUBLIC_PREFIXES = ("/login", "/auth/verify", "/_nicegui/")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)

    session_token = request.cookies.get("session_id")
    user = get_session_user(session_token) if session_token else None
    if user is None:
        return RedirectResponse("/login", status_code=302)

    return await call_next(request)


async def _cleanup_loop() -> None:
    while True:
        cleanup_expired()
        await asyncio.sleep(3600)


@app.on_startup
async def startup() -> None:
    init_db()
    seed_admin()
    asyncio.create_task(_cleanup_loop())


@ui.page("/")
def index():
    home.render(posts)


@ui.page("/posts/{category}/{slug}")
def post_detail(request: Request):
    post_page.render(request, posts)


@ui.page("/login")
def login():
    login_page.render()


@ui.page("/auth/verify")
def auth_verify(request: Request):
    token = request.query_params.get("token", "")
    session_token = verify_magic_token(token, SESSION_EXPIRE_DAYS)

    if session_token is None:
        with ui.column().classes("w-full max-w-md mx-auto mt-20 p-6 gap-4"):
            ui.label("Invalid or expired link.").classes("text-red-500")
            ui.link("Request a new link", "/login").classes("text-blue-500")
        return

    response = RedirectResponse("/admin")
    response.set_cookie(
        key="session_id",
        value=session_token,
        max_age=SESSION_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return response


@ui.page("/admin")
def admin(request: Request):
    return admin_page.render(request)


ui.run(host=HOST, port=PORT, storage_secret=STORAGE_SECRET)
