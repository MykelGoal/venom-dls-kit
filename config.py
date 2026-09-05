"""VENOM DLS — configuration & env loading."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (os.environ.get('DATABASE_URL') or '').strip()
WA_NUMBER = os.environ.get('WA_NUMBER', '2348021016309')
VERCEL = bool(os.environ.get('VERCEL'))

BASE = os.path.dirname(os.path.abspath(__file__))
KITS_DIR = os.path.join(BASE, 'kits')
STATIC_DIR = os.path.join(BASE, 'static')
try:
    os.makedirs(KITS_DIR, exist_ok=True)
except Exception:
    pass
