import asyncio
import os
from dotenv import load_dotenv
from nicegui import app, ui

from src.db import init_db, cleanup_expired
from src.content import load_posts
from fastapi import Request
from src.pages import home, post as post_page

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

posts = load_posts()


async def _cleanup_loop() -> None:
    while True:
        cleanup_expired()
        await asyncio.sleep(3600)


@app.on_startup
async def startup() -> None:
    init_db()
    asyncio.create_task(_cleanup_loop())


@ui.page("/")
def index():
    home.render(posts)


@ui.page("/posts/{category}/{slug}")
def post_detail(request: Request):
    post_page.render(request, posts)


ui.run(host=HOST, port=PORT)
