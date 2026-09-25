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

# Huquqlar taqsimoti
SUPER_ADMIN_ID = 6738533029  # Faqat shu ID egasida Super Admin panel chiqadi
STATIC_ADMIN_IDS = [6738533029, 5156453500] # Bu ikki ID mahsulot qo'shish/o'chirish huquqiga ega

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, name TEXT, memory TEXT, battery TEXT, color TEXT, 
            condition TEXT, price TEXT, quantity INTEGER, photo TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, referred_by INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, phone_id INTEGER, quantity INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
            user_id INTEGER PRIMARY KEY, name TEXT, role TEXT, branch TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, address TEXT, location TEXT)''')
    
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_phone', '+998 95 776 02 22')")
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
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def is_admin(user_id):
    return user_id in STATIC_ADMIN_IDS

iphone_models_list = ["iPhone 11", "iPhone 12", "iPhone 12 Pro", "iPhone 12 Pro Max", "iPhone 13", "iPhone 13 Pro", "iPhone 13 Pro Max", "iPhone 14", "iPhone 14 Pro", "iPhone 14 Pro Max", "iPhone 15", "iPhone 15 Pro", "iPhone 15 Pro Max", "iPhone 16", "iPhone 16 Pro", "iPhone 16 Pro Max", "iPhone 17", "iPhone 17 Pro", "iPhone 17 Pro Max", "iPhone 18 Pro", "iPhone 18 Pro Max"]

class AddPhone(StatesGroup):
    category, name, memory, battery, color, condition, price, quantity, photo, confirm = State(), State(), State(), State(), State(), State(), State(), State(), State(), State()
class BroadcastNews(StatesGroup): content = State()
class SearchState(StatesGroup): query = State()
class CheckoutState(StatesGroup): phone_number = State()
class SettingsState(StatesGroup): channel = State(); phone = State()

def get_main_menu(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 iPhone")
    builder.button(text="📱 Samsung")
    builder.button(text="📱 HONOR")
    builder.button(text="📱 Redmi")
    builder.button(text="🎧 Aksessuarlar")
    builder.button(text="🔍 Qidiruv")
    builder.button(text="🛒 Savat")
    builder.button(text="📞 Operator")
    builder.button(text="🏢 Filiallarimiz")
    
    if is_admin(user_id):
        builder.button(text="➕ Mahsulot qo'shish")
        builder.button(text="📊 Statistika")
    if user_id == SUPER_ADMIN_ID:
        builder.button(text="👑 Super Admin Panel")
        
    builder.adjust(2, 2, 2, 2, 1, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_super_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="⚙️ Kanal sozlamalari")
    builder.button(text="📞 Aloqa raqami")
    builder.button(text="📢 Yangilik yuborish")
    builder.button(text="🏢 Filiallarni boshqarish")
    builder.button(text="🔙 Bosh menyu")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_menu():
    return ReplyKeyboardBuilder().button(text="❌ Bekor qilish").as_markup(resize_keyboard=True)

@dp.message(F.text == "❌ Bekor qilish", StateFilter('*'))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == SUPER_ADMIN_ID:
        await message.answer("❌ Amal bekor qilindi.", reply_markup=get_super_admin_menu())
    else:
        await message.answer("❌ Amal bekor qilindi va bosh menyuga qaytdingiz.", reply_markup=get_main_menu(message.from_user.id))

@dp.message(F.text.in_(["🔙 Bosh menyu", "⬅️ Orqaga"]), StateFilter('*'))
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=get_main_menu(message.from_user.id))

async def check_subscription(user_id):
    channel = get_setting('channel')
    if channel == 'none' or not channel: return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return True 

@dp.message(Command("start"), StateFilter('*'))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        channel = get_setting('channel')
        markup = InlineKeyboardBuilder().button(text="Obuna bo'lish", url=f"https://t.me/{channel.replace('@', '')}").as_markup()
        await message.answer(f"Botdan foydalanish uchun {channel} kanaliga obuna bo'ling!", reply_markup=markup)
        return
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    conn.close()
    await message.answer("Assalomu alaykum! Airmax Mobile do'koniga xush kelibsiz.", reply_markup=get_main_menu(user_id))

# ==========================================
# 🛑 MAHSULOT QO'SHISH (IPHONE MODEL TANLASH BILAN)
# ==========================================
@dp.message(F.text == "➕ Mahsulot qo'shish", StateFilter(None))
async def start_add_phone(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 B/U iPhone")
    builder.button(text="✨ Yangi iPhone")
    builder.button(text="Samsung")
    builder.button(text="HONOR")
    builder.button(text="Redmi")
    builder.button(text="Aksessuarlar")
    builder.button(text="❌ Bekor qilish")
    builder.adjust(2, 2, 2, 1)
    
    await message.answer("Qaysi bo'limga mahsulot qo'shasiz? Tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AddPhone.category)

@dp.message(AddPhone.category)
async def p_cat(m: types.Message, state: FSMContext):
    await state.update_data(category=m.text)
    
    if m.text in ["📦 B/U iPhone", "✨ Yangi iPhone"]:
        builder = ReplyKeyboardBuilder()
        for model in iphone_models_list:
            builder.button(text=model)
        builder.button(text="❌ Bekor qilish")
        builder.adjust(2)
        await m.answer("Qaysi modelni qo'shasiz? Ro'yxatdan tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    else:
        await m.answer(f"Mahsulot nomi (Masalan: S24 Ultra, to'liq yozing!):", reply_markup=get_cancel_menu())
        
    await state.set_state(AddPhone.name)

@dp.message(AddPhone.name)
async def p_name(m: types.Message, state: FSMContext): 
    await state.update_data(name=m.text)
    await m.answer("Xotirasi (Agar aksessuar bo'lsa '-' yozing):", reply_markup=get_cancel_menu())
    await state.set_state(AddPhone.memory)

@dp.message(AddPhone.memory)
async def p_mem(m: types.Message, state: FSMContext): 
    await state.update_data(memory=m.text)
    await m.answer("Battery Health (Agar aksessuar bo'lsa '-' yozing):")
    await state.set_state(AddPhone.battery)

@dp.message(AddPhone.battery)
async def p_bat(m: types.Message, state: FSMContext): 
    await state.update_data(battery=m.text)
    await m.answer("Rangi (Agar yo'q bo'lsa '-' yozing):")
    await state.set_state(AddPhone.color)

@dp.message(AddPhone.color)
async def p_col(m: types.Message, state: FSMContext): 
    await state.update_data(color=m.text)
    await m.answer("Holati (Yangi / Ideal / Qirilgan):")
    await state.set_state(AddPhone.condition)

@dp.message(AddPhone.condition)
async def p_cond(m: types.Message, state: FSMContext): 
    await state.update_data(condition=m.text)
    await m.answer("Narxi ($):")
    await state.set_state(AddPhone.price)

@dp.message(AddPhone.price)
async def p_price(m: types.Message, state: FSMContext): 
    await state.update_data(price=m.text)
    await m.answer("Qoldiq (omborda nechta bor, faqat raqam yozing):")
    await state.set_state(AddPhone.quantity)

@dp.message(AddPhone.quantity)
async def p_qty(m: types.Message, state: FSMContext):
    try: await state.update_data(quantity=int(m.text))
    except: await m.answer("Faqat raqam kiriting!"); return
    await m.answer("Rasm yuboring:")
    await state.set_state(AddPhone.photo)

@dp.message(AddPhone.photo)
async def p_photo(m: types.Message, state: FSMContext):
    if not m.photo: return await m.answer("Iltimos, rasm yuboring:")
    await state.update_data(photo=m.photo[-1].file_id)
    d = await state.get_data()
    text = f"📱 {d['name']}\n📂 {d['category']}\n💾 {d['memory']}\n🔋 {d['battery']}\n🎨 {d['color']}\n🛠 {d['condition']}\n💰 {d['price']}\n📦 Qoldiq: {d['quantity']} ta\n\nShu mahsulot omborga saqlansinmi?"
    btn = InlineKeyboardBuilder().button(text="✅ Tasdiqlash", callback_data="confirm_add").button(text="❌ Bekor", callback_data="cancel_add").adjust(2)
    await m.answer_photo(photo=d['photo'], caption=text, reply_markup=btn.as_markup())
    await m.answer("Quyidagilardan tanlang:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddPhone.confirm)

@dp.callback_query(F.data.in_(["confirm_add", "cancel_add"]))
async def confirm_addition(c: types.CallbackQuery, state: FSMContext):
    if c.data == "cancel_add":
        await state.clear(); await c.message.delete(); await bot.send_message(c.from_user.id, "❌ Bekor qilindi.", reply_markup=get_main_menu(c.from_user.id)); return
    
    d = await state.get_data()
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO phones (category, name, memory, battery, color, condition, price, quantity, photo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (d['category'], d['name'], d['memory'], d['battery'], d['color'], d['condition'], d['price'], d['quantity'], d['photo']))
    conn.commit()
    
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    await c.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(c.from_user.id, f"✅ Mahsulot <b>{d['category']}</b> bo'limiga muvaffaqiyatli qo'shildi! Mijozlarga xabar yuborilmoqda...", reply_markup=get_main_menu(c.from_user.id), parse_mode="HTML")
    
    notification_text = (
        f"🚨 <b>YANGI MAHSULOT QO'SHILDI!</b> 🚨\n\n"
        f"📱 <b>{d['name']}</b>\n"
        f"📂 Bo'lim: <b>{d['category']}</b>\n"
        f"💾 Xotira: {d['memory']}\n"
        f"🔋 Battery: {d['battery']}\n"
        f"🎨 Rangi: {d['color']}\n"
        f"🛠 Holati: {d['condition']}\n"
        f"💰 Narxi: <b>{d['price']}</b>\n\n"
        f"❗️ <b>Kelishadigan joyi bor</b> ❗️\n\n"
        f"👉 Ko'rish uchun botga kiring!"
    )
    
    for user in users:
        u_id = user[0]
        try:
            await bot.send_photo(chat_id=u_id, photo=d['photo'], caption=notification_text, parse_mode="HTML")
            await asyncio.sleep(0.05)
        except Exception:
            pass 
            
    await state.clear()


# ==========================================
# 6. ASOSIY BO'LIMLAR
# ==========================================
@dp.message(F.text == "🔍 Qidiruv", StateFilter(None))
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

@dp.callback_query(F.data.startswith("add_cart_"), StateFilter(None))
async def add_to_cart_callback(callback: types.CallbackQuery):
    phone_id = int(callback.data.split("_")[2])
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart (user_id, phone_id) VALUES (?, ?)", (callback.from_user.id, phone_id))
    conn.commit()
    conn.close()
    await callback.answer("🛒 Savatga qo'shildi!", show_alert=True)

@dp.callback_query(F.data == "out_of_stock", StateFilter(None))
async def out_of_stock_callback(callback: types.CallbackQuery):
    await callback.answer("❌ Kechirasiz, bu mahsulot hozircha qolmagan!", show_alert=True)

@dp.message(F.text == "🛒 Savat", StateFilter(None))
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

@dp.callback_query(F.data == "clear_cart", StateFilter(None))
async def clear_cart_callback(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (callback.from_user.id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text("🛒 Savatingiz tozalandi.")

@dp.callback_query(F.data == "checkout", StateFilter(None))
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "📞 Zakaz berish uchun raqamingizni yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(CheckoutState.phone_number)

@dp.message(CheckoutState.phone_number)
async def process_checkout(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT p.name, p.price FROM cart c JOIN phones p ON c.phone_id = p.id WHERE c.user_id = ?", (message.from_user.id,))
    items = cursor.fetchall()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    conn.close()

    order = "\n".join([f"▪️ {i[0]} ({i[1]})" for i in items])
    admin_text = f"🚨 <b>YANGI BUYURTMA!</b>\n👤 Mijoz ID: {message.from_user.id}\n📞 Tel: {message.text}\n\n🛒 <b>Mahsulotlar:</b>\n{order}"
    await bot.send_message(SUPER_ADMIN_ID, admin_text, parse_mode="HTML")
    await state.clear()
    
    admin_contact = get_setting('admin_phone')
    await message.answer(f"✅ Buyurtmangiz qabul qilindi!\n\n📞 <b>Tasdiqlash uchun ushbu raqamga qo'ng'iroq qiling:</b>\n{admin_contact}", reply_markup=get_main_menu(message.from_user.id), parse_mode="HTML")


# ==========================================
# 7. IPHONE VA BOSHQALAR KATEGORIYALARI
# ==========================================
@dp.message(F.text == "📱 iPhone", StateFilter(None))
async def iphone_menu(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 B/U iPhone")
    builder.button(text="✨ Yangi iPhone")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 1)
    await message.answer("iPhone bo'limini tanladingiz:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📦 B/U iPhone", StateFilter(None))
async def bu_iphone_models(message: types.Message):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    builder = ReplyKeyboardBuilder()
    for m in iphone_models_list:
        cursor.execute("SELECT SUM(quantity) FROM phones WHERE category='📦 B/U iPhone' AND name LIKE ?", (f"%{m}%",))
        res = cursor.fetchone()
        qty = res[0] if res[0] else 0
        if qty > 0: builder.button(text=f"✅ {m}")
        else: builder.button(text=f"❌ {m}")
    conn.close()
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2)
    await message.answer("📦 B/U iPhone modellari (✅ - bor, ❌ - yo'q):", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "✨ Yangi iPhone", StateFilter(None))
async def new_iphone_models(message: types.Message):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    builder = ReplyKeyboardBuilder()
    for m in iphone_models_list:
        cursor.execute("SELECT SUM(quantity) FROM phones WHERE category='✨ Yangi iPhone' AND name LIKE ?", (f"%{m}%",))
        res = cursor.fetchone()
        qty = res[0] if res[0] else 0
        if qty > 0: builder.button(text=f"✅ {m}")
        else: builder.button(text=f"❌ {m}")
    conn.close()
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2)
    await message.answer("✨ Yangi iPhone modellari (✅ - bor, ❌ - yo'q):", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda msg: msg.text and (msg.text.startswith("✅ iPhone") or msg.text.startswith("❌ iPhone")), StateFilter(None))
async def show_iphone_models(message: types.Message):
    model_name = message.text.replace("✅ ", "").replace("❌ ", "")
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phones WHERE name LIKE ? AND category LIKE '%iPhone%'", (f"%{model_name}%",))
    phones = cursor.fetchall()
    conn.close()
    
    if not phones:
        await message.answer(f"❌ Kechirasiz, <b>{model_name}</b> hozircha omborda yo'q.", parse_mode="HTML")
        return
        
    found_in_stock = False
    for phone in phones:
        if phone[8] > 0:
            await send_phone_card(message, phone)
            found_in_stock = True
            
    if not found_in_stock:
        await message.answer(f"❌ Kechirasiz, <b>{model_name}</b> barchasi sotib bo'lingan.", parse_mode="HTML")

async def send_phone_card(message: types.Message, phone: tuple):
    phone_id, category, name, memory, battery, color, condition, price, quantity, photo = phone
    stock_icon = "✅ Bor" if quantity > 0 else "❌ Yo'q"
    text = (f"📱 <b>{name}</b>\n📂 Bo'lim: {category}\n💾 Xotira: {memory}\n🔋 Battery: {battery}\n🎨 Rangi: {color}\n"
            f"🛠 Holati: {condition}\n💰 Narxi: {price}\n📦 Holati: {stock_icon} (Qoldiq: {quantity} ta)\n\n❗️ <b>Kelishadigan joyi bor</b> ❗️")
            
    inline_builder = InlineKeyboardBuilder()
    if quantity > 0: inline_builder.button(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{phone_id}")
    else: inline_builder.button(text="❌ Sotib bo'lingan", callback_data="out_of_stock")
        
    if is_admin(message.from_user.id): inline_builder.button(text="🗑 O'chirish", callback_data=f"del_{phone_id}")
    inline_builder.adjust(1)
    
    if photo and photo != 'none': await message.answer_photo(photo=photo, caption=text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")
    else: await message.answer(text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")

@dp.message(F.text.in_(["📱 Samsung", "📱 HONOR", "📱 Redmi", "🎧 Aksessuarlar"]), StateFilter(None))
async def catalog_handler(message: types.Message):
    cat = message.text.replace("📱 ", "").replace("🎧 ", "")
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phones WHERE category=?", (cat,))
    phones = cursor.fetchall()
    conn.close()
    if not phones:
        await message.answer(f"Hozircha {cat} bo'limida mahsulotlar mavjud emas.")
        return
    for phone in phones: await send_phone_card(message, phone)

@dp.callback_query(F.data.startswith("del_"), StateFilter(None))
async def del_cb(c: types.CallbackQuery):
    if not is_admin(c.from_user.id): return
    conn = sqlite3.connect('shop.db'); cur = conn.cursor(); cur.execute("DELETE FROM phones WHERE id = ?", (int(c.data.split("_")[1]),)); conn.commit(); conn.close()
    await c.message.delete(); await c.answer("✅ O'chirildi!")

# ==========================================
# 8. SUPER ADMIN VA QOLGAN FUNKSIYALAR
# ==========================================
@dp.message(F.text == "👑 Super Admin Panel", StateFilter(None))
async def super_admin_panel(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer("👑 Super Admin paneliga xush kelibsiz!", reply_markup=get_super_admin_menu())

@dp.message(F.text == "⚙️ Kanal sozlamalari", StateFilter(None))
async def settings_channel(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer(f"Hozirgi kanal: {get_setting('channel')}\n\nYangi kanal userneymini yuboring (@bilan) yoki 'none' deng:", reply_markup=get_cancel_menu())
    await state.set_state(SettingsState.channel)

@dp.message(SettingsState.channel)
async def process_channel(message: types.Message, state: FSMContext):
    update_setting('channel', message.text)
    await state.clear()
    await message.answer("✅ Kanal saqlandi!", reply_markup=get_super_admin_menu())

@dp.message(F.text == "📞 Aloqa raqami", StateFilter(None))
async def settings_phone(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID: return
    await message.answer(f"Hozirgi raqam: {get_setting('admin_phone')}\n\nYangi raqamni yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(SettingsState.phone)

@dp.message(SettingsState.phone)
async def process_phone(message: types.Message, state: FSMContext):
    update_setting('admin_phone', message.text)
    await state.clear()
    await message.answer("✅ Aloqa raqami saqlandi!", reply_markup=get_super_admin_menu())

@dp.message(F.text == "📢 Yangilik yuborish", StateFilter(None))
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

@dp.message(F.text == "🏢 Filiallarimiz", StateFilter(None))
async def show_branches(message: types.Message):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM branches")
    brs = cursor.fetchall()
    conn.close()
    if not brs: await message.answer("Hozircha filiallar haqida ma'lumot yo'q.")
    else:
        text = "<b>🏢 Bizning filiallarimiz:</b>\n\n"
        for b in brs: text += f"📍 <b>{b[1]}</b>\nManzil: {b[2]}\nLokatsiya: {b[3]}\n\n"
        await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "📞 Operator", StateFilter(None))
async def operator_handler(message: types.Message):
    admin_phone = get_setting('admin_phone')
    await message.answer(f"📞 Telefon: {admin_phone}\n✍️ Telegram: @AirmaxAdmin")

@dp.message(F.text == "📊 Statistika", StateFilter(None))
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM phones")
    phones = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 <b>Statistika:</b>\n\n👥 Mijozlar: {users} ta\n📱 Qoldiq: {phones} xil mahsulot", parse_mode="HTML")

async def run_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot ishlayapti!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

async def main():
    asyncio.create_task(run_server())
    print("Tayyor bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
