import telebot
from telebot import types
import sqlite3

# --- 1. SOZLAMALAR ---
TOKEN = "8855626110:AAFUiBL8EEqF17QFV2MkABbyBJ6OVVBtvEQ"
ADMIN_ID = 7042304810  # O'zingizning Telegram ID raqamingizni yozing (cheklar sizga boradi)
KARTA_RAQAM = "5614681875659595"  # Pul tushadigan karta raqamingiz
XIZMAT_NARXI = "10 000 so'm"

bot = telebot.TeleBot(TOKEN)

# --- 2. MA'LUMOTLAR BAZASINI YARATISH ---
def baza_yarat():
    conn = sqlite3.connect('tanishuv_baza.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foydalanuvchilar (
            id INTEGER PRIMARY KEY,
            ismi TEXT,
            yoshi INTEGER,
            hudud TEXT,
            jinsi TEXT,
             premium INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

baza_yarat()

# --- 3. BOT LOGIKASI (FUNKSIYALAR) ---

# /start bosilganda
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    
    # Bazada bormi-yo'qligini tekshirish
    conn = sqlite3.connect('tanishuv_baza.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foydalanuvchilar WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Agar ro'yxatdan o'tgan bo'lsa, asosiy menyu
        menyu_yubor(user_id)
    else:
        # Agar yangi bo'lsa, ro'yxatga olishni boshlash
        bot.send_message(user_id, "🌟 Tanishuv botimizga xush kelibsiz!\nRo'yxatdan o'tish uchun ismingizni kiriting:")
        bot.register_next_step_handler(message, ism_ol)

# Ro'yxatdan o'tish bosqichlari
def ism_ol(message):
    user_id = message.chat.id
    ismi = message.text
    bot.send_message(user_id, f"Rahmat, {ismi}. Endi yoshingizni kiriting (Faqat raqamda):")
    bot.register_next_step_handler(message, yosh_ol, ismi)

def yosh_ol(message, ismi):
    user_id = message.chat.id
    try:
        yoshi = int(message.text)
        bot.send_message(user_id, "Yashash hududingizni kiriting (Masalan: Xorazm, Toshkent...):")
        bot.register_next_step_handler(message, hudud_ol, ismi, yoshi)
    except ValueError:
        bot.send_message(user_id, "Iltimos, yoshingizni faqat raqamda kiriting:")
        bot.register_next_step_handler(message, yosh_ol, ismi)

def hudud_ol(message, ismi, yoshi):
    user_id = message.chat.id
    hudud = message.text
    
    # Jinsini tanlash uchun tugma
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Yigit 🧑", "Qiz 👧")
    
    bot.send_message(user_id, "Jinsingizni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(message, jins_ol, ismi, yoshi, hudud)

def jins_ol(message, ismi, yoshi, hudud):
    user_id = message.chat.id
    jinsi = message.text
    
    if jinsi not in ["Yigit 🧑", "Qiz 👧"]:
        bot.send_message(user_id, "Iltimos, tugmalardan birini bosing:")
        bot.register_next_step_handler(message, jins_ol, ismi, yoshi, hudud)
        return

    # Bazaga saqlash
    conn = sqlite3.connect('tanishuv_baza.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO foydalanuvchilar (id, ismi, yoshi, hudud, jinsi) VALUES (?, ?, ?, ?, ?)",
                   (user_id, ismi, yoshi, hudud, jinsi))
    conn.commit()
    conn.close()
    
    bot.send_message(user_id, "🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz!")
    menyu_yubor(user_id)

# Asosiy menyu
def menyu_yubor(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Juft qidirish", "👤 Mening profilim")
    bot.send_message(user_id, "Kerakli bo'limni tanlang:", reply_markup=markup)

# Tugmalar bosilganda
@bot.message_handler(func=lambda message: True)
def menyu_bosilganda(message):
    user_id = message.chat.id
    text = message.text
    
    conn = sqlite3.connect('tanishuv_baza.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM foydalanuvchilar WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        bot.send_message(user_id, "Avval ro'yxatdan o'ting. /start bosing.")
        return

    if text == "👤 Mening profilim":
        status = "Premium 💎 (Faol)" if user[5] == 1 else "Oddiy (Qidiruv yopiq)"
        profil_text = f"📋 Sizning profilingiz:\n\n👤 Ism: {user[1]}\n🎂 Yosh: {user[2]}\n📍 Hudud: {user[3]}\n⚧ Jins: {user[4]}\n💳 Holat: {status}"
        bot.send_message(user_id, profil_text)
        
    elif text == "🔍 Juft qidirish":
        if user[5] == 1: # Agar to'lov qilgan bo'lsa (Premium bo'lsa)
            juft_qidirish(message, user)
        else: # To'lov qilmagan bo'lsa
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("✅ To'lov qildim (Chek yuborish)", "⬅️ Orqaga")
            pay_text = (
                f"⚠️ Juft qidirish xizmati pullik!\n\n"
                f"Xizmat narxi: {XIZMAT_NARXI}\n"
                f"To'lov uchun karta: `{KARTA_RAQAM}`\n\n"
                f"Pulni o'tkazib, 'To'lov qildim' tugmasini bosing va chekni yuboring."
            )
            bot.send_message(user_id, pay_text, parse_mode="Markdown", reply_markup=markup)

    elif text == "✅ To'lov qildim (Chek yuborish)":
        bot.send_message(user_id, "Iltimos, to'lov chekining rasmini (skrinshotini) yuboring:")
        bot.register_next_step_handler(message, chek_qabul_qilish)
        
    elif text == "⬅️ Orqaga":
        menyu_yubor(user_id)

# Chekni qabul qilish va Adminga yuborish
def chek_qabul_qilish(message):
    user_id = message.chat.id
    if message.content_type != 'photo':
        bot.send_message(user_id, "Iltimos, faqat rasm (chek) yuboring:")
        bot.register_next_step_handler(message, chek_qabul_qilish)
        return
    
    # Adminga chekni yuborish (Tasdiqlash tugmalari bilan)
    photo_id = message.photo[-1].file_id
    markup = types.InlineKeyboardMarkup()
    btn_xa = types.InlineKeyboardButton("✅ Tasdiqlash (A'zo qilish)", callback_data=f"ok_{user_id}")
    btn_yoq = types.InlineKeyboardButton("❌ Rad etish", callback_data=f"no_{user_id}")
    markup.add(btn_xa, btn_yoq)
    
    bot.send_photo(ADMIN_ID, photo_id, caption=f"🔔 Yangi to'lov!\nFoydalanuvchi ID: {user_id}\nTasdiqlaysizmi?", reply_markup=markup)
    bot.send_message(user_id, "⏳ Chekingiz adminga yuborildi. Tekshirilgandan so'ng qidiruv ochiladi (Odatda 5-10 daqiqa).")

# Admin tugmani bosganda (Inline tugmalar)
@bot.callback_query_handler(func=lambda call: True)
def admin_tasdiqlash(call):
    action, target_id = call.data.split("_")
    target_id = int(target_id)
    
    if action == "ok":
        conn = sqlite3.connect('tanishuv_baza.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE foydalanuvchilar SET premium=1 WHERE id=?", (target_id,))
        conn.commit()
        conn.close()
        
        bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption="✅ To'lov tasdiqlandi va qidiruv ochildi!")
        bot.send_message(target_id, "🎉 Tabriklaymiz! To'lovingiz tasdiqlandi. Endi '🔍 Juft qidirish' tugmasini bosib foydalanishingiz mumkin!")
        
    elif action == "no":
        bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption="❌ To'lov rad etildi.")
        bot.send_message(target_id, "❌ Afsuski, to'lovingiz tasdiqlanmadi. Agar xatolik bo'lsa, adminga murojaat qiling.")

# Juft qidirish algoritmi (MUKAMMAL VA SODDA)
def juft_qidirish(message, user):
    user_id = user[0]
    user_jinsi = user[4]
    user_hudud = user[3]
    
    # O'ziga qarama-qarshi jinsni topish (Yigit bo'lsa Qizni, Qiz bo'lsa Yigitni)
    izlanayotgan_jins = "Qiz 👧" if user_jinsi == "Yigit 🧑" else "Yigit 🧑"
    
    conn = sqlite3.connect('tanishuv_baza.db')
    cursor = conn.cursor()
    # O'sha hududdagi qarama-qarshi jins vakillarini tasodifiy (RANDOM) tartibda chiqarish
    cursor.execute("SELECT * FROM foydalanuvchilar WHERE jinsi=? AND hudud=? AND id!=? ORDER BY RANDOM() LIMIT 1", 
                   (izlanayotgan_jins, user_hudud, user_id))
    juft = cursor.fetchone()
    conn.close()
    
    if juft:
        # Agar mos juft topilsa, uning ma'lumotlarini ko'rsatish (Username yashirin bo'ladi)
        markup = types.InlineKeyboardMarkup()
        btn_aloqa = types.InlineKeyboardButton("💬 Bog'lanish (Telegram)", url=f"tg://user?id={juft[0]}")
        markup.add(btn_aloqa)
        
        juft_text = f"❤️ Sizga mos juft topildi:\n\n👤 Ism: {juft[1]}\n🎂 Yosh: {juft[2]}\n📍 Hudud: {juft[3]}\n\nPastdagi tugma orqali to'g'ridan-to'g'ri unga yozishingiz mumkin 👇"
        bot.send_message(user_id, juft_text, reply_markup=markup)
    else:
        bot.send_message(user_id, "😔 Afsuski, hozircha sizning hududingizdan mos juft topilmadi. Birozdan so'ng qayta urinib ko'ring.")

# Botni yuritish
print("Bot muvaffaqiyatli ishlamoqda...")
bot.polling(none_stop=True)