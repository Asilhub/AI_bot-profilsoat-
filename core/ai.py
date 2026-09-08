"""AI dvigatel: matn (Groq/Gemini), rasm (Gemini vision), ovoz (Groq Whisper)."""
import asyncio

from config import GEMINI_API_KEY, load_config, log
from clients import groq_client, genai


async def ask_ai_universal(question, custom_prompt=None, history=None):
    """Matnli savolga javob (Groq Llama/Gemma yoki Gemini)."""
    config = load_config()
    model_name = config.get('current_model', 'llama-3.1-8b-instant')
    sys_instruction = custom_prompt if custom_prompt else config.get('system_instruction', '')
    history = history or []

    try:
        # --- GROQ (Llama / Mixtral / Gemma) ---
        if any(k in model_name for k in ('llama', 'mixtral', 'gemma')):
            if not groq_client:
                return "❌ Groq API error"
            messages = [{"role": "system", "content": sys_instruction}]
            messages += history
            messages.append({"role": "user", "content": question})

            def _call():
                return groq_client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    temperature=0.7,
                    max_tokens=1024,
                )

            completion = await asyncio.to_thread(_call)
            return completion.choices[0].message.content

        # --- GEMINI ---
        else:
            if not GEMINI_API_KEY:
                return "❌ Gemini API error"
            model = genai.GenerativeModel(model_name)
            hist_txt = ""
            for m in history:
                who = "User" if m["role"] == "user" else "Assistant"
                hist_txt += f"{who}: {m['content']}\n"
            full_prompt = f"{sys_instruction}\n\n{hist_txt}User: {question}"
            response = await model.generate_content_async(full_prompt)
            return response.text if response else "..."

    except Exception as e:
        return f"❌ Error: {str(e)[:80]}"


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
        return f"❌ Rasm xato: {str(e)[:80]}"


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
