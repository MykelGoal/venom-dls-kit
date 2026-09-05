# VENOM DLS — Custom DLS 26 Kits

A storefront + auto kit-generator for **Dream League Soccer 2026** custom kits.
Visitors design a kit (colors + style), get an import-ready 512×512 PNG, and can
order a custom kit via WhatsApp.

## Stack
- **Frontend:** static `index.html` (no build step)
- **Backend:** Flask (`app.py`) deployed on Vercel via `@vercel/python`
- **Kit engine:** `kitgen.py` — paints a DLS UV template with any colors (Pillow)
- **Data:** Supabase Postgres (`orders`) + Supabase Storage (`kits` public bucket)
- **Local fallback:** SQLite + local `/kits` files when Supabase env vars are absent

## Project structure
```
app.py            Flask app: site + /api/orders + /api/generate + /admin/orders
kitgen.py         Builds a 512x512 DLS kit PNG from colors
index.html        Storefront + live "Design Your Kit" section
dls_template.png  Official DLS 512x512 UV template (base for generation)
schema.sql        Supabase table + storage bucket + RLS policies
vercel.json       Vercel Python build config
requirements.txt  flask, Pillow, supabase
.env.example      Environment variable template
```

## Local development
```bash
pip install -r requirements.txt
python3 app.py                 # http://localhost:5000
```
Without Supabase env vars it runs fully locally (SQLite + local files).

## Supabase setup
1. Create a project at supabase.com
2. Run `schema.sql` in the SQL Editor (creates `orders` table + public `kits` bucket)
3. (Optional) create the `kits` bucket in Storage → make it **Public**
4. Copy `.env.example` → `.env` and fill in your keys

## Environment variables (set on Vercel)
```
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
KITS_BUCKET=kits
WA_NUMBER=2348021016309
```

## Deploy (GitHub → Vercel + custom domain)
1. Push this repo to GitHub
2. In Vercel: **Add New → Project → import the GitHub repo**
3. Framework preset: leave as is (uses `vercel.json`); set the env vars above
4. Deploy → you get a `.vercel.app` URL
5. **Domains:** add your custom domain, update its DNS (A/CNAME) per Vercel's instructions
6. Done — `/api/generate` returns public Supabase Storage URLs that DLS can import directly

## Notes
- DLS needs a **one-time 300-diamond unlock** (per player account) to import custom kits.
- Generated kits are 512×512 PNG following the official DLS UV template.
- The DLS logo on the site is First Touch Games' trademark — use as a fan-made nod.
