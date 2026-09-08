"""Sozlamalar: .env o'zgaruvchilari, konstantalar va config.json bilan ishlash."""
import os
import sys
import json
import logging

from dotenv import load_dotenv

load_dotenv()

# Windows uchun UTF-8 encoding tuzatish
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger('telethon').setLevel(logging.WARNING)  # ortiqcha shovqinni kamaytirish
log = logging.getLogger("userbot")

# --- Telegram ---
def _required(name):
    """Majburiy .env o'zgaruvchisi. Bo'lmasa tushunarli xabar bilan to'xtaymiz."""
    value = os.getenv(name)
    if not value:
        sys.exit(f"❌ .env faylida {name} ko'rsatilmagan. Namuna: .env.example")
    return value


API_ID = int(_required('API_ID'))
API_HASH = _required('API_HASH')
PHONE = _required('PHONE')
BOT_TOKEN = _required('BOT_TOKEN')
ADMIN_ID = int(_required('ADMIN_ID'))

# --- AI kalitlari ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# --- Qo'shimcha ---
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tashkent')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 60))
CONFIG_FILE = 'config.json'
TELEGRAM_LIMIT = 4096  # bitta xabarning maksimal uzunligi


def load_config():
    """config.json ni o'qish."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config):
    """config.json ga yozish."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
