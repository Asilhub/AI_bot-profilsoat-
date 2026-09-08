"""AI dvigatel: matn (Groq/Gemini), rasm (Gemini vision), ovoz (Groq Whisper)."""
import asyncio

from config import GEMINI_API_KEY, load_config, log
from clients import groq_client, genai


# Groq'da Llama/Gemma modellari bekor qilindi — hozirgi ishonchli standart
DEFAULT_MODEL = 'openai/gpt-oss-120b'


def _is_gemini(model_name):
    """Model Gemini'niki bo'lsa True. Qolgan hamma model Groq orqali ketadi."""
    return model_name.startswith('gemini')


async def _ask_groq(model_name, messages):
    kwargs = {
        "messages": messages,
        "model": model_name,
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    # gpt-oss — "o'ylaydigan" model. Effort pasaytirilmasa token budjetini
    # fikrlashga sarflab, bo'sh javob qaytarishi mumkin.
    if model_name.startswith('openai/gpt-oss'):
        kwargs["reasoning_effort"] = "low"

    def _call():
        return groq_client.chat.completions.create(**kwargs)

    completion = await asyncio.to_thread(_call)
    return (completion.choices[0].message.content or "").strip()


async def _ask_gemini(model_name, sys_instruction, history, question):
    model = genai.GenerativeModel(model_name)
    hist_txt = ""
    for m in history:
        who = "User" if m["role"] == "user" else "Assistant"
        hist_txt += f"{who}: {m['content']}\n"
    full_prompt = f"{sys_instruction}\n\n{hist_txt}User: {question}"
    response = await model.generate_content_async(full_prompt)
    return response.text if response else "..."


async def ask_ai_universal(question, custom_prompt=None, history=None):
    """Matnli savolga javob. Gemini ishlamasa — avtomatik Groq'ga o'tadi."""
    config = load_config()
    model_name = config.get('current_model') or DEFAULT_MODEL
    sys_instruction = custom_prompt if custom_prompt else config.get('system_instruction', '')
    history = history or []

    messages = [{"role": "system", "content": sys_instruction}]
    messages += history
    messages.append({"role": "user", "content": question})

    if _is_gemini(model_name):
        if GEMINI_API_KEY:
            try:
                return await _ask_gemini(model_name, sys_instruction, history, question)
            except Exception as e:
                # Xosting IP'si Google tomonidan bloklangan bo'lishi mumkin (403).
                # Foydalanuvchini javobsiz qoldirmaslik uchun Groq bilan davom etamiz.
                log.warning("Gemini ishlamadi (%s: %s) — Groq'ga o'tyapman",
                            type(e).__name__, str(e)[:120])
        if not groq_client:
            return "❌ Gemini ishlamadi, Groq kaliti esa yo'q"
        model_name = DEFAULT_MODEL

    if not groq_client:
        return "❌ GROQ_API_KEY ko'rsatilmagan (.env fayliga qarang)"

    try:
        answer = await _ask_groq(model_name, messages)
        if answer:
            return answer
        log.warning("Groq bo'sh javob qaytardi (%s)", model_name)
        return "🤔 Javob chiqmadi, qaytadan urinib ko'ring."
    except Exception as e:
        log.warning("Groq xato (%s): %s", model_name, str(e)[:200])
        return f"❌ Xato: {type(e).__name__}: {str(e)[:150]}"


async def ask_ai_vision(image_bytes, question, custom_prompt=None):
    """Rasmni Gemini vision bilan tahlil qilish."""
    if not GEMINI_API_KEY:
        return "❌ Rasm tahlili uchun Gemini API kerak"
    config = load_config()
    sys_instruction = custom_prompt if custom_prompt else config.get('system_instruction', '')
    vision_model = config.get('vision_model', 'gemini-2.5-flash')
    try:
        model = genai.GenerativeModel(vision_model)
        q = question or "Bu rasmda nima borligini tushuntir."
        prompt = f"{sys_instruction}\n\nUser: {q}"
        response = await model.generate_content_async(
            [prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
        )
        return response.text if response else "..."
    except Exception as e:
        log.warning("Vision xato (%s): %s", type(e).__name__, str(e)[:200])
        return ("❌ Rasm tahlili ishlamadi — Gemini API'ga ulanib bo'lmadi "
                "(xosting IP'si bloklangan bo'lishi mumkin).")


async def transcribe_voice(audio_bytes):
    """Ovozli xabarni Groq Whisper bilan matnga aylantirish."""
    if not groq_client:
        return None
    config = load_config()
    whisper_model = config.get('whisper_model', 'whisper-large-v3')
    lang = config.get('whisper_language', 'uz')  # '' bo'lsa avto-aniqlash
    try:
        def _call():
            kwargs = {"file": ("voice.ogg", audio_bytes), "model": whisper_model}
            if lang:
                kwargs["language"] = lang
            return groq_client.audio.transcriptions.create(**kwargs)
        result = await asyncio.to_thread(_call)
        return (result.text or "").strip()
    except Exception as e:
        log.warning("Whisper xato: %s: %s", type(e).__name__, str(e)[:150])
        return None
