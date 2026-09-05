import os
import uuid
from flask import Blueprint, Response, request, jsonify, send_from_directory, current_app
from config import DATABASE_URL
from db import ensure_db, conn
from kitgen import generate_kit

bp = Blueprint('kits', __name__)


@bp.route('/kits/<path:filename>')
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
    return send_from_directory(os.path.join(current_app.static_folder, 'img'), filename)


@bp.route('/api/generate', methods=['POST'])
def generate():
    d = request.get_json(silent=True) or request.form.to_dict() or {}
    primary = d.get('primary', '#22C55E')
    secondary = d.get('secondary', '#0C0E10')
    socks = d.get('socks') or secondary
    style = d.get('style', 'home')
    club = (d.get('club') or 'kit').replace(' ', '_').replace('/', '_')
    kid = f"{club}_{style}_{uuid.uuid4().hex[:10]}"
    tmp = os.path.join('/tmp', kid + '.png')
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
    if DATABASE_URL:
        return jsonify({'ok': False, 'error': 'database unavailable'}), 500
    # local dev fallback: keep file under static/img
    import shutil
    dest = os.path.join(current_app.static_folder, 'img', kid + '.png')
    try:
        shutil.copy(tmp, dest)
    except Exception:
        pass
    return jsonify({'ok': True, 'url': f'/img/{kid}.png'})
