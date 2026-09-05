-- ============================================================
--  VENOM DLS — Supabase schema
--  Run this in Supabase → SQL Editor, then create the storage bucket.
-- ============================================================

-- 1) Orders table
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

alter table public.orders enable row level security;

-- Anonymous visitors can INSERT orders (used by the API with the anon key).
-- Reads are blocked for anon; the admin view uses the service-role key server-side.
drop policy if exists "anon insert orders" on public.orders;
create policy "anon insert orders"
  on public.orders for insert to anon with check (true);

-- 2) Storage bucket for generated kits (public so DLS can fetch the import URL)
insert into storage.buckets (id, name, public)
values ('kits', 'kits', true)
on conflict (id) do update set public = true;

-- (Optional) restrict uploads to authenticated/service-role only:
drop policy if exists "authenticated upload kits" on storage.objects;
create policy "authenticated upload kits"
  on storage.objects for insert to service_role with check (bucket_id = 'kits');
