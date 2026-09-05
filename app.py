"""VENOM DLS — WSGI entrypoint.

Serves the static storefront from /static and mounts the API blueprints.
Deploy target: Vercel (@vercel/python builder -> this file).
"""
import os
from flask import Flask
from config import BASE
from routes import pages, kits, orders
from db import init_db

app = Flask(__name__, static_folder=os.path.join(BASE, 'static'), static_url_path='')

app.register_blueprint(pages.bp)
app.register_blueprint(kits.bp)
app.register_blueprint(orders.bp)

# Best-effort DB init; never crash the function if the DB is unreachable.
try:
    init_db()
except Exception as e:
    print('init_db non-fatal:', e)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
