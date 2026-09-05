-- ============================================================
--  VENOM DLS — Supabase Postgres schema
--  Run in Supabase -> SQL Editor. (The app also auto-creates
--  these tables on first run via init_db().)
-- ============================================================

-- Orders captured from the storefront
create table if not exists public.orders (
  id         text primary key,
  name       text,
  contact    text,
  club       text,
  style      text,
  details    text,
  kit_url    text,
  created_at timestamptz default now()
);

-- Generated kits (PNG stored as bytea; served at /kits/<id>.png)
create table if not exists public.kits (
  id              text primary key,
  club            text,
  style           text,
  primary_color   text,
  secondary_color text,
  socks_color     text,
  png             bytea,
  created_at      timestamptz default now()
);

-- Row Level Security: block public reads; writes happen server-side
-- using the DATABASE_URL (which connects with the postgres role).
alter table public.orders enable row level security;
alter table public.kits    enable row level security;

-- The app connects with the postgres role (via the pooler), which
-- bypasses RLS, so no anon policies are required for writes.
