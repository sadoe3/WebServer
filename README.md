# Portfolio Web Server

A self-hosted, full-stack portfolio blog built from scratch in Python —  
migrated from a static Jekyll/GitHub Pages site and rebuilt as a dynamic web server with auth, DB, and live deployment via Cloudflare Tunnel.

> **Goal:** Own the full stack. No managed platforms, no vendor lock-in. Just Python running on a local machine, exposed to the world — with proper auth, role-based access, and zero open ports.

---

## What It Does

- **Closed, invite-only access** — every page requires a valid session. Unregistered visitors see only the login page.
- **Role-based access control** — `admin` users can manage content and users; `viewer` users can read posts. The DB is the source of truth for who gets in.
- **Passwordless login via magic links** — enter your email, get a one-time link, done. No passwords to store or leak.
- **Reads and renders Markdown** posts from a local `content/` directory — the same files that used to live in Jekyll `_posts/`, now served dynamically
- **Bilingual (EN/KR)** post support with a per-post language toggle
- **LaTeX math rendering** via KaTeX and **syntax highlighting** via highlight.js
- **Dark mode** that persists across page navigation (server-side, no flash)
- **Cloudflare Tunnel deployment** — reachable from anywhere without port forwarding or a VPS

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | |
| Package Manager | `uv` | No `pip` |
| Web Framework | NiceGUI 2.x | FastAPI under the hood |
| Database | SQLite (`sqlite3`) | Standard library, zero config |
| Email | `aiosmtplib` | Async SMTP for magic links |
| Rendering | `markdown2` + KaTeX + highlight.js | Server-side MD → HTML, client-side math/code |
| Deployment | Cloudflare Tunnel (`cloudflared`) | Free, no open ports |
| Env | `python-dotenv` | `.env` file |

---

## Features

### Content (F-01)
- Scans `content/` recursively on startup and caches all posts in memory
- Parses Jekyll-style YAML frontmatter (`title`, `date`, `tags`, etc.)
- URL scheme: `/posts/{category}/{slug}?lang=en|kr`
- KR fallback: requesting `?lang=kr` on an EN-only post silently serves EN
- Math regions (`$...$`, `$$...$$`) are extracted before markdown processing to prevent HTML-encoding corruption, then restored for KaTeX

### Auth & Access Control (F-02)
- **Fully closed** — global middleware guards every route; unauthenticated requests are redirected to `/login`
- **Role-based:** `admin` (full access) vs `viewer` (read-only). Only registered users in the DB can log in.
- Magic link flow: email input → DB lookup → one-time UUID token (15 min) → SMTP → cookie session
- `HttpOnly; Secure; SameSite=Lax` session cookie; token is single-use
- Initial admin seeded from `ADMIN_EMAIL` in `.env` on first run

### User Management (F-05)
- Admin panel (`/admin`) lists all users with their roles
- Add users (email + role), change roles, delete users
- New users can receive an invite email automatically on creation
- Self-delete guard — admins cannot delete their own account

### Database (F-03)
- Three tables: `users`, `magic_tokens`, `sessions`
- Auto-created on first run (`CREATE TABLE IF NOT EXISTS`)
- Background task cleans up expired tokens every hour

### Deployment (F-04)
- **Quick Tunnel (free):** `cloudflared tunnel --url http://localhost:8080` — temporary `*.trycloudflare.com` URL, changes on restart
- **Named Tunnel (~$10/yr):** Fixed custom domain via `cloudflared/config.yml`

### UI/UX (Phase 5)
- Dark / light mode toggle — preference stored server-side (`app.storage.user`), applied before first render to eliminate flash
- Pill-style EN/KR language toggle on every post
- Floating "↑" back-to-top button (appears after 300 px scroll)
- Bottom navigation bar mirrors the top — no scrolling back up to switch language or go home
- Post typography: line height, heading margins, inline code, blockquote, image styles

---

## Project Structure

```
project/
├── main.py              # Entry point — routes, startup, cleanup task
├── pyproject.toml       # uv project config
├── .env.example         # Required environment variables
├── content/             # Markdown posts (Jekyll _posts/ structure)
│   ├── CV/
│   ├── ComputerGraphics/
│   ├── PhysicsEngine/
│   └── PintOS/
├── data/                # SQLite DB file (gitignored)
├── cloudflared/         # Tunnel config (Named Tunnel only)
└── src/
    ├── layout.py        # Shared page header — dark mode, KaTeX, highlight.js
    ├── db.py            # Schema init & query helpers
    ├── auth.py          # Magic link creation & session verification
    ├── mail.py          # Async email dispatch
    ├── content.py       # MD scan, frontmatter parse, safe HTML render
    └── pages/
        ├── home.py      # Post list grouped by category
        ├── post.py      # Post detail with math/code rendering
        ├── login.py     # Magic link request form
        └── admin.py     # Session-protected admin page
```

---

## Getting Started

**1. Clone and install**
```bash
git clone https://github.com/sadoe3/WebServer.git
cd WebServer
uv sync
```

**2. Configure environment**
```bash
cp .env.example .env
# Edit .env — fill in SMTP credentials, ADMIN_EMAIL, SESSION_SECRET, STORAGE_SECRET
```

**3. Run**
```bash
uv run main.py
# → http://localhost:8080
```

**4. Expose publicly (optional)**
```bash
cloudflared tunnel --url http://localhost:8080
# Copy the *.trycloudflare.com URL → set as MAGIC_LINK_BASE_URL in .env → restart server
```

---

## Deployment Notes

| Option | Cost | URL | Config |
|---|---|---|---|
| Quick Tunnel | Free | Changes on restart (`*.trycloudflare.com`) | None |
| Named Tunnel | ~$10/yr (domain) | Fixed custom domain | `cloudflared/config.yml` |

Cloudflare handles TLS termination — the local server runs plain HTTP, HTTPS is automatic at the edge.
