"""Boshqaruv boti (manager_v2): reply-klaviaturali admin panel, kanal qo'shish va qidiruv."""
import re

from telethon import events, Button

from config import ADMIN_ID, load_config, save_config
from clients import bot_client
from state import CHAT_HISTORY
from helpers import chunk_text
from commands import search_listings

# Modellar uchun chiroyli nomlar
FRIENDLY = {
    'openai/gpt-oss-120b': '🚀 GPT-OSS 120B',
    'openai/gpt-oss-20b': '⚡ GPT-OSS 20B',
    'qwen/qwen3.8-27b': '🐧 Qwen3.8 27B',
    'groq/compound': '🔍 Compound (web)',
    'gemini-2.5-flash': '✨ Gemini 2.5 Flash',
    'gemini-2.5-flash-lite': '🪶 Gemini Flash Lite',
}

CITIES = [
    "Tashkent", "Andijan", "Namangan", "Fergana",
    "Samarkand", "Bukhara", "Navoiy", "Jizzakh",
    "Termez", "Urgench", "Nukus", "Qarshi", "Guliston", "Marhamat",
]

# Asosiy menyu tugmalari (matni — moslashtirish uchun barqaror bo'lishi shart)
BTN_MODEL, BTN_CITY = "🧠 Model", "📍 Shahar"
BTN_AUTO, BTN_AWAY, BTN_MEM = "🗣 Avto-javob", "😴 Away", "🧠 Xotira"
BTN_TRIGGER, BTN_PROMPT, BTN_APROMPT = "⚡ Trigger", "📝 Asosiy prompt", "🤖 Auto prompt"
BTN_SEARCH, BTN_CHANNELS = "🔎 Qidirish", "🛒 Kanallar"
BTN_LISTS, BTN_STATUS, BTN_BACK = "📋 Ro'yxatlar", "📡 Status", "🔙 Orqaga"

BASE_BUTTONS = {
    BTN_MODEL, BTN_CITY, BTN_AUTO, BTN_AWAY, BTN_MEM, BTN_TRIGGER, BTN_PROMPT,
    BTN_APROMPT, BTN_SEARCH, BTN_CHANNELS, BTN_LISTS, BTN_STATUS, BTN_BACK,
}

# Admin "🔎 Qidirish" bosgach, keyingi xabar so'rov sifatida qabul qilinadi
PENDING_SEARCH = set()
# So'rov kiritilgach, keyingi xabar "nechta xabardan qidiray?" javobi sifatida kutiladi
# {admin_id: so'rov_matni}
PENDING_COUNT = {}


def b(label):
    return Button.text(label, resize=True)


def main_kb():
    return [
        [b(BTN_MODEL), b(BTN_CITY)],
        [b(BTN_AUTO), b(BTN_AWAY), b(BTN_MEM)],
        [b(BTN_TRIGGER), b(BTN_PROMPT), b(BTN_APROMPT)],
        [b(BTN_SEARCH), b(BTN_CHANNELS)],
        [b(BTN_LISTS), b(BTN_STATUS)],
    ]


def friendly(model):
    return FRIENDLY.get(model, model or "—")


def model_map(config):
    """{chiroyli nom: model_id} — faqat mavjud modellar."""
    return {friendly(m): m for m in config.get('available_models', [])}


def main_text(config):
    is_auto = "✅ ON" if config.get('auto_answer_enabled') else "🔴 OFF"
    away = "✅ ON" if config.get('away_mode') else "🔴 OFF"
    mem = "✅ ON" if config.get('memory_enabled', True) else "🔴 OFF"
    return (
        f"🛠 **Admin Panel**\n\n"
        f"🧠 Model: `{friendly(config.get('current_model'))}`\n"
        f"📍 Shahar: `{config.get('user_city', 'Andijan')}`\n"
        f"⚡ Trigger: `{config.get('activation_trigger', '.')}`\n"
        f"🗣 Avto-javob: {is_auto}\n"
        f"😴 Away: {away}   |   🧠 Xotira: {mem}\n\n"
        f"Pastdagi tugmalardan foydalaning 👇"
    )


def is_known_button(text, config):
    return text in BASE_BUTTONS or text in model_map(config) or text in CITIES


async def show_main_menu(event):
    config = load_config()
    await event.reply(main_text(config), buttons=main_kb())


@bot_client.on(events.NewMessage(pattern='/start'))
async def bot_start(event):
    if event.sender_id != ADMIN_ID:
        return
    PENDING_SEARCH.discard(ADMIN_ID)
    PENDING_COUNT.pop(ADMIN_ID, None)
    await show_main_menu(event)


async def show_models(event, config):
    cur = friendly(config.get('current_model'))
    rows, row = [], []
    for label in model_map(config):
        row.append(b(label))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([b(BTN_BACK)])
    await event.reply(f"🧠 Modelni tanlang (hozir: **{cur}**):", buttons=rows)


async def show_cities(event, config):
    cur = config.get('user_city', 'Andijan')
    rows, row = [], []
    for c in CITIES:
        row.append(b(c))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([b(BTN_BACK)])
    await event.reply(f"📍 Shaharni tanlang (hozir: **{cur}**):", buttons=rows)


async def show_channels(event, config):
    shops = config.get('shop_channels', [])
    if shops:
        lst = "\n".join(f"• `{c}`" for c in shops)
        txt = (
            f"🛒 **Qidiriladigan kanallar ({len(shops)}):**\n{lst}\n\n"
            f"➕ Yana qo'shish: kerakli kanaldagi e'londan istalganini shu botga **forward** qiling.\n"
            f"🗑 Tozalash: `/shop_clear`"
        )
    else:
        txt = (
            "🛒 **Kanallar ro'yxati bo'sh.**\n\n"
            "➕ Qo'shish uchun: qidirmoqchi bo'lgan kanaldagi istalgan e'lonni shu botga **forward** qiling — "
            "men uni ro'yxatga qo'shaman.\n\n"
            "_Eslatma: o'sha kanalga a'zo bo'lishingiz kerak._"
        )
    await event.reply(txt, buttons=main_kb())


async def show_lists(event, config):
    wl = config.get('auto_whitelist', [])
    bl = config.get('auto_blacklist', [])
    away_min = config.get('away_after_minutes', 5)
    cooldown = config.get('auto_cooldown', 20)
    empty = "bo'sh"
    txt = (
        f"📋 **Auto-javob ro'yxatlari**\n\n"
        f"✅ Whitelist (faqat shularga): `{wl or empty}`\n"
        f"⛔ Blacklist (hech qachon): `{bl or empty}`\n\n"
        f"😴 Away kutish: `{away_min} daq`  |  ⏱ Cooldown: `{cooldown} s`\n\n"
        f"**Komandalar:**\n"
        f"`/auto_allow <id>`  •  `/auto_block <id>`\n"
        f"`/auto_unblock <id>`  •  `/auto_clear`\n"
        f"`/set_away_min <daq>`  •  `/forget`"
    )
    await event.reply(txt, buttons=main_kb())


async def run_search(event, query, scan=None):
    config = load_config()
    targets = config.get('shop_channels', [])
    if not targets:
        await event.reply(
            "🛒 Hali kanal qo'shilmagan.\n\nKanaldan istalgan e'lonni shu botga **forward** qiling.",
            buttons=main_kb(),
        )
        return
    scan_txt = f" (oxirgi {scan} ta xabardan)" if scan else ""
    msg = await event.reply(f"🔎 Qidirilyapti{scan_txt}...")
    result = await search_listings(query, targets, scan)
    parts = chunk_text(result)
    try:
        await msg.edit(parts[0])
    except Exception:
        await event.reply(parts[0])
    for p in parts[1:]:
        await event.reply(p)


# =========================================================
# Kanaldan forward qilinsa — ro'yxatga qo'shish
# =========================================================
@bot_client.on(events.NewMessage(func=lambda e: e.is_private and e.forward))
async def add_channel_via_forward(event):
    if event.sender_id != ADMIN_ID:
        return
    fwd = event.forward
    cid = getattr(fwd, 'chat_id', None)
    chat = getattr(fwd, 'chat', None)
    title = getattr(chat, 'title', None)

    if not cid or not title:
        await event.reply("❌ Bu forward kanaldan emas. Kanaldagi e'londan forward qiling.", buttons=main_kb())
        return

    config = load_config()
    shops = config.get('shop_channels', [])
    if cid in shops:
        await event.reply(f"ℹ️ **{title}** allaqachon ro'yxatda.", buttons=main_kb())
        return
    shops.append(cid)
    config['shop_channels'] = shops
    save_config(config)
    await event.reply(
        f"✅ Kanal qo'shildi: **{title}**\nJami: {len(shops)} ta.\n\n"
        f"Endi 🔎 **Qidirish** tugmasi yoki `/qidir <so'rov>` bilan izlang.",
        buttons=main_kb(),
    )


# =========================================================
# Asosiy panel handleri (reply tugmalar)
# =========================================================
@bot_client.on(events.NewMessage(incoming=True))
async def panel_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    if event.forward:
        return  # forward handleri ishlaydi
    text = (event.raw_text or "").strip()
    if not text or text.startswith('/'):
        return  # komandalar alohida handlerlarda

    config = load_config()

    # 2-bosqich: so'rov kiritilgan, endi "nechta xabar?" javobini kutamiz
    if ADMIN_ID in PENDING_COUNT and not is_known_button(text, config):
        query = PENDING_COUNT.pop(ADMIN_ID)
        digits = re.findall(r'\d+', text)
        scan = int(digits[0]) if digits else config.get('search_scan_limit', 80)
        await run_search(event, query, scan)
        return

    # 1-bosqich: 🔎 bosilgan, so'rov kiritildi — endi son so'raymiz
    if ADMIN_ID in PENDING_SEARCH and not is_known_button(text, config):
        PENDING_SEARCH.discard(ADMIN_ID)
        PENDING_COUNT[ADMIN_ID] = text
        await event.reply(
            "🔢 Oxirgi nechta xabardan qidiray?\n"
            "Masalan: `100`  (bo'sh/raqamsiz yozsangiz — 80 tadan).\n"
            "_Eng ko'pi: 1000._"
        )
        return

    # Tugma bosilsa — kutilayotgan qidiruv holatlarini bekor qilamiz
    PENDING_SEARCH.discard(ADMIN_ID)
    PENDING_COUNT.pop(ADMIN_ID, None)

    # --- Asosiy / orqaga ---
    if text == BTN_BACK:
        await show_main_menu(event)

    # --- Submenyular ---
    elif text == BTN_MODEL:
        await show_models(event, config)
    elif text == BTN_CITY:
        await show_cities(event, config)

    # --- Togglelar ---
    elif text == BTN_AUTO:
        config['auto_answer_enabled'] = not config.get('auto_answer_enabled')
        save_config(config)
        await show_main_menu(event)
    elif text == BTN_AWAY:
        config['away_mode'] = not config.get('away_mode')
        save_config(config)
        await show_main_menu(event)
    elif text == BTN_MEM:
        config['memory_enabled'] = not config.get('memory_enabled', True)
        save_config(config)
        await show_main_menu(event)

    # --- Sozlamalar (matn kiritish komandalar orqali) ---
    elif text == BTN_TRIGGER:
        await event.reply(
            f"⚡ Hozirgi trigger: `{config.get('activation_trigger', '.')}`\n"
            f"O'zgartirish: `/set_trigger .`"
        )
    elif text == BTN_PROMPT:
        empty = "(bo'sh)"
        await event.reply(
            f"📝 **Asosiy prompt:**\n{config.get('system_instruction') or empty}\n\n"
            f"O'zgartirish: `/set_prompt yangi matn`"
        )
    elif text == BTN_APROMPT:
        empty = "(bo'sh)"
        await event.reply(
            f"🤖 **Auto-javob prompti:**\n{config.get('auto_answer_prompt') or empty}\n\n"
            f"O'zgartirish: `/set_auto_prompt yangi matn`"
        )

    # --- Qidiruv / kanallar / ro'yxatlar / status ---
    elif text == BTN_SEARCH:
        PENDING_SEARCH.add(ADMIN_ID)
        await event.reply("🔎 Nimani qidiray? Yozing.\nMasalan: `16gb ram noutbuk`  yoki  `arzon iphone`")
    elif text == BTN_CHANNELS:
        await show_channels(event, config)
    elif text == BTN_LISTS:
        await show_lists(event, config)
    elif text == BTN_STATUS:
        chats = len(CHAT_HISTORY)
        await event.reply(f"🟢 Online | Xotirada {chats} ta suhbat")

    # --- Submenyu tanlovlari ---
    elif text in model_map(config):
        config['current_model'] = model_map(config)[text]
        save_config(config)
        await show_main_menu(event)
    elif text in CITIES:
        config['user_city'] = text
        save_config(config)
        await show_main_menu(event)
    # boshqa oddiy matnga javob bermaymiz


# =========================================================
# Qidiruv komandasi
# =========================================================
@bot_client.on(events.NewMessage(pattern=r'^/qidir (.+)'))
async def qidir_cmd(event):
    """`/qidir <so'rov>` yoki `/qidir <son> <so'rov>` (oxirgi <son> ta xabardan)."""
    if event.sender_id != ADMIN_ID:
        return
    PENDING_SEARCH.discard(ADMIN_ID)
    PENDING_COUNT.pop(ADMIN_ID, None)
    arg = event.pattern_match.group(1).strip()
    scan = None
    m = re.match(r'^(\d+)\s+(.+)', arg)
    if m:
        scan = int(m.group(1))
        arg = m.group(2)
    await run_search(event, arg, scan)


# =========================================================
# Matn kiritish / sozlama komandalari
# =========================================================
@bot_client.on(events.NewMessage(pattern=r'^/set_trigger (.+)'))
async def set_trigger(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    config['activation_trigger'] = event.pattern_match.group(1).strip()
    save_config(config)
    await event.reply(f"✅ Trigger: `{config['activation_trigger']}`", buttons=main_kb())


@bot_client.on(events.NewMessage(pattern=r'^/set_prompt (.+)'))
async def set_prompt_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    config['system_instruction'] = event.pattern_match.group(1)
    save_config(config)
    await event.reply("✅ Asosiy prompt saqlandi.", buttons=main_kb())


@bot_client.on(events.NewMessage(pattern=r'^/set_auto_prompt (.+)'))
async def set_auto_prompt_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    config['auto_answer_prompt'] = event.pattern_match.group(1)
    save_config(config)
    await event.reply("✅ Auto-javob prompti saqlandi.", buttons=main_kb())


@bot_client.on(events.NewMessage(pattern=r'^/auto_allow (\d+)'))
async def auto_allow_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    uid = int(event.pattern_match.group(1))
    wl = config.get('auto_whitelist', [])
    if uid not in wl:
        wl.append(uid)
    config['auto_whitelist'] = wl
    save_config(config)
    await event.reply(f"✅ Whitelistga qo'shildi: `{uid}`")


@bot_client.on(events.NewMessage(pattern=r'^/auto_block (\d+)'))
async def auto_block_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    uid = int(event.pattern_match.group(1))
    bl = config.get('auto_blacklist', [])
    if uid not in bl:
        bl.append(uid)
    config['auto_blacklist'] = bl
    save_config(config)
    await event.reply(f"⛔ Blacklistga qo'shildi: `{uid}`")


@bot_client.on(events.NewMessage(pattern=r'^/auto_unblock (\d+)'))
async def auto_unblock_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    uid = int(event.pattern_match.group(1))
    config['auto_blacklist'] = [x for x in config.get('auto_blacklist', []) if x != uid]
    save_config(config)
    await event.reply(f"✅ Blacklistdan olib tashlandi: `{uid}`")


@bot_client.on(events.NewMessage(pattern=r'^/auto_clear$'))
async def auto_clear_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    config['auto_whitelist'] = []
    config['auto_blacklist'] = []
    save_config(config)
    await event.reply("✅ Auto ro'yxatlar tozalandi.")


@bot_client.on(events.NewMessage(pattern=r'^/set_away_min (\d+)'))
async def set_away_min_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    config['away_after_minutes'] = int(event.pattern_match.group(1))
    save_config(config)
    await event.reply(f"✅ Away kutish vaqti: `{config['away_after_minutes']} daqiqa`")


@bot_client.on(events.NewMessage(pattern=r'^/forget$'))
async def forget_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    CHAT_HISTORY.clear()
    await event.reply("🧹 Suhbat xotirasi tozalandi.")


@bot_client.on(events.NewMessage(pattern=r'^/shop_clear$'))
async def shop_clear_cmd(event):
    if event.sender_id != ADMIN_ID:
        return
    config = load_config()
    config['shop_channels'] = []
    save_config(config)
    await event.reply("✅ Kanallar ro'yxati tozalandi.", buttons=main_kb())
