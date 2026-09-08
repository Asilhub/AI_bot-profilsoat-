"""Umumiy yordamchi funksiyalar."""
from datetime import datetime, timedelta

import pytz
import requests

from config import TELEGRAM_LIMIT, TIMEZONE
from state import STATE


def get_signature(model_name):
    """AI javobi ostidagi imzo."""
    short_model = model_name.split('-')[0].capitalize()
    if 'llama' in model_name:
        short_model = "Llama 3"
    elif 'gemini' in model_name:
        short_model = "Gemini"

    return (
        f"\n\n🤖 **@yozuras xabaringizni o'qigunicha men sizga yordam bera olaman.**\n"
        f"⚙️ _Model: {short_model}_"
    )


def get_coords(city_name):
    """Shahar nomidan koordinata (open-meteo geocoding)."""
    try:
        url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city_name}&count=1&language=en&format=json"
        )
        res = requests.get(url, timeout=5).json()
        if 'results' in res:
            return res['results'][0]['latitude'], res['results'][0]['longitude']
    except Exception:
        pass
    return None, None


def build_msg_link(msg):
    """Xabarga to'g'ridan-to'g'ri havola yasash (ommaviy yoki yopiq kanal)."""
    try:
        chat = getattr(msg, 'chat', None)
        username = getattr(chat, 'username', None) if chat else None
        if username:
            return f"https://t.me/{username}/{msg.id}"
        cid = str(msg.chat_id)
        if cid.startswith('-100'):
            return f"https://t.me/c/{cid[4:]}/{msg.id}"
    except Exception:
        pass
    return ""


def parse_delay(s):
    """'30s', '10m', '2h' yoki '18:00' ni soniyaga aylantirish."""
    s = (s or "").strip().lower()
    try:
        if s.endswith('s'):
            return int(s[:-1])
        if s.endswith('m'):
            return int(s[:-1]) * 60
        if s.endswith('h'):
            return int(s[:-1]) * 3600
        if ':' in s:
            tz = pytz.timezone(TIMEZONE)
            now = datetime.now(tz)
            hh, mm = map(int, s.split(':'))
            target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return (target - now).total_seconds()
    except Exception:
        return None
    return None


def chunk_text(text, size=TELEGRAM_LIMIT):
    """Uzun matnni Telegram limitiga mos bo'laklarga ajratish."""
    text = text or "..."
    if len(text) <= size:
        return [text]
    parts = []
    while text:
        parts.append(text[:size])
        text = text[size:]
    return parts


async def bot_send(event, text, edit=False):
    """Javobni (kerak bo'lsa bo'lib) yuborish. Bot yuborayotgan vaqtda faollik hisoblanmaydi."""
    STATE['suppress_activity'] = True
    try:
        parts = chunk_text(text)
        if edit:
            await event.edit(parts[0])
        else:
            await event.reply(parts[0])
        for p in parts[1:]:
            await event.respond(p)
    finally:
        STATE['suppress_activity'] = False
