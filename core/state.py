"""RAM dagi holat: suhbat xotirasi va avto-javob holati."""
import time

# Har chat uchun suhbat tarixi: {chat_id: [{"role": "user/assistant", "content": "..."}]}
CHAT_HISTORY = {}

# Aqlli avto-javob holati
STATE = {
    'last_activity': 0.0,       # siz oxirgi marta yozgan vaqt (away-rejim uchun)
    'last_reply': {},           # {chat_id: vaqt} — cooldown uchun
    'suppress_activity': False,  # bot o'zi yuborayotganda faollikni hisoblamaslik
}


# --- Suhbat xotirasi ---
def get_history(chat_id, limit):
    return CHAT_HISTORY.get(chat_id, [])[-(limit * 2):]


def add_history(chat_id, role, content, limit):
    h = CHAT_HISTORY.setdefault(chat_id, [])
    h.append({"role": role, "content": content})
    max_len = limit * 2
    if len(h) > max_len:
        del h[:len(h) - max_len]


# --- Aqlli avto-javob qoidalari ---
def should_auto_answer(event, config):
    sid = event.sender_id
    blacklist = config.get('auto_blacklist', [])
    whitelist = config.get('auto_whitelist', [])

    if sid in blacklist:
        return False
    if whitelist and sid not in whitelist:
        return False

    # Away-rejim: siz yaqinda yozgan bo'lsangiz (faolsiz) — javob bermaymiz
    if config.get('away_mode'):
        away_min = config.get('away_after_minutes', 5)
        if time.time() - STATE['last_activity'] < away_min * 60:
            return False

    # Cooldown: bitta chatga tez-tez javob bermaslik (spam himoyasi)
    cooldown = config.get('auto_cooldown', 20)
    last = STATE['last_reply'].get(event.chat_id, 0)
    if time.time() - last < cooldown:
        return False

    return True
