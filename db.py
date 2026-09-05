"""VENOM DLS — database layer (Supabase Postgres with local SQLite fallback).

The connection is LAZY and CRASH-PROOF: a failed DB connection must never
take down the whole function. Tables are created on first use.
"""
import os
import sqlite3
import psycopg2
from config import DATABASE_URL, VERCEL, KITS_DIR

ORDERS_SQL = '''CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY, name TEXT, contact TEXT, club TEXT, style TEXT,
    details TEXT, kit_url TEXT, created_at TIMESTAMPTZ DEFAULT now())'''
KITS_SQL = '''CREATE TABLE IF NOT EXISTS kits (
    id TEXT PRIMARY KEY, club TEXT, style TEXT,
    primary_color TEXT, secondary_color TEXT, socks_color TEXT,
    png BYTEA, created_at TIMESTAMPTZ DEFAULT now())'''

DB_READY = False


def _url():
    u = DATABASE_URL
    if u and 'sslmode' not in u:
        u += ('&' if '?' in u else '?') + 'sslmode=require'
    return u


def conn():
    return psycopg2.connect(_url(), connect_timeout=10)


def init_db():
    global DB_READY
    if not DATABASE_URL:
        try:
            path = '/tmp/venom_orders.db' if VERCEL else os.path.join(BASE_SQLITE())
            c = sqlite3.connect(path); c.row_factory = sqlite3.Row
            c.execute('''CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY, name TEXT, contact TEXT, club TEXT,
                style TEXT, details TEXT, kit_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            c.commit(); c.close()
            DB_READY = True
        except Exception as e:
            print('sqlite init failed:', e)
        return
    try:
        c = conn(); cur = c.cursor()
        cur.execute(ORDERS_SQL); cur.execute(KITS_SQL)
        c.commit(); c.close()
        DB_READY = True
    except Exception as e:
        print('supabase init failed:', e)
        DB_READY = False


def BASE_SQLITE():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.db')


def ensure_db():
    if not DB_READY:
        try:
            init_db()
        except Exception:
            pass
    return DB_READY
