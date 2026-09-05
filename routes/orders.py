import uuid
import sqlite3
from flask import Blueprint, request, jsonify
from config import DATABASE_URL, WA_NUMBER
from db import ensure_db, conn

bp = Blueprint('orders', __name__)


@bp.route('/api/orders', methods=['POST'])
def orders():
    d = request.get_json(silent=True) or request.form.to_dict() or {}
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
    elif DATABASE_URL:
        return jsonify({'ok': False, 'error': 'database unavailable'}), 500
    else:
        try:
            c = sqlite3.connect('/tmp/venom_orders.db')
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
