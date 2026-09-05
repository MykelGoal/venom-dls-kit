"""VENOM DLS — Flask backend (Vercel + Supabase ready).

Modes:
  - With SUPABASE_URL + key set  -> orders go to Supabase Postgres,
    generated kits uploaded to a PUBLIC Supabase Storage bucket (import-ready URLs).
  - Without Supabase env vars     -> local SQLite + local /kits files (dev fallback).

Deploy: Vercel Python builder (@vercel/python) -> app.py, see vercel.json.
"""
import os
import io
import uuid
import sqlite3
from flask import Flask, request, send_from_directory, jsonify, Response

from kitgen import generate_kit

BASE = os.path.dirname(os.path.abspath(__file__))
KITS_DIR = os.path.join(BASE, 'kits')
os.makedirs(KITS_DIR, exist_ok=True)

app = Flask(__name__, static_folder=BASE, static_url_path='')
WA_NUMBER = os.environ.get('WA_NUMBER', '2348021016309')


# ---------------- Supabase (optional) ----------------
def get_sb():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
    if not (url and key):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


sb = get_sb()


def db():
    conn = sqlite3.connect(os.path.join(BASE, 'orders.db'))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, name TEXT, contact TEXT, club TEXT,
        style TEXT, details TEXT, kit_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.commit()
    c.close()


init_db()


# ---------------- Routes ----------------
@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/kits/<path:filename>')
def kits(filename):
    return send_from_directory(KITS_DIR, filename)


def _payload():
    d = request.get_json(silent=True)
    return d or request.form.to_dict() or {}


@app.route('/api/orders', methods=['POST'])
def orders():
    d = _payload()
    oid = uuid.uuid4().hex[:10]
    kit_url = d.get('kit_url')
    if sb is not None:
        sb.table('orders').insert({
            'id': oid, 'name': d.get('name'), 'contact': d.get('contact'),
            'club': d.get('club'), 'style': d.get('style'),
            'details': d.get('details'), 'kit_url': kit_url,
        }).execute()
    else:
        conn = db()
        conn.execute(
            'INSERT INTO orders (id,name,contact,club,style,details,kit_url) '
            'VALUES (?,?,?,?,?,?,?)',
            (oid, d.get('name'), d.get('contact'), d.get('club'),
             d.get('style'), d.get('details'), kit_url))
        conn.commit()
        conn.close()
    wa = (f"https://wa.me/{WA_NUMBER}?text=New%20order%20from%20"
          f"{d.get('name','')}%20-%20club%20{d.get('club','')}")
    return jsonify({'ok': True, 'order_id': oid, 'notify': wa})


@app.route('/api/generate', methods=['POST'])
def generate():
    d = _payload()
    primary = d.get('primary', '#22C55E')
    secondary = d.get('secondary', '#0C0E10')
    socks = d.get('socks') or secondary
    style = d.get('style', 'home')
    club = (d.get('club') or 'kit').replace(' ', '_').replace('/', '_')
    fname = f"{club}_{style}_{uuid.uuid4().hex[:6]}.png"

    tmp = os.path.join(KITS_DIR, fname)
    generate_kit(tmp, primary, secondary, socks, style)
    with open(tmp, 'rb') as f:
        data = f.read()

    if sb is not None:
        bucket = os.environ.get('KITS_BUCKET', 'kits')
        sb.storage.from_(bucket).upload(
            fname, data, {'content-type': 'image/png', 'upsert': True})
        url = sb.storage.from_(bucket).get_public_url(fname)
        try:
            os.remove(tmp)
        except Exception:
            pass
    else:
        url = f"/kits/{fname}"

    return jsonify({'ok': True, 'url': url})


@app.route('/admin/orders')
def admin():
    if sb is not None:
        rows = sb.table('orders').select('*').order('created_at', desc=True).limit(200).execute().data
    else:
        conn = db()
        rows = [dict(r) for r in conn.execute(
            'SELECT * FROM orders ORDER BY created_at DESC').fetchall()]
        conn.close()

    html = ['<html><head><meta charset="utf-8"><title>VENOM DLS Orders</title>'
            '<style>body{font-family:sans-serif;background:#0b0d12;color:#eee;padding:24px}'
            'h2{color:#39ff14}table{width:100%;border-collapse:collapse}'
            'th,td{border:1px solid #262d3a;padding:8px;text-align:left;font-size:14px}'
            'th{background:#141821}</style></head><body><h2>VENOM DLS — Orders</h2>']
    if not rows:
        html.append('<p>No orders yet.</p>')
    else:
        html.append('<table><tr><th>ID</th><th>Name</th><th>Contact</th><th>Club</th>'
                    '<th>Style</th><th>Details</th><th>Kit</th><th>When</th></tr>')
        for r in rows:
            html.append(
                f"<tr><td>{r.get('id')}</td><td>{r.get('name')}</td><td>{r.get('contact')}</td>"
                f"<td>{r.get('club')}</td><td>{r.get('style')}</td><td>{r.get('details')}</td>"
                f"<td>{r.get('kit_url') or '-'}</td><td>{r.get('created_at')}</td></tr>")
        html.append('</table>')
    html.append('</body></html>')
    return Response(''.join(html), mimetype='text/html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
