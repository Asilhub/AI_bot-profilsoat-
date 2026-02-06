from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import UpdateProfileRequest
import asyncio
from datetime import datetime
import pytz
import sys
import os
import json
import requests
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Fix Encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# CONFIG
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tashkent')
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 60))
CONFIG_FILE = 'config.json'

# CLIENTS
user_client = TelegramClient('userbot_v2', API_ID, API_HASH)
bot_client = TelegramClient('manager_v2', API_ID, API_HASH)

# API SETUP
groq_client = None
if GROQ_API_KEY:
    try: groq_client = Groq(api_key=GROQ_API_KEY)
    except: pass

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# HELPER
def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, indent=2, ensure_ascii=False)

def get_signature(model_name):
    short_model = model_name.split('-')[0].capitalize()
    if 'llama' in model_name: short_model = "Llama 3"
    elif 'gemini' in model_name: short_model = "Gemini"
    
    return (
        f"\n\n🤖 **@yozuras xabaringizni o'qigunicha men sizga yordam bera olaman.**\n"
        f"⚙️ _Model: {short_model}_"
    )

def get_coords(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        res = requests.get(url, timeout=5).json()
        if 'results' in res:
            return res['results'][0]['latitude'], res['results'][0]['longitude']
    except: pass
    return None, None

# AI ENGINE
async def ask_ai_universal(question, custom_prompt=None):
    config = load_config()
    model_name = config.get('current_model', 'llama-3.1-8b-instant')
    
    if custom_prompt:
        sys_instruction = custom_prompt
    else:
        sys_instruction = config.get('system_instruction', '')
    
    try:
        # GROQ
        if 'llama' in model_name or 'mixtral' in model_name or 'gemma' in model_name:
            if not groq_client: return "❌ Groq API error"
            completion = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": sys_instruction}, {"role": "user", "content": question}],
                model=model_name,
                temperature=0.7, max_tokens=1024
            )
            return completion.choices[0].message.content
        # GEMINI
        else:
            if not GEMINI_API_KEY: return "❌ Gemini API error"
            model = genai.GenerativeModel(model_name)
            full_prompt = f"{sys_instruction}\n\nUser: {question}"
            response = await model.generate_content_async(full_prompt)
            return response.text if response else "..."
    except Exception as e:
        return f"❌ Error: {str(e)[:50]}"

# =========================================
# MANAGER BOT
# =========================================
@bot_client.on(events.NewMessage(pattern='/start'))
async def bot_start(event):
    if event.sender_id != ADMIN_ID: return
    await show_main_menu(event, is_new=True)

async def show_main_menu(event, is_new=False):
    config = load_config()
    is_auto = "✅ ON" if config.get('auto_answer_enabled') else "🔴 OFF"
    curr_model = config.get('current_model')
    trigger = config.get('activation_trigger', '.')
    city = config.get('user_city', 'Andijan')
    
    # Model nomini qisqartirish
    short_model = curr_model.replace('gemini-', '').replace('llama-', '').split('-')[0].capitalize()

    text = (
        f"🛠 **Admin Panel**\n\n"
        f"🧠 **Model:** `{short_model}`\n"
        f"📍 **Shahar:** `{city}`\n"
        f"⚡️ **Trigger:** `{trigger}`\n"
        f"🗣 **Avto-Javob:** {is_auto}"
    )
    buttons = [
        [Button.inline("🧠 Model", b'menu_models'), Button.inline(f"🗣 Avto: {is_auto}", b'toggle_auto')],
        [Button.inline(f"📍 Shahar: {city}", b'menu_cities')],
        [Button.inline("📝 Asosiy Prompt", b'edit_prompt'), Button.inline("🤖 Auto Prompt", b'edit_auto_prompt')],
        [Button.inline(f"⚡️ Trigger: {trigger}", b'edit_trigger')],
        [Button.inline("📡 Status", b'check_status')]
    ]
    if is_new: await event.reply(text, buttons=buttons)
    else: 
        try: await event.edit(text, buttons=buttons)
        except: await event.reply(text, buttons=buttons)

@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    if event.sender_id != ADMIN_ID: return
    data = event.data.decode('utf-8')
    config = load_config()

    if data == 'menu_main': await show_main_menu(event)
    
    elif data == 'menu_models':
        models = config.get('available_models', [])
        buttons = []
        row = []
        for m in models:
            tick = "✅ " if m == config['current_model'] else ""
            short_name = m.replace('gemini-', '').replace('llama-', '').split('-')[0].capitalize()
            row.append(Button.inline(f"{tick}{short_name}", f'set_model:{m}'.encode()))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row: buttons.append(row)
        buttons.append([Button.inline("🔙", b'menu_main')])
        await event.edit("🧠 Modelni tanlang:", buttons=buttons)
        
    elif data.startswith('set_model:'):
        config['current_model'] = data.split(':')[1]
        save_config(config)
        await show_main_menu(event)
    
    elif data == 'menu_cities':
        # VILOYATLAR RO'YXATI
        cities = [
            "Tashkent", "Andijan", "Namangan", "Fergana", 
            "Samarkand", "Bukhara", "Navoiy", "Jizzakh", 
            "Termez", "Urgench", "Nukus", "Qarshi", "Guliston", "Marhamat"
        ]
        buttons = []
        row = []
        for c in cities:
            tick = "✅ " if c == config.get('user_city') else ""
            row.append(Button.inline(f"{tick}{c}", f'set_city:{c}'.encode()))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row: buttons.append(row)
        buttons.append([Button.inline("🔙", b'menu_main')])
        await event.edit("📍 Shaharni tanlang:", buttons=buttons)
    
    elif data.startswith('set_city:'):
        city = data.split(':')[1]
        config['user_city'] = city
        save_config(config)
        await event.answer(f"✅ Shahar o'zgardi: {city}")
        await show_main_menu(event)

    elif data == 'toggle_auto':
        config['auto_answer_enabled'] = not config.get('auto_answer_enabled')
        save_config(config)
        await show_main_menu(event)

    elif data == 'edit_trigger':
        await event.edit("⚡️ Yuboring: `/set_trigger .`", buttons=[[Button.inline("🔙", b'menu_main')]])
    
    elif data == 'edit_prompt':
        p = config.get('system_instruction', '')
        await event.edit(f"📝 **Asosiy Prompt** (Trigger uchun):\n`{p}`\n\nCommand: `/set_prompt yangi matn`", buttons=[[Button.inline("🔙", b'menu_main')]])

    elif data == 'edit_auto_prompt':
        p = config.get('auto_answer_prompt', '')
        await event.edit(f"🤖 **Auto-Javob Prompt**:\n`{p}`\n\nCommand: `/set_auto_prompt yangi matn`", buttons=[[Button.inline("🔙", b'menu_main')]])

    elif data == 'check_status':
        await event.answer("🟢 Online", alert=True)

# COMMANDS
@bot_client.on(events.NewMessage(pattern=r'^/set_trigger (.+)'))
async def set_trigger(event):
    if event.sender_id != ADMIN_ID: return
    config = load_config()
    config['activation_trigger'] = event.pattern_match.group(1).strip()
    save_config(config)
    await event.reply(f"✅ Trigger: `{config['activation_trigger']}`")

@bot_client.on(events.NewMessage(pattern=r'^/set_prompt (.+)'))
async def set_prompt_cmd(event):
    if event.sender_id != ADMIN_ID: return
    config = load_config()
    config['system_instruction'] = event.pattern_match.group(1)
    save_config(config)
    await event.reply("✅ Asosiy Prompt saqlandi.")

@bot_client.on(events.NewMessage(pattern=r'^/set_auto_prompt (.+)'))
async def set_auto_prompt_cmd(event):
    if event.sender_id != ADMIN_ID: return
    config = load_config()
    config['auto_answer_prompt'] = event.pattern_match.group(1)
    save_config(config)
    await event.reply("✅ Auto-Javob Prompt saqlandi.")

# =========================================
# USERBOT CORE
# =========================================

# 1. MANUAL TRIGGER (Asosiy Prompt)
@user_client.on(events.NewMessage(outgoing=True))
async def manual_trigger_handler(event):
    config = load_config()
    trigger = config.get('activation_trigger', '.')
    if not event.text.startswith(trigger): return
    query = event.text[len(trigger):].strip()
    if not query: return
    await event.edit("🧠...")
    answer = await ask_ai_universal(query)
    await event.edit(answer)


# 2. INCOMING TRIGGER (Asosiy Prompt)
@user_client.on(events.NewMessage(incoming=True))
async def incoming_trigger_handler(event):
    if not event.is_private: return
    config = load_config()
    trigger = config.get('activation_trigger', '.')
    
    if event.text.startswith(trigger):
        query = event.text[len(trigger):].strip()
        if not query: return
        sender = await event.get_sender()
        if sender and sender.bot: return

        async with user_client.action(event.chat_id, 'typing'):
            answer = await ask_ai_universal(query)
        
        sig = get_signature(config.get('current_model'))
        await event.reply(f"{answer}\n{sig}")


# 3. AUTO-ANSWER (Auto Prompt!!!)
@user_client.on(events.NewMessage(incoming=True))
async def auto_answer_handler(event):
    if not event.is_private: return
    if event.text.startswith('/'): return
    config = load_config()
    trigger = config.get('activation_trigger', '.')
    if event.text.startswith(trigger): return
    if not config.get('auto_answer_enabled'): return
    
    sender = await event.get_sender()
    if sender and sender.bot: return
    me = await user_client.get_me()
    if event.sender_id == me.id: return

    await asyncio.sleep(4)
    async with user_client.action(event.chat_id, 'typing'):
        custom_p = config.get('auto_answer_prompt', config.get('system_instruction'))
        answer = await ask_ai_universal(event.text, custom_prompt=custom_p)
    
    sig = get_signature(config.get('current_model'))
    await event.reply(f"{answer}\n{sig}")


# UTILS
def get_weather():
    config = load_config()
    city_name = config.get('user_city', 'Andijan')
    try:
        lat, lon = get_coords(city_name)
        if not lat: lat, lon = 40.7821, 72.3442
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Asia/Tashkent"
        r = requests.get(url, timeout=3).json()
        t = round(r['current_weather']['temperature'])
        c = r['current_weather']['weathercode']
        e = "☀️" if c == 0 else "⛅" if c < 4 else "🌧" if c < 60 else "❄️"
        return f"{e} {t:+d}°C"
    except: return ""

async def update_bio():
    while True:
        try:
            tz = pytz.timezone(TIMEZONE)
            now = datetime.now(tz)
            time = now.strftime('%H:%M')
            config = load_config()
            city = config.get('user_city', 'Andijan')
            trig = config.get('activation_trigger', '.')
            w = get_weather()
            
            # Emojilar qaytarildi
            bio = f"✨ {time} | 📍 {city}"
            if w: bio += f" | {w}"
            bio += f" | 🧠 AI: {trig}savol"

            await user_client(UpdateProfileRequest(about=bio))
            await asyncio.sleep(UPDATE_INTERVAL)
        except: await asyncio.sleep(20)

async def main():
    print("🚀 Running...")
    await user_client.start(phone=PHONE)
    await bot_client.start(bot_token=BOT_TOKEN)
    
    # Faqat ADMINGA xabar (Saved Messages ga emas)
    try:
        await bot_client.send_message(ADMIN_ID, "🚀 **Userbot muvaffaqiyatli ishga tushdi!**")
    except: pass
    
    print("✅ OK")
    asyncio.create_task(update_bio())
    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())

if __name__ == '__main__':
    asyncio.run(main())
