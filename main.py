import os
import asyncio
import logging
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "8582520793:AAEJw65DPp780yky_wZHlKFyIQJNkJ3GowM"
BOT_USERNAME = "AirmaxMobileBot" 

# Super Admin va Adminlar
SUPER_ADMIN_ID = 6738533029  
ADMIN_IDS = [6738533029, 5156453500]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA SOZLAMALARI ---
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, memory TEXT, battery TEXT, color TEXT, 
            condition TEXT, price TEXT, quantity INTEGER, photo TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'points' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    if 'referred_by' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, phone_id INTEGER, quantity INTEGER DEFAULT 1)''')
            
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_phone', '+998900000000')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel', 'none')")
    conn.commit()
    conn.close()

init_db()

def get_setting(key):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def update_setting(key, value):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    conn.commit()
    conn.close()

# --- HOLATLAR (States) ---
class AddPhone(StatesGroup):
    category, name, memory, battery, color, condition, price, quantity, photo, confirm = State(), State(), State(), State(), State(), State(), State(), State(), State(), State()
class BroadcastNews(StatesGroup): content = State()
class SearchState(StatesGroup): query = State()
class CheckoutState(StatesGroup): phone_number = State()
class SettingsState(StatesGroup): channel = State(); phone = State()

# --- MENYULAR ---
def get_main_menu(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 iPhone")
    builder.button(text="📱 Samsung")
    builder.button(text="📱 HONOR")
    builder.button(text="📱 Redmi")
    builder.button(text="🎧 Aksessuarlar")
    builder.button(text="🔍 Qidiruv")
    builder.button(text="🛒 Savat")
    builder.button(text="🎁 Referal (Bonus)")
    builder.button(text="📞 Operator")
    
    if user_id in ADMIN_IDS:
        builder.button(text="➕ Yangi telefon")
        builder.button(text="📊 Statistika")
    if user_id == SUPER_ADMIN_ID:
        builder.button(text="👑 Super Admin Panel")
        
    builder.adjust(2, 2, 2, 2, 1, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_super_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="⚙️ Kanal sozlamalari")
    builder.button(text="📞 Aloqa raqamini o'zgartirish")
    builder.button(text="📢 Yangilik yuborish")
    builder.button(text="🗑 Barcha mahsulotni tozalash")
    builder.button(text="🔙 Bosh menyu")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_menu():
    return ReplyKeyboardBuilder().button(text="❌ Bekor qilish").as_markup(resize_keyboard=True)

# --- UMUMIY BEKOR QILISH VA ORQAGA ---
@dp.message(F.text == "❌ Bekor qilish", StateFilter('*'))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == SUPER_ADMIN_ID:
        await message.answer("❌ Amal bekor qilindi.", reply_markup=get_super_admin_menu())
    else:
        await message.answer("❌ Amal bekor qilindi va bosh menyuga qaytdingiz.", reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text.in_(["🔙 Bosh menyu", "⬅️ Orqaga"]))
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=get_main_menu(message.from_user.id))

# --- MAJBURIY OBUNA ---
async def check_subscription(user_id):
    channel = get_setting('channel')
    if channel == 'none' or not channel: return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return True

# --- START ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    if not await check_subscription(user_id):
        channel = get_setting('channel')
        markup = InlineKeyboardBuilder().button(text="Obuna bo'lish", url=f"https://t.me/{channel.replace('@', '')}").as_markup()
        await message.answer(f"Botdan foydalanish uchun {channel} kanaliga obuna bo'ling!", reply_markup=markup)
        return

    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        if referrer_id and referrer_id != user_id:
            cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id))
            cursor.execute("UPDATE users SET points = points + 10000 WHERE user_id = ?", (referrer_id,))
            try: await bot.send_message(referrer_id, "🎉 Do'stingiz botga kirdi! Sizga 10,000 so'm bonus berildi!")
            except: pass
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    conn.close()
    await message.answer("Assalomu alaykum! Airmax Mobile do'koniga xush kelibsiz.", reply_markup=get_main_menu(user_id))

# ==========================================
# 👑 SUPER ADMIN PANEL FUNKSIYALARI
# ==========================================
@dp.message(F.text == "👑 Super Admin Panel")
async def super_admin_panel(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer("👑 Super Admin paneliga xush kelibsiz!", reply_markup=get_super_admin_menu())

@dp.message(F.text == "⚙️ Kanal sozlamalari")
async def settings_channel(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer(f"Hozirgi kanal: {get_setting('channel')}\n\nYangi kanal userneymini yuboring (@bilan) yoki 'none' deng:", reply_markup=get_cancel_menu())
    await state.set_state(SettingsState.channel)

@dp.message(SettingsState.channel)
async def process_channel(message: types.Message, state: FSMContext):
    update_setting('channel', message.text)
    await state.clear()
    await message.answer("✅ Kanal saqlandi!", reply_markup=get_super_admin_menu())

@dp.message(F.text == "📞 Aloqa raqamini o'zgartirish")
async def settings_phone(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer(f"Hozirgi raqam: {get_setting('admin_phone')}\n\nYangi raqamni yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(SettingsState.phone)

@dp.message(SettingsState.phone)
async def process_phone(message: types.Message, state: FSMContext):
    update_setting('admin_phone', message.text)
    await state.clear()
    await message.answer("✅ Aloqa raqami saqlandi!", reply_markup=get_super_admin_menu())

@dp.message(F.text == "🗑 Barcha mahsulotni tozalash")
async def clear_all_products(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM phones")
    conn.commit()
    conn.close()
    await message.answer("✅ Barcha mahsulotlar o'chirildi!")

@dp.message(F.text == "📢 Yangilik yuborish")
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer("Yangilikni yuboring (rasm yoki matn):", reply_markup=get_cancel_menu())
    await state.set_state(BroadcastNews.content)

@dp.message(BroadcastNews.content)
async def process_broadcast(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    status_msg = await message.answer("Jo'natilmoqda...")
    sent = 0
    text = "<b>🔔 Airmax Mobile:</b>\n\n"
    for (uid,) in users:
        try:
            if message.photo: await bot.send_photo(uid, message.photo[-1].file_id, caption=text+(message.caption or ""), parse_mode="HTML")
            else: await bot.send_message(uid, text+message.text, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except: pass
    await state.clear()
    await status_msg.edit_text(f"✅ Yetkazildi: {sent} ta mijozga.")
    await message.answer("Menyu:", reply_markup=get_super_admin_menu())

# ==========================================
# ASOSIY FUNKSIYALAR
# ==========================================
@dp.message(F.text == "🔍 Qidiruv")
async def start_search(message: types.Message, state: FSMContext):
    await message.answer("Qidirmoqchi bo'lgan modelingizni yozing (masalan: 15 pro):", reply_markup=get_cancel_menu())
    await state.set_state(SearchState.query)

@dp.message(SearchState.query)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text
    await state.clear()
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phones WHERE name LIKE ?", (f"%{query}%",))
    phones = cursor.fetchall()
    conn.close()
    if not phones:
        await message.answer("Bunday model topilmadi.", reply_markup=get_main_menu(message.from_user.id))
        return
    await message.answer(f"🔍 Natijalar:", reply_markup=get_main_menu(message.from_user.id))
    for phone in phones: await send_phone_card(message, phone)

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM phones")
    phones = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 <b>Statistika:</b>\n\n👥 Mijozlar: {users} ta\n📱 Qoldiq: {phones} xil", parse_mode="HTML")

@dp.message(F.text == "🎁 Referal (Bonus)")
async def referral_system(message: types.Message):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (message.from_user.id,))
    res = cursor.fetchone()
    conn.close()
    points = res[0] if res else 0
    ref_link = f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"
    await message.answer(f"🎁 <b>Referal</b>\n\nSizning balansingiz: <b>{points} so'm</b>\n\n👇 Havolani ulashing:\n{ref_link}", parse_mode="HTML")

# --- SAVAT VA ZAKAZ ---
@dp.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_callback(callback: types.CallbackQuery):
    phone_id = int(callback.data.split("_")[2])
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart (user_id, phone_id) VALUES (?, ?)", (callback.from_user.id, phone_id))
    conn.commit()
    conn.close()
    await callback.answer("🛒 Savatga qo'shildi!", show_alert=True)

@dp.callback_query(F.data == "out_of_stock")
async def out_of_stock_callback(callback: types.CallbackQuery):
    await callback.answer("❌ Kechirasiz, bu mahsulot hozircha qolmagan!", show_alert=True)

@dp.message(F.text == "🛒 Savat")
async def view_cart(message: types.Message):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT c.id, p.name, p.price FROM cart c JOIN phones p ON c.phone_id = p.id WHERE c.user_id = ?", (message.from_user.id,))
    items = cursor.fetchall()
    conn.close()
    if not items:
        await message.answer("🛒 Savatingiz bo'sh.")
        return
    text = "🛒 <b>Sizning savatingiz:</b>\n\n" + "\n".join([f"▪️ {i[1]} - {i[2]}" for i in items])
    inline_btn = InlineKeyboardBuilder()
    inline_btn.button(text="✅ Buyurtma berish", callback_data="checkout")
    inline_btn.button(text="🗑 Tozalash", callback_data="clear_cart")
    inline_btn.adjust(1)
    await message.answer(text, reply_markup=inline_btn.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (callback.from_user.id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text("🛒 Savatingiz tozalandi.")

@dp.callback_query(F.data == "checkout")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "📞 Raqamingizni yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(CheckoutState.phone_number)

@dp.message(CheckoutState.phone_number)
async def process_checkout(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT p.name, p.price FROM cart c JOIN phones p ON c.phone_id = p.id WHERE c.user_id = ?", (message.from_user.id,))
    items = cursor.fetchall()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (message.from_user.id,))
    points = cursor.fetchone()[0]
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (message.from_user.id,))
    cursor.execute("UPDATE users SET points = 0 WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    conn.close()

    order = "\n".join([f"▪️ {i[0]} ({i[1]})" for i in items])
    admin_text = f"🚨 <b>YANGI BUYURTMA!</b>\n👤 Mijoz ID: {message.from_user.id}\n📞 Tel: {message.text}\n🎁 Bonus: {points} so'm\n\n🛒 <b>Mahsulotlar:</b>\n{order}"
    await bot.send_message(SUPER_ADMIN_ID, admin_text, parse_mode="HTML")
    await state.clear()
    await message.answer(f"✅ Qabul qilindi!\n\n📞 <b>Tasdiqlash uchun:</b>\n{get_setting('admin_phone')}", reply_markup=get_main_menu(message.from_user.id), parse_mode="HTML")

# --- IPHONE ICHKI MENYULARI ---
@dp.message(F.text == "📱 iPhone")
async def iphone_menu(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 B/U iPhone")
    builder.button(text="✨ Yangi iPhone")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 1)
    await message.answer("iPhone bo'limini tanladingiz:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "✨ Yangi iPhone")
async def new_iphone_handler(message: types.Message):
    await message.answer("✨ Yangi iPhone modellari hozircha yo'q. **Tez kunda qo'shiladi!**", parse_mode="HTML")

iphone_models_list = ["iPhone 11", "iPhone 12", "iPhone 12 Pro", "iPhone 12 Pro Max", "iPhone 13", "iPhone 13 Pro", "iPhone 13 Pro Max", "iPhone 14", "iPhone 14 Pro", "iPhone 14 Pro Max", "iPhone 15", "iPhone 15 Pro", "iPhone 15 Pro Max", "iPhone 16", "iPhone 16 Pro", "iPhone 16 Pro Max", "iPhone 17", "iPhone 17 Pro", "iPhone 17 Pro Max", "iPhone 18 Pro", "iPhone 18 Pro Max"]

@dp.message(F.text == "📦 B/U iPhone")
async def bu_iphone_models(message: types.Message):
    builder = ReplyKeyboardBuilder()
    for m in iphone_models_list: builder.button(text=m)
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2)
    await message.answer("Kerakli modelni tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text in iphone_models_list)
async def show_iphone_models(message: types.Message):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phones WHERE name LIKE ?", (f"%{message.text}%",))
    phones = cursor.fetchall()
    conn.close()
    if not phones:
        await message.answer(f"Hozircha <b>{message.text}</b> yo'q.", parse_mode="HTML")
        return
    for phone in phones: await send_phone_card(message, phone)

# --- MAHSULOT KARTASI (✅ va ❌ mantiqi) ---
async def send_phone_card(message: types.Message, phone: tuple):
    phone_id, category, name, memory, battery, color, condition, price, quantity, photo = phone
    
    # Qoldiqqa qarab status o'zgaradi
    stock_icon = "✅ Bor" if quantity > 0 else "❌ Yo'q"
    
    text = (f"📱 <b>{name}</b>\n💾 Xotira: {memory}\n🔋 Battery: {battery}\n🎨 Rangi: {color}\n"
            f"🛠 Holati: {condition}\n💰 Narxi: {price}\n📦 Holati: {stock_icon} (Qoldiq: {quantity} ta)")
            
    inline_builder = InlineKeyboardBuilder()
    if quantity > 0:
        inline_builder.button(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{phone_id}")
    else:
        inline_builder.button(text="❌ Sotib bo'lingan", callback_data="out_of_stock")
        
    if message.from_user.id in ADMIN_IDS:
        inline_builder.button(text="🗑 O'chirish", callback_data=f"del_{phone_id}")
    inline_builder.adjust(1)
    
    if photo and photo != 'none': await message.answer_photo(photo=photo, caption=text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")
    else: await message.answer(text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")

@dp.message(F.text.in_(["📱 Samsung", "📱 HONOR", "📱 Redmi"]))
async def catalog_handler(message: types.Message):
    cat = message.text.replace("📱 ", "")
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phones WHERE category=?", (cat,))
    phones = cursor.fetchall()
    conn.close()
    if not phones:
        await message.answer(f"Hozircha {cat} modellari mavjud emas.")
        return
    for phone in phones: await send_phone_card(message, phone)

# --- MAHSULOT QO'SHISH ---
@dp.message(F.text == "➕ Yangi telefon")
async def start_add_phone(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    builder = ReplyKeyboardBuilder()
    for cat in ["iPhone", "Samsung", "HONOR", "Redmi"]: builder.button(text=cat)
    builder.button(text="❌ Bekor qilish")
    builder.adjust(2, 2, 1)
    await message.answer("Kategoriyani tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AddPhone.category)

@dp.message(AddPhone.category)
async def p_cat(m: types.Message, state: FSMContext): await state.update_data(category=m.text); await m.answer("Telefon nomi:", reply_markup=get_cancel_menu()); await state.set_state(AddPhone.name)
@dp.message(AddPhone.name)
async def p_name(m: types.Message, state: FSMContext): await state.update_data(name=m.text); await m.answer("Xotirasi:"); await state.set_state(AddPhone.memory)
@dp.message(AddPhone.memory)
async def p_mem(m: types.Message, state: FSMContext): await state.update_data(memory=m.text); await m.answer("Battery Health:"); await state.set_state(AddPhone.battery)
@dp.message(AddPhone.battery)
async def p_bat(m: types.Message, state: FSMContext): await state.update_data(battery=m.text); await m.answer("Rangi:"); await state.set_state(AddPhone.color)
@dp.message(AddPhone.color)
async def p_col(m: types.Message, state: FSMContext): await state.update_data(color=m.text); await m.answer("Holati:"); await state.set_state(AddPhone.condition)
@dp.message(AddPhone.condition)
async def p_cond(m: types.Message, state: FSMContext): await state.update_data(condition=m.text); await m.answer("Narxi ($):"); await state.set_state(AddPhone.price)
@dp.message(AddPhone.price)
async def p_price(m: types.Message, state: FSMContext): await state.update_data(price=m.text); await m.answer("Qoldiq (nechta bor):"); await state.set_state(AddPhone.quantity)
@dp.message(AddPhone.quantity)
async def p_qty(m: types.Message, state: FSMContext):
    try: await state.update_data(quantity=int(m.text))
    except: await m.answer("Faqat raqam kiriting!"); return
    await m.answer("Rasm yuboring:"); await state.set_state(AddPhone.photo)

@dp.message(AddPhone.photo)
async def p_photo(m: types.Message, state: FSMContext):
    if not m.photo: return await m.answer("Rasm yuboring:")
    await state.update_data(photo=m.photo[-1].file_id)
    d = await state.get_data()
    text = f"📱 {d['name']}\n💾 {d['memory']}\n🔋 {d['battery']}\n🎨 {d['color']}\n🛠 {d['condition']}\n💰 {d['price']}\n📦 Qoldiq: {d['quantity']} ta\n\nSaqlansinmi?"
    btn = InlineKeyboardBuilder().button(text="✅ Tasdiqlash", callback_data="confirm_add").button(text="❌ Bekor", callback_data="cancel_add").adjust(2)
    await m.answer_photo(photo=d['photo'], caption=text, reply_markup=btn.as_markup())
    await m.answer("Tanlang:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddPhone.confirm)

@dp.callback_query(F.data.in_(["confirm_add", "cancel_add"]))
async def confirm_addition(c: types.CallbackQuery, state: FSMContext):
    if c.data == "cancel_add":
        await state.clear(); await c.message.delete(); await bot.send_message(c.from_user.id, "❌ Bekor qilindi.", reply_markup=get_main_menu(c.from_user.id)); return
    d = await state.get_data()
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO phones (category, name, memory, battery, color, condition, price, quantity, photo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (d['category'], d['name'], d['memory'], d['battery'], d['color'], d['condition'], d['price'], d['quantity'], d['photo']))
    conn.commit(); conn.close()
    await c.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(c.from_user.id, "✅ Qo'shildi!", reply_markup=get_main_menu(c.from_user.id))
    await state.clear()

@dp.callback_query(F.data.startswith("del_"))
async def del_cb(c: types.CallbackQuery):
    if c.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('shop.db'); cur = conn.cursor(); cur.execute("DELETE FROM phones WHERE id = ?", (int(c.data.split("_")[1]),)); conn.commit(); conn.close()
    await c.message.delete(); await c.answer("✅ O'chirildi!")

@dp.message()
async def txt_hndl(m: types.Message):
    if m.text == "🎧 Aksessuarlar": await m.answer("Aksessuarlar bo'limiga tez orada mahsulotlar qo'shiladi.")
    elif m.text == "📞 Operator": await m.answer(f"📞 Telefon: {get_setting('admin_phone')}\n✍️ Telegram: @AirmaxAdmin")

# --- RENDER SERVER ---
async def run_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot ishlayapti!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

async def main():
    asyncio.create_task(run_server())
    print("Maksimal bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
