# 🤖 AIBOT - Telegram AI Assistant

Bu **Telegram Userbot** (foydalanuvchi boti) bo'lib, u @yozuras-ga kelgan xabarlarga avtomatik javob berish, sun'iy intellekt (Gemini, Llama) yordamida suhbatlashish va profilni boshqarish (Bio-ni yangilab turish) imkoniyatlariga ega.

## ✨ Imkoniyatlari

*   **🧠 Sun'iy Intellekt:** Google Gemini va Groq (Llama 3, Mixtral) modellaridan foydalanadi.
*   **🗣 Avto-Javob:** Siz band vaqtingizda kelgan xabarlarga "aqlli" javob qaytaradi.
*   **🛠 Admin Panel:** Telegram ichidan turib botni boshqarish (Modelni o'zgartirish, Trigger, Shahar va boshqalar).
*   **📍 Bio Yangilanishi:** Profilingizdagi "Bio" qismini soat, sana, ob-havo va AI holati bilan avtomatik yangilab turadi.
*   **🔐 Xavfsiz:** API kalitlari va maxfiy ma'lumotlar `.env` faylida saqlanadi.

## 🚀 O'rnatish

Loyihani kompyuteringizga o'rnatish uchun quyidagi qadamlarni bajaring:

### 1. Loyihani yuklab oling
```bash
git clone https://github.com/Asilhub/AI_bot-profilsoat-.git
cd AI_bot-profilsoat-
```

### 2. Kerakli kutubxonalarni o'rnating
Python o'rnatilganligiga ishonch hosil qiling, so'ngra:
```bash
pip install -r requirements.txt
```

### 3. Sozlamalarni kiriting
`.env.example` faylidan nusxa olib, yangi `.env` fayl yarating va ichiga o'z ma'lumotlaringizni kiriting:

**Linux/Mac:**
```bash
cp .env.example .env
nano .env
```

**Windows:**
`.env.example` fayl nomini `.env` ga o'zgartiring va ichini tahrirlang.

**To'ldirilishi kerak bo'lgan ma'lumotlar (`.env`):**
*   `API_ID` va `API_HASH`: [my.telegram.org](https://my.telegram.org) saytidan oling.
*   `PHONE`: Telefon raqamingiz (masalan, +998901234567).
*   `BOT_TOKEN`: [@BotFather](https://t.me/BotFather) dan olingan bot tokeni (Admin panel uchun).
*   `ADMIN_ID`: O'zingizning Telegram ID raqamingiz.
*   `GEMINI_API_KEY`: [Google AI Studio](https://aistudio.google.com/) dan oling.
*   `GROQ_API_KEY`: (Ixtiyoriy) [Groq Console](https://console.groq.com/) dan oling.

### 4. Botni ishga tushiring
```bash
python userbot.py
```

Birinchi marta ishga tushirganda, Telegram tasdiqlash kodini kiritishingiz so'raladi.

## 🎮 Ishlatish

*   **Avtomatik Javob:** Sozlamalarda yoqilgan bo'lsa, lichkaga yozganlarga avtomatik javob beradi.
*   **AI bilan suhbat:** `.` (nuqta) bilan boshlangan xabarlar AI ga yuboriladi. Masalan: `.Salom, qalaysan?`
*   **Admin Panel:** O'zingiz yaratgan botga (BOT_TOKEN dagi botga) `/start` buyrug'ini yuboring.

## 🤝 Hissa qo'shish (Contributing)
Xatoliklarni topsangiz yoki yangi g'oyalar bo'lsa, **Pull Request** yuborishingiz yoki **Issues** bo'limida yozib qoldirishingiz mumkin.

## 📄 Litsenziya
Bu loyiha ochiq manba hisoblanadi.
