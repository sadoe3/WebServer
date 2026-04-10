# Portfolio Web Server

A full-stack portfolio web server built with Python, migrated from a static Jekyll + GitHub Pages blog.  
Implemented end-to-end: web server, SQLite DB, passwordless auth, and Cloudflare Tunnel deployment.

## Features

- **F-01. Portfolio Hosting** — Scans and renders Markdown posts from `content/`, with bilingual (EN/KR) support and Jekyll frontmatter parsing
- **F-02. Magic Link Auth** — Passwordless admin login via one-time email token (15-min expiry, HttpOnly cookie session)
- **F-03. SQLite Session Management** — Local DB for users, tokens, and sessions with background cleanup
- **F-04. Cloudflare Tunnel Deployment** — Exposes local server to the internet without port forwarding via `cloudflared`

## Tech Stack

| | |
|---|---|
| Language | Python 3.12 |
| Package Manager | `uv` |
| Web Framework | NiceGUI 2.x (FastAPI built-in) |
| Database | SQLite (`sqlite3` stdlib) |
| Email | `aiosmtplib` (async SMTP) |
| YAML Parsing | `pyyaml` (Jekyll frontmatter) |
| Deployment | Cloudflare Tunnel (`cloudflared`) |
| Env Management | `python-dotenv` |

## Project Structure

```
project/
├── main.py              # App entry point
├── pyproject.toml       # uv project config
├── .env.example         # Environment variable template
├── content/             # Migrated Markdown posts
│   ├── CV/
│   ├── ComputerGraphics/
│   ├── PhysicsEngine/
│   └── PintOS/
├── data/                # SQLite DB (gitignored)
└── src/
    ├── db.py            # DB init & helpers
    ├── auth.py          # Magic link & session logic
    ├── mail.py          # Async email sending
    ├── content.py       # MD file scanning & parsing
    └── pages/
        ├── home.py      # Home page
        ├── post.py      # Post detail page
        ├── login.py     # Login page
        └── admin.py     # Admin page
```

## Getting Started

**1. Clone and install dependencies**
```bash
git clone https://github.com/sadoe3/WebServer.git
cd WebServer
uv sync
```

**2. Set up environment variables**
```bash
cp .env.example .env
# Fill in SMTP credentials, SESSION_SECRET, ADMIN_EMAIL
```

**3. Run the server**
```bash
uv run main.py
```

**4. (Optional) Expose via Cloudflare Tunnel**
```bash
cloudflared tunnel --url http://localhost:8080
# Copy the *.trycloudflare.com URL into MAGIC_LINK_BASE_URL in .env, then restart the server
```

## Deployment Notes

- **Quick Tunnel (free):** Temporary `*.trycloudflare.com` domain, changes on every restart
- **Named Tunnel (paid, ~$10/yr):** Fixed custom domain via `cloudflared/config.yml`
