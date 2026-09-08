"""Tezkor komandalar (chiquvchi xabarda) va e'lon-qidiruv yadrosi."""
import re
import asyncio

from config import load_config
from clients import user_client
from ai import ask_ai_universal
from helpers import bot_send, build_msg_link, parse_delay

# Tezkor komandalar uchun promptlar
QUICK_PROMPTS = {
    'tarjima': (
        "Quyidagi matnni tarjima qil. Agar matn o'zbekcha bo'lsa inglizchaga, "
        "aks holda o'zbekchaga tarjima qil. Faqat tarjimani yoz, boshqa izoh berma:"
    ),
    'qisqartir': "Quyidagi matnni qisqa va aniq xulosa qilib ber (o'zbek tilida):",
    'tahrirla': (
        "Quyidagi matnning imlo va uslubini to'g'rilab, chiroyli qilib qayta yoz. "
        "Til o'zgarmasin. Faqat tahrirlangan matnni yoz:"
    ),
}


async def cmd_quick(event, kind, text):
    """Tarjima / qisqartirish / tahrirlash."""
    if not text:
        trigger = load_config().get('activation_trigger', '.')
        await event.edit(f"❌ Matn yo'q. Masalan: `{trigger}{kind} matn...`")
        return
    await event.edit("🧠...")
    answer = await ask_ai_universal(text, custom_prompt=QUICK_PROMPTS[kind])
    await bot_send(event, answer, edit=True)


async def cmd_remind(event, arg):
    """Eslatma: `.eslat 18:00 matn` yoki `.eslat 10m matn`."""
    parts = arg.split(maxsplit=1)
    if len(parts) < 2:
        await event.edit("❌ Format: `.eslat 18:00 matn`  yoki  `.eslat 10m matn`")
        return
    when, msg = parts
    delay = parse_delay(when)
    if delay is None:
        await event.edit("❌ Vaqtni tushunmadim. Masalan: `18:00`, `10m`, `2h`, `30s`")
        return
    chat_id = event.chat_id
    await event.edit(f"⏰ Eslatma o'rnatildi ({when}): {msg}")

    async def _remind():
        await asyncio.sleep(delay)
        try:
            await user_client.send_message(chat_id, f"⏰ **Eslatma:** {msg}")
        except Exception:
            pass

    asyncio.create_task(_remind())


# =========================================================
# E'LON QIDIRUV YADROSI (bot va userbot ikkalasi ishlatadi)
# =========================================================
async def search_listings(query, targets, scan=None):
    """Berilgan kanal(lar)dan e'lonlarni o'qib, AI bilan so'rovga moslarini topadi.
    `scan` — har kanaldan o'qiladigan oxirgi xabarlar soni (None bo'lsa config'dan yoki 80).
    Natija — tayyor matn (havolalar bilan) yoki xato/izoh matni."""
    config = load_config()
    if scan is None:
        scan = config.get('search_scan_limit', 80)
    scan = max(10, min(int(scan), 1000))
    cap = min(max(scan, 120), 400)  # AI'ga yuboriladigan e'lonlar umumiy chegarasi

    collected = []
    for t in targets:
        try:
            async for msg in user_client.iter_messages(t, limit=scan):
                if msg.text:
                    snippet = msg.text[:220].replace('\n', ' ')
                    collected.append((snippet, build_msg_link(msg)))
                if len(collected) >= cap:
                    break
        except Exception:
            continue

    if not collected:
        return "❌ E'lon topilmadi. Kanalga a'zo emasligingiz yoki xabar yo'qligi mumkin."

    listing = "".join(f"[{i}] {txt}\n" for i, (txt, _l) in enumerate(collected))
    filter_prompt = (
        "Sen e'lonlardan foydalanuvchi so'roviga mos keladiganlarini tanlaysan. "
        "Javobda FAQAT mos e'lonlarning raqamlarini vergul bilan yoz (masalan: 2,5,7). "
        "Mos kelmasa 'yoq' deb yoz. Boshqa hech narsa qo'shma."
    )
    raw = await ask_ai_universal(f"So'rov: {query}\n\nE'lonlar:\n{listing}", custom_prompt=filter_prompt)

    idxs = [int(x) for x in re.findall(r'\d+', raw or '')]
    idxs = [i for i in idxs if 0 <= i < len(collected)][:8]
    if not idxs:
        return f"😕 '{query}' bo'yicha mos e'lon topilmadi."

    out = f"🔎 **'{query}'** bo'yicha {len(idxs)} ta mos e'lon:\n\n"
    for n, i in enumerate(idxs, 1):
        txt, link = collected[i]
        out += f"**{n}.** {txt}"
        if link:
            out += f"\n🔗 {link}"
        out += "\n\n"
    return out


async def cmd_search(event, query):
    """Userbot (guruh ichida) `.qidir [son] <so'rov>` — joriy guruh yoki shop ro'yxatida qidirish.
    So'rov oldidan son yozilsa — oxirgi shuncha xabardan qidiradi (masalan `.qidir 200 iphone`)."""
    if not query:
        await event.edit("❌ So'rov yo'q. Masalan: `.qidir 16gb ram laptop`  yoki  `.qidir 200 iphone`")
        return
    scan = None
    m = re.match(r'^(\d+)\s+(.+)', query)
    if m:
        scan = int(m.group(1))
        query = m.group(2)
    config = load_config()
    targets = [event.chat_id] if not event.is_private else config.get('shop_channels', [])
    if not targets:
        await event.edit("❌ Kanal yo'q. Botga kanaldan e'lon **forward** qiling yoki guruh ichida ishlating.")
        return
    scan_txt = f" (oxirgi {scan} ta)" if scan else ""
    await event.edit(f"🔎 Qidirilyapti{scan_txt}...")
    result = await search_listings(query, targets, scan)
    await bot_send(event, result, edit=True)
