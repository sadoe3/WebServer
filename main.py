import asyncio
import os
from dotenv import load_dotenv
from nicegui import app, ui

from src.db import init_db, cleanup_expired

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))


async def _cleanup_loop() -> None:
    while True:
        cleanup_expired()
        await asyncio.sleep(3600)  # run every hour


@app.on_startup
async def startup() -> None:
    init_db()
    asyncio.create_task(_cleanup_loop())


@ui.page("/")
def index():
    ui.label("Hello")


ui.run(host=HOST, port=PORT)
