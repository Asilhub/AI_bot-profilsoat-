"""Profil bio'sini vaqt / shahar / ob-havo bilan davriy yangilash."""
import asyncio
from datetime import datetime

import pytz
import requests
from telethon.tl.functions.account import UpdateProfileRequest

from config import load_config, TIMEZONE, UPDATE_INTERVAL
from clients import user_client
from helpers import get_coords


def get_weather():
    config = load_config()
    city_name = config.get('user_city', 'Andijan')
    try:
        lat, lon = get_coords(city_name)
        if not lat:
            lat, lon = 40.7821, 72.3442
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Tashkent"
        )
        r = requests.get(url, timeout=3).json()
        t = round(r['current_weather']['temperature'])
        c = r['current_weather']['weathercode']
        e = "☀️" if c == 0 else "⛅" if c < 4 else "🌧" if c < 60 else "❄️"
        return f"{e} {t:+d}°C"
    except Exception:
        return ""


async def update_bio():
    while True:
        try:
            tz = pytz.timezone(TIMEZONE)
            now = datetime.now(tz)
            time_str = now.strftime('%H:%M')
            config = load_config()
            city = config.get('user_city', 'Andijan')
            trig = config.get('activation_trigger', '.')
            w = get_weather()

            bio = f"✨ {time_str} | 📍 {city}"
            if w:
                bio += f" | {w}"
            bio += f" | 🧠 AI: {trig}savol"

            await user_client(UpdateProfileRequest(about=bio))
            await asyncio.sleep(UPDATE_INTERVAL)
        except Exception:
            await asyncio.sleep(20)
