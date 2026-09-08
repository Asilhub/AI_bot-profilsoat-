"""Userbot (shaxsiy akkaunt) xabar handlerlari: qo'lda trigger, komandalar, avto-javob."""
import time
import asyncio

from telethon import events

from config import load_config
from clients import user_client
from state import STATE, get_history, add_history, should_auto_answer
from ai import ask_ai_universal, ask_ai_vision, transcribe_voice
from helpers import bot_send, get_signature
from commands import QUICK_PROMPTS, cmd_search, cmd_quick, cmd_remind


# Faollikni kuzatish (away-rejim uchun) — har chiquvchi xabarda
@user_client.on(events.NewMessage(outgoing=True))
async def track_activity(event):
    if STATE.get('suppress_activity'):
        return
    STATE['last_activity'] = time.time()


# QO'LDA TRIGGER + KOMANDALAR (chiquvchi xabar)
@user_client.on(events.NewMessage(outgoing=True))
async def manual_trigger_handler(event):
    config = load_config()
    trigger = config.get('activation_trigger', '.')
    if not event.text or not event.text.startswith(trigger):
        return
    body = event.text[len(trigger):].strip()
    if not body:
        return

    parts = body.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ''

    # --- Maxsus komandalar ---
    if cmd in ('qidir', 'top'):
        await cmd_search(event, arg)
    elif cmd in QUICK_PROMPTS:
        await cmd_quick(event, cmd, arg)
    elif cmd == 'eslat':
        await cmd_remind(event, arg)
    # --- Oddiy AI savol ---
    else:
        await event.edit("🧠...")
        answer = await ask_ai_universal(body)
        await bot_send(event, answer, edit=True)


# KIRUVCHI XABARLAR (matn / ovoz / rasm) — yagona handler
@user_client.on(events.NewMessage(incoming=True))
async def incoming_handler(event):
    if not event.is_private:
        return

    sender = await event.get_sender()
    if sender and sender.bot:
        return

    config = load_config()
    trigger = config.get('activation_trigger', '.')
    text = event.text or ''

    is_trigger = text.startswith(trigger) and not text.startswith('/')
    is_voice = bool(getattr(event, 'voice', None))
    is_photo = bool(getattr(event, 'photo', None))

    # Javob berish kerakmi va qaysi rejimda?
    if is_trigger:
        mode = 'trigger'
    else:
        if text.startswith('/'):
            return
        if not config.get('auto_answer_enabled'):
            return
        if not should_auto_answer(event, config):
            return
        mode = 'auto'

    chat_id = event.chat_id
    mem_on = config.get('memory_enabled', True)
    mem_limit = config.get('memory_limit', 10)
    history = get_history(chat_id, mem_limit) if mem_on else []

    # Kirish ma'lumotini aniqlash (ovoz / rasm / matn)
    image_bytes = None
    if is_voice:
        audio = await event.download_media(file=bytes)
        question = await transcribe_voice(audio)
        if not question:
            return
        user_log = f"🎤 {question}"
    elif is_photo:
        image_bytes = await event.download_media(file=bytes)
        caption = text[len(trigger):].strip() if is_trigger else text.strip()
        question = caption
        user_log = f"🖼 {caption}" if caption else "🖼 [rasm]"
    else:
        question = text[len(trigger):].strip() if is_trigger else text.strip()
        if not question:
            return
        user_log = question

    # Prompt tanlash
    if mode == 'trigger':
        prompt = config.get('system_instruction', '')
    else:
        prompt = config.get('auto_answer_prompt') or config.get('system_instruction', '')
        await asyncio.sleep(3)  # tabiiy ko'rinish uchun

    # AI javobi
    async with user_client.action(chat_id, 'typing'):
        if image_bytes is not None:
            answer = await ask_ai_vision(image_bytes, question, custom_prompt=prompt)
        else:
            answer = await ask_ai_universal(question, custom_prompt=prompt, history=history)

    sig = get_signature(config.get('current_model'))
    await bot_send(event, f"{answer}\n{sig}")

    # Xotira va holatni yangilash
    if mem_on:
        add_history(chat_id, 'user', user_log, mem_limit)
        add_history(chat_id, 'assistant', answer, mem_limit)
    if mode == 'auto':
        STATE['last_reply'][chat_id] = time.time()
