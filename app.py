"""VENOM DLS — Flask backend (Vercel + Supabase Postgres ready).

Key design note: database access is LAZY and CRASH-PROOF. The app must
never fail to import/start just because the DB is unreachable (that caused
FUNCTION_INVOCATION_FAILED on Vercel). Tables are created on first use and
any DB error is caught and logged, not raised.

Data layer:
  - DATABASE_URL set  -> Supabase Postgres (orders + kits BYTEA)
  - DATABASE_URL unset -> local SQLite + local /kits files (dev fallback)
"""
import os
import uuid
from flask import Flask, request, send_from_directory, jsonify, Response
from PIL import Image

from kitgen import generate_kit

BASE = os.path.dirname(os.path.abspath(__file__))
KITS_DIR = os.path.join(BASE, 'kits')
try:
    os.makedirs(KITS_DIR, exist_ok=True)
except Exception:
    pass

app = Flask(__name__, static_folder=BASE, static_url_path='')
WA_NUMBER = os.environ.get('WA_NUMBER', '2348021016309')
DATABASE_URL = os.environ.get('DATABASE_URL')
try:
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.environ.get('DATABASE_URL') or DATABASE_URL
except Exception:
    pass

DB_READY = False

ORDERS_SQL = '''CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY, name TEXT, contact TEXT, club TEXT, style TEXT,
    details TEXT, kit_url TEXT, created_at TIMESTAMPTZ DEFAULT now())'''
KITS_SQL = '''CREATE TABLE IF NOT EXISTS kits (
    id TEXT PRIMARY KEY, club TEXT, style TEXT,
    primary_color TEXT, secondary_color TEXT, socks_color TEXT,
    png BYTEA, created_at TIMESTAMPTZ DEFAULT now())'''


def _url():
    u = DATABASE_URL
    if u and 'sslmode' not in u:
        u += ('&' if '?' in u else '?') + 'sslmode=require'
    return u


def conn():
    import psycopg2
    return psycopg2.connect(_url(), connect_timeout=10)


def init_db():
    """Create tables if needed. Never raises."""
    global DB_READY
    if not DATABASE_URL:
        import sqlite3
        db_path = '/tmp/venom_orders.db' if os.environ.get('VERCEL') else os.path.join(BASE, 'orders.db')
        try:
            c = sqlite3.connect(db_path); c.row_factory = sqlite3.Row
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


# Best-effort at import, but NEVER crash the function if the DB is down.
try:
    init_db()
except Exception as e:
    print('init_db non-fatal:', e)


def ensure_db():
    if not DB_READY:
        try:
            init_db()
        except Exception:
            pass
    return DB_READY


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/kits/<path:filename>')
def kits(filename):
    if DATABASE_URL:
        ensure_db()
        kid = filename.rsplit('.', 1)[0]
        try:
            c = conn(); cur = c.cursor()
            cur.execute('SELECT png FROM kits WHERE id=%s', (kid,))
            row = cur.fetchone(); c.close()
            if row and row[0]:
                return Response(bytes(row[0]), mimetype='image/png')
        except Exception as e:
            print('kit fetch failed:', e)
        return ('not found', 404)
    return send_from_directory(KITS_DIR, filename)


def _payload():
    d = request.get_json(silent=True)
    return d or request.form.to_dict() or {}


@app.route('/api/orders', methods=['POST'])
def orders():
    d = _payload()
    oid = uuid.uuid4().hex[:10]
    kit_url = d.get('kit_url')
    if ensure_db() and DATABASE_URL:
        try:
            c = conn(); cur = c.cursor()
            cur.execute(
                'INSERT INTO orders (id,name,contact,club,style,details,kit_url) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s)',
                (oid, d.get('name'), d.get('contact'), d.get('club'),
                 d.get('style'), d.get('details'), kit_url))
            c.commit(); c.close()
        except Exception as e:
            print('order insert failed:', e)
            return jsonify({'ok': False, 'error': 'db error'}), 500
    else:
        import sqlite3
        db_path = '/tmp/venom_orders.db' if os.environ.get('VERCEL') else os.path.join(BASE, 'orders.db')
        c = sqlite3.connect(db_path)
        try:
            c.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)',
                      (oid, d.get('name'), d.get('contact'), d.get('club'),
                       d.get('style'), d.get('details'), kit_url, None))
            c.commit()
        except Exception as e:
            print('sqlite order failed:', e)
        c.close()
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
    kid = f"{club}_{style}_{uuid.uuid4().hex[:10]}"
    tmp = os.path.join('/tmp', kid + '.png')   # Vercel FS is read-only except /tmp
    try:
        generate_kit(tmp, primary, secondary, socks, style)
    except Exception as e:
        print('kitgen failed:', e)
        return jsonify({'ok': False, 'error': 'generation failed'}), 500
    with open(tmp, 'rb') as f:
        data = f.read()
    if ensure_db() and DATABASE_URL:
        import psycopg2
        try:
            c = conn(); cur = c.cursor()
            cur.execute(
                'INSERT INTO kits (id,club,style,primary_color,secondary_color,'
                'socks_color,png) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                (kid, club, style, primary, secondary, socks, psycopg2.Binary(data)))
            c.commit(); c.close()
            return jsonify({'ok': True, 'url': f'/kits/{kid}.png'})
        except Exception as e:
            print('kit insert failed:', e)
            return jsonify({'ok': False, 'error': 'db error'}), 500
    # local fallback: keep file in KITS_DIR so /kits can serve it
    import shutil
    try:
        shutil.copy(tmp, os.path.join(KITS_DIR, kid + '.png'))
    except Exception:
        pass
    return jsonify({'ok': True, 'url': f'/kits/{kid}.png'})


@app.route('/admin/orders')
def admin():
    rows = []
    if ensure_db() and DATABASE_URL:
        try:
            c = conn(); cur = c.cursor()
            cur.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 200')
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]; c.close()
        except Exception as e:
            print('admin fetch failed:', e)
    else:
        import sqlite3
        db_path = '/tmp/venom_orders.db' if os.environ.get('VERCEL') else os.path.join(BASE, 'orders.db')
        c = sqlite3.connect(db_path); c.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in c.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()]
        except Exception:
            rows = []
        c.close()
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
