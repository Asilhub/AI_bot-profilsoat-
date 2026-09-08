"""
Telegram AI Userbot + Manager Bot — kirish nuqtasi
==================================================
Ishga tushirish:  python userbot.py

Modullar (core/ papkasida):
  config.py            — .env, konstantalar, config.json, logging
  clients.py           — Telegram klientlari + Groq/Gemini
  state.py             — suhbat xotirasi + avto-javob holati/qoidalari
  ai.py                — matn/rasm/ovoz uchun AI funksiyalari
  helpers.py           — imzo, ob-havo koordinatasi, havola, vaqt, matn bo'lish, yuborish
  bio.py               — profil bio'sini davriy yangilash
  commands.py          — tezkor komandalar (.tarjima/.qisqartir/.tahrirla/.eslat) + shop-qidiruv
  handlers_manager.py  — admin panel (manager bot)
  handlers_userbot.py  — kiruvchi/chiquvchi xabar handlerlari
"""
import os
import sys
import asyncio

# Yordamchi modullar core/ papkasida — uni import yo'liga qo'shamiz
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

from config import PHONE, BOT_TOKEN, ADMIN_ID, log
from clients import user_client, bot_client
from bio import update_bio

# Handler modullarini import qilish = dekoratorlar orqali handlerlarni ro'yxatdan o'tkazish
import handlers_manager  # noqa: F401,E402
import handlers_userbot  # noqa: F401,E402


async def main():
    log.info("🚀 Ishga tushyapti...")
    await user_client.start(phone=PHONE)
    await bot_client.start(bot_token=BOT_TOKEN)

    # Faqat ADMINGA xabar (Saved Messages ga emas)
    try:
        await bot_client.send_message(ADMIN_ID, "🚀 **Userbot muvaffaqiyatli ishga tushdi!**")
    except Exception:
        pass

    log.info("✅ Tayyor")
    asyncio.create_task(update_bio())

    # Tarmoq uzilib ketsa ham bot o'lib qolmasligi uchun — qayta ulanib ishlashda davom etadi
    while True:
        try:
            await asyncio.gather(
                user_client.run_until_disconnected(),
                bot_client.run_until_disconnected(),
            )
            break  # toza uzilish — chiqamiz
        except Exception as e:
            log.warning("Ulanish uzildi (%s). 5s dan keyin qayta ulanaman...", type(e).__name__)
            await asyncio.sleep(5)
            for c in (user_client, bot_client):
                try:
                    if not c.is_connected():
                        await c.connect()
                except Exception:
                    pass


if __name__ == '__main__':
    asyncio.run(main())
