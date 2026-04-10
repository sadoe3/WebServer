import os
from dotenv import load_dotenv
from nicegui import ui

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))


@ui.page("/")
def index():
    ui.label("Hello")


ui.run(host=HOST, port=PORT)
