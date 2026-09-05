import os
import sqlite3
from flask import Blueprint, send_from_directory, Response
from config import DATABASE_URL, BASE
from db import ensure_db, conn

bp = Blueprint('pages', __name__)
STATIC = os.path.join(BASE, 'static')


@bp.route('/')
def index():
    return send_from_directory(STATIC, 'index.html')


@bp.route('/admin/orders')
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
        try:
            c = sqlite3.connect('/tmp/venom_orders.db'); c.row_factory = sqlite3.Row
            rows = [dict(r) for r in c.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()]
            c.close()
        except Exception:
            rows = []
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
