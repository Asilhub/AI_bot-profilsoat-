# 🤖 AIBOT — Telegram AI Userbot

Telegram akkauntingizga ulanadigan **userbot**: kelgan xabarlarga sun'iy intellekt yordamida javob beradi, profil bio'sini soat/ob-havo bilan yangilab turadi va Telegram ichidagi admin panel orqali boshqariladi.

## ✨ Imkoniyatlari

- **🧠 AI** — Groq (GPT-OSS, Qwen3, Compound) va Google Gemini modellari, panel orqali almashtiriladi
- **🗣 Aqlli avto-javob** — faqat shaxsiy chatlarda, cooldown va qora/oq ro'yxat bilan
- **😴 Away-rejim** — siz yaqinda faol bo'lsangiz bot aralashmaydi
- **🖼 Rasm va 🎤 ovoz** — rasmni tahlil qiladi (Gemini Vision), ovozli xabarni matnga o'giradi (Whisper)
- **⚡ Tezkor komandalar** — `.tarjima`, `.qisqartir`, `.tahrirla`, `.eslat`
- **📍 Bio yangilanishi** — profil bio'sida joriy vaqt, sana va ob-havo (Open-Meteo, kalit talab qilmaydi)
- **🛠 Admin panel** — alohida bot orqali: Model, Shahar, Avto-javob, Away, Xotira, Trigger, Promptlar, Qidirish, Kanallar, Ro'yxatlar, Status
- **🔄 Barqarorlik** — tarmoq uzilsa avtomatik qayta ulanadi

## 🧠 Modellar

Standart model — `openai/gpt-oss-120b` (Groq). Admin paneldan almashtiriladi.

| Model | Izoh |
|---|---|
| `openai/gpt-oss-120b` | standart, eng sifatli o'zbekcha |
| `openai/gpt-oss-20b` | tezroq, yengilroq |
| `qwen/qwen3.8-27b` | eng tez |
| `groq/compound` | internetdan qidira oladi |
| `gemini-2.5-flash` | rasm tahlili uchun ham ishlatiladi |
| `gemini-2.5-flash-lite` | yengil Gemini |

> **Eslatma:** ba'zi xostinglarning IP manzillari Google tomonidan bloklangan
> bo'lishi mumkin — u holda Gemini `403` qaytaradi. Bunday paytda bot avtomatik
> ravishda Groq modeliga o'tadi, faqat rasm tahlili ishlamaydi.

## 📁 Struktura

```
userbot.py              # kirish nuqtasi
core/
├── config.py           # .env, konstantalar, config.json, logging
├── clients.py          # Telegram klientlari + Groq/Gemini
├── state.py            # suhbat xotirasi, avto-javob qoidalari
├── ai.py               # matn / rasm / ovoz uchun AI
├── helpers.py          # imzo, koordinata, vaqt, matn bo'lish
├── bio.py              # bio'ni davriy yangilash
├── commands.py         # tezkor komandalar + kanal qidiruvi
├── handlers_manager.py # admin panel
└── handlers_userbot.py # kiruvchi/chiquvchi xabarlar
```

## 🚀 O'rnatish

**1. Loyihani yuklang**

```bash
git clone https://github.com/Asilhub/AI_bot-profilsoat-.git
cd AI_bot-profilsoat-
```

**2. Virtual muhit va kutubxonalar**

```bash
python -m venv .venv
```

```bash
# Windows
.venv\Scripts\pip install -r requirements.txt
# Linux/Mac
.venv/bin/pip install -r requirements.txt
```

**3. Sozlamalar**

`.env.example` dan nusxa oling va to'ldiring:

```bash
cp .env.example .env
```

| O'zgaruvchi | Qayerdan olinadi |
|---|---|
| `API_ID`, `API_HASH` | [my.telegram.org](https://my.telegram.org) → API development tools |
| `PHONE` | userbot ulanadigan raqam, `+998...` |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) — admin panel boti uchun |
| `ADMIN_ID` | [@userinfobot](https://t.me/userinfobot) beradigan raqam |
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) |

Ixtiyoriy: `TIMEZONE` (default `Asia/Tashkent`), `UPDATE_INTERVAL` (bio yangilanish oralig'i, soniya).

**4. Boshlang'ich konfiguratsiya**

```bash
cp config.example.json config.json
```

Bu fayl ixtiyoriy — bo'lmasa bot standart qiymatlar bilan ishlaydi. Keyinchalik hamma sozlama admin panel orqali o'zgartiriladi va shu faylga yozib boriladi.

**5. Ishga tushirish**

```bash
python userbot.py
```

Birinchi ishga tushirishda Telegram SMS kod so'raydi. Kod kiritilgach `*.session` fayllari yaratiladi va keyingi safar login talab qilinmaydi.

## 🎛 Foydalanish

**Admin panel** — `BOT_TOKEN` bilan yaratgan botingizga `/start` yozing. Barcha sozlamalar shu yerdan boshqariladi.

**Tezkor komandalar** — o'z chatingizda, trigger belgisi bilan (default `.`):

```
.tarjima <matn>     — o'zbekcha ↔ inglizcha tarjima
.qisqartir <matn>   — qisqa xulosa
.tahrirla <matn>    — matnni tahrirlash
.eslat 18:00 matn   — eslatma (yoki .eslat 10m matn)
```

## ⚠️ Xavfsizlik

Quyidagi fayllar `.gitignore` da va **hech qachon commit qilinmasligi kerak**:

- `.env` — barcha API kalitlari
- `*.session` — Telegram sessiyasi, akkauntingizga to'liq kirish huquqini beradi
- `config.json` — shaxsiy promptlar va kanal ro'yxati

## 📄 Litsenziya

MIT — [LICENSE](LICENSE) fayliga qarang.
