"""Telegram klientlari va AI provayderlarini sozlash."""
import google.generativeai as genai
from groq import Groq
from telethon import TelegramClient

from config import API_ID, API_HASH, GROQ_API_KEY, GEMINI_API_KEY

# Telegram klientlari (tarmoq uzilsa — ko'p marta avtomatik qayta ulanadi)
_conn = dict(connection_retries=10000, retry_delay=3, auto_reconnect=True)
user_client = TelegramClient('userbot_v2', API_ID, API_HASH, **_conn)   # shaxsiy akkaunt
bot_client = TelegramClient('manager_v2', API_ID, API_HASH, **_conn)    # boshqaruv boti

# Groq (Llama / Gemma + Whisper)
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception:
        pass

# Google Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
