# VENOM DLS — Custom DLS 26 Kits

A storefront + auto kit-generator for **Dream League Soccer 2026** custom kits.
Visitors design a kit (colors + style), get an import-ready 512×512 PNG, and can
order a custom kit via WhatsApp.

## Stack
- **Frontend:** static `index.html` (no build step)
- **Backend:** Flask (`app.py`) deployed on Vercel via `@vercel/python`
- **Kit engine:** `kitgen.py` — paints a DLS UV template with any colors (Pillow)
- **Data:** **Supabase Postgres** — `orders` table + `kits` table (PNG stored as `bytea`)
- **Local fallback:** SQLite + local `/kits` files when `DATABASE_URL` is absent

Generated kits are served from the DB at `/kits/<id>.png`, which on Vercel is a
real public image URL — directly importable by DLS (no extra Storage keys needed).

## Project structure
```
app.py            Flask app: site + /api/orders + /api/generate + /kits + /admin/orders
kitgen.py         Builds a 512x512 DLS kit PNG from colors
index.html        Storefront + live "Design Your Kit" section
dls_template.png  Official DLS 512x512 UV template (base for generation)
schema.sql        Supabase Postgres schema (orders + kits)
vercel.json       Vercel Python build config
requirements.txt  flask, Pillow, psycopg2-binary, python-dotenv
.env.example      Environment variable template
```

## Local development
```bash
pip install -r requirements.txt
cp .env.example .env      # add your Supabase DATABASE_URL
python3 app.py            # http://localhost:5000
```
Without `DATABASE_URL` it runs fully locally (SQLite + local files).

## Supabase setup
1. Create a project at supabase.com
2. Get the **Connection string** (URI) for your database (pooler, port 6543)
3. Put it in `.env` as `DATABASE_URL` (the app appends `?sslmode=require`)
4. Tables are auto-created on first run (`init_db()`), or run `schema.sql` in SQL Editor

## Environment variables (set on Vercel)
```
DATABASE_URL=postgresql://postgres:PASSWORD@aws-1-...pooler.supabase.com:6543/postgres
WA_NUMBER=2348021016309
```

## Deploy (GitHub → Vercel + custom domain)
1. Push this repo to GitHub
2. Vercel: **Add New → Project → import the GitHub repo**
3. Set the env vars above (keep `DATABASE_URL` secret)
4. Deploy → you get a `.vercel.app` URL
5. **Domains:** add your custom domain, update its DNS per Vercel's instructions
6. Done — `/api/generate` returns a public `/kits/<id>.png` URL DLS can import directly

## Notes
- DLS needs a **one-time 300-diamond unlock** (per player account) to import custom kits.
- Kits are 512×512 PNG following the official DLS UV template.
- The DLS logo on the site is First Touch Games' trademark — use as a fan-made nod.
