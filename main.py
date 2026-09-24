import os
import asyncio
import logging
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "8582520793:AAEJw65DPp780yky_wZHlKFyIQJNkJ3GowM"

# O'zingizning botingiz userneymini yozing (@ belgisiz)
BOT_USERNAME = "AirmaxMobileBot" 

SUPER_ADMIN_ID = 6738533029  
ADMIN_IDS = [6738533029, 5156453500]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# BAZANI XAVFSIZ YANGILASH VA YARATISH
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    # 1. Telefonlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            memory TEXT,
            battery TEXT,
            color TEXT,
            condition TEXT,
            price TEXT,
            quantity INTEGER,
            photo TEXT
        )
    ''')
    
    # 2. Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    # Eski users jadvaliga yangi ustunlar qo'shish (Referal tizimi uchun)
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'points' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    if 'referred_by' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
        
    # 3. Savat (Korzinka) jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone_id INTEGER,
            quantity INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# HOLATLAR (States)
class AddPhone(StatesGroup):
    category, name, memory, battery, color, condition, price, quantity, photo, confirm = State(), State(), State(), State(), State(), State(), State(), State(), State(), State()

class BroadcastNews(StatesGroup):
    content = State()

class SearchState(StatesGroup):
    query = State()

class CheckoutState(StatesGroup):
    phone_number = State()

# ASOSIY MENYU
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
        builder.button(text="📢 Yangilik yuborish")
        builder.button(text="🗑 Barcha mahsulotni tozalash")
        
    builder.adjust(2, 2, 2, 2, 1, 2, 2)
    return builder.as_markup(resize_keyboard=True)

# /START VA REFERAL TEKSHIRUVI
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        if referrer_id and referrer_id != user_id:
            cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id))
            # Refererga 10 000 so'mlik bonus ball yozamiz
            cursor.execute("UPDATE users SET points = points + 10000 WHERE user_id = ?", (referrer_id,))
            try:
                await bot.send_message(referrer_id, "🎉 Tabriklaymiz! Sizning taklifingiz orqali yangi do'stingiz botga kirdi. Sizga 10,000 so'm bonus berildi!")
            except:
                pass
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    conn.close()

    await message.answer(
        "Assalomu alaykum! Airmax Mobile do'koniga xush kelibsiz. Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(user_id)
    )

# --- 1. QIDIRUV FUNKSIYASI ---
@dp.message(lambda message: message.text == "🔍 Qidiruv")
async def start_search(message: types.Message, state: FSMContext):
    await message.answer("Qidirmoqchi bo'lgan modelingizni yozing (masalan: 15 pro):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SearchState.query)

@dp.message(SearchState.query)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text
    await state.clear()
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, memory, battery, color, condition, price, quantity, photo FROM phones WHERE name LIKE ?", (f"%{query}%",))
    phones = cursor.fetchall()
    conn.close()

    if not phones:
        await message.answer("Bunday model topilmadi.", reply_markup=get_main_menu(message.from_user.id))
        return

    await message.answer(f"🔍 Qidiruv natijalari:", reply_markup=get_main_menu(message.from_user.id))
    for phone in phones:
        await send_phone_card(message, phone)

# --- 2. STATISTIKA (ADMIN) ---
@dp.message(lambda message: message.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM phones")
    phones_count = cursor.fetchone()[0]
    conn.close()
    
    text = (
        f"📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 Umumiy mijozlar: {users_count} ta\n"
        f"📱 Baza qoldig'i (xil): {phones_count} xil mahsulot"
    )
    await message.answer(text, parse_mode="HTML")

# --- 3. REFERAL TIZIMI ---
@dp.message(lambda message: message.text == "🎁 Referal (Bonus)")
async def referral_system(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    points = res[0] if res else 0
    conn.close()
    
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    text = (
        f"🎁 <b>Referal Dasturi</b>\n\n"
        f"Do'stlaringizni taklif qiling va har bir do'stingiz uchun 10,000 so'm chegirma bonusi oling!\n\n"
        f"💰 Sizning balansingiz: <b>{points} so'm</b>\n\n"
        f"👇 Quyidagi havolani do'stlaringizga yuboring:\n{ref_link}"
    )
    await message.answer(text, parse_mode="HTML")

# --- 4. SAVAT VA BUYURTMA ---
@dp.callback_query(lambda c: c.data.startswith("add_cart_"))
async def add_to_cart_callback(callback: types.CallbackQuery):
    phone_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart (user_id, phone_id) VALUES (?, ?)", (user_id, phone_id))
    conn.commit()
    conn.close()
    
    await callback.answer("🛒 Savatga qo'shildi!", show_alert=True)

@dp.message(lambda message: message.text == "🛒 Savat")
async def view_cart(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, p.name, p.price 
        FROM cart c 
        JOIN phones p ON c.phone_id = p.id 
        WHERE c.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    conn.close()
    
    if not cart_items:
        await message.answer("🛒 Savatingiz bo'sh.")
        return

    text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    for item in cart_items:
        text += f"▪️ {item[1]} - {item[2]}\n"
        
    inline_btn = InlineKeyboardBuilder()
    inline_btn.button(text="✅ Buyurtma berish", callback_data="checkout")
    inline_btn.button(text="🗑 Tozalash", callback_data="clear_cart")
    inline_btn.adjust(1)
    
    await message.answer(text, reply_markup=inline_btn.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_callback(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (callback.from_user.id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text("🛒 Savatingiz tozalandi.")

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "📞 Iltimos, telefon raqamingizni yuboring (masalan: +998901234567):")
    await state.set_state(CheckoutState.phone_number)

@dp.message(CheckoutState.phone_number)
async def process_checkout(message: types.Message, state: FSMContext):
    phone_number = message.text
    user_id = message.from_user.id
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.name, p.price 
        FROM cart c 
        JOIN phones p ON c.phone_id = p.id 
        WHERE c.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    
    # Bonusni olish
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    points = cursor.fetchone()[0]
    
    # Savatni tozalash va bonusni yechish
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE users SET points = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    order_details = "\n".join([f"▪️ {item[0]} ({item[1]})" for item in cart_items])
    
    admin_text = (
        f"🚨 <b>YANGI BUYURTMA!</b>\n\n"
        f"👤 Mijoz ID: {user_id}\n"
        f"📞 Tel: {phone_number}\n"
        f"🎁 Ishlatilgan bonus: {points} so'm\n\n"
        f"🛒 <b>Mahsulotlar:</b>\n{order_details}"
    )
    
    # Super Adminga xabar ketadi
    await bot.send_message(SUPER_ADMIN_ID, admin_text, parse_mode="HTML")
    
    await state.clear()
    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz siz bilan bog'lanishadi.", reply_markup=get_main_menu(user_id))


# --- KATALOG VA TELEFON KARTOCHKASI ---
async def send_phone_card(message: types.Message, phone: tuple):
    phone_id, name, memory, battery, color, condition, price, quantity, photo = phone
    text = (
        f"📱 <b>{name}</b>\n"
        f"💾 Xotira: {memory}\n"
        f"🔋 Battery: {battery}\n"
        f"🎨 Rangi: {color}\n"
        f"🛠 Holati: {condition}\n"
        f"💰 Narxi: {price}\n"
        f"📦 Qoldiq: {quantity} ta"
    )
    inline_builder = InlineKeyboardBuilder()
    inline_builder.button(text="🛒 Savatga qo'shish", callback_data=f"add_cart_{phone_id}")
    
    if message.from_user.id in ADMIN_IDS:
        inline_builder.button(text="🗑 Sotildi (O'chirish)", callback_data=f"del_{phone_id}")
    inline_builder.adjust(1)
    
    if photo and photo != 'none':
        await message.answer_photo(photo=photo, caption=text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")

async def show_category_phones(message: types.Message, category_name: str):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, memory, battery, color, condition, price, quantity, photo FROM phones WHERE category=?", (category_name,))
    phones = cursor.fetchall()
    conn.close()

    if not phones:
        await message.answer(f"Hozircha {category_name} modellari mavjud emas.")
        return
    for phone in phones:
        await send_phone_card(message, phone)

@dp.message(lambda message: message.text in ["📱 iPhone", "📱 Samsung", "📱 HONOR", "📱 Redmi"])
async def catalog_handler(message: types.Message):
    category = message.text.replace("📱 ", "")
    await show_category_phones(message, category)

# --- ADMIN: TOZALASH, YANGILIK, QO'SHISH, O'CHIRISH (Oldingi kodlar to'liq saqlangan) ---

@dp.message(lambda message: message.text == "🗑 Barcha mahsulotni tozalash")
async def clear_all_products(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM phones")
    conn.commit()
    conn.close()
    await message.answer("✅ Barcha mahsulotlar o'chirildi!")

@dp.message(lambda message: message.text == "📢 Yangilik yuborish")
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID: return
    cancel_btn = ReplyKeyboardBuilder().button(text="❌ Bekor qilish")
    await message.answer("Yubormoqchi bo'lgan yangiligingizni yozing (rasm ham bo'lishi mumkin):", reply_markup=cancel_btn.as_markup(resize_keyboard=True))
    await state.set_state(BroadcastNews.content)

@dp.message(BroadcastNews.content)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu(message.from_user.id))
        return
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    status_msg = await message.answer("Xabar jo'natilmoqda...")
    sent_count = 0
    header_text = "<b>🔔 Airmax Mobile:</b>\n\n"
    for (uid,) in users:
        try:
            if message.photo:
                await bot.send_photo(chat_id=uid, photo=message.photo[-1].file_id, caption=header_text + (message.caption or ""), parse_mode="HTML")
            else:
                await bot.send_message(chat_id=uid, text=header_text + message.text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)
        except: continue
    await state.clear()
    await status_msg.edit_text(f"✅ Yangilik tarqatildi! Yetkazildi: {sent_count} ta mijozga.")
    await message.answer("Menyu:", reply_markup=get_main_menu(message.from_user.id))

@dp.message(lambda message: message.text == "➕ Yangi telefon")
async def start_add_phone(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    builder = ReplyKeyboardBuilder()
    for cat in ["iPhone", "Samsung", "HONOR", "Redmi"]: builder.button(text=cat)
    builder.adjust(2)
    await message.answer("Kategoriyani tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AddPhone.category)

@dp.message(AddPhone.category)
async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Telefon nomini yuboring (masalan: iPhone 15 Pro):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddPhone.name)

@dp.message(AddPhone.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Xotirasini yuboring:")
    await state.set_state(AddPhone.memory)

@dp.message(AddPhone.memory)
async def process_memory(message: types.Message, state: FSMContext):
    await state.update_data(memory=message.text)
    await message.answer("Battery Health yuboring:")
    await state.set_state(AddPhone.battery)

@dp.message(AddPhone.battery)
async def process_battery(message: types.Message, state: FSMContext):
    await state.update_data(battery=message.text)
    await message.answer("Rangini yuboring:")
    await state.set_state(AddPhone.color)

@dp.message(AddPhone.color)
async def process_color(message: types.Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer("Holatini yuboring:")
    await state.set_state(AddPhone.condition)

@dp.message(AddPhone.condition)
async def process_condition(message: types.Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Narxini yuboring (masalan: $950):")
    await state.set_state(AddPhone.price)

@dp.message(AddPhone.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Sotuvdagi sonini raqamda yuboring:")
    await state.set_state(AddPhone.quantity)

@dp.message(AddPhone.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    try: await state.update_data(quantity=int(message.text))
    except ValueError:
        await message.answer("Faqat raqam kiriting:")
        return
    await message.answer("Endi telefon rasmini yuboring:")
    await state.set_state(AddPhone.photo)

@dp.message(AddPhone.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Rasm yuboring:")
        return
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    text = (f"<b>Qo'shilsinmi?</b>\n\n📱 Nomi: {data['name']}\n📂 Kategoriya: {data['category']}\n"
            f"💾 Xotira: {data['memory']}\n🔋 Battery: {data['battery']}\n🎨 Rangi: {data['color']}\n"
            f"🛠 Holati: {data['condition']}\n💰 Narxi: {data['price']}\n📦 Qoldiq: {data['quantity']} ta")
    inline_btn = InlineKeyboardBuilder()
    inline_btn.button(text="✅ Tasdiqlash", callback_data="confirm_add")
    inline_btn.button(text="❌ Bekor qilish", callback_data="cancel_add")
    inline_btn.adjust(2)
    await message.answer_photo(photo=data['photo'], caption=text, reply_markup=inline_btn.as_markup(), parse_mode="HTML")
    await state.set_state(AddPhone.confirm)

@dp.callback_query(lambda c: c.data in ["confirm_add", "cancel_add"])
async def confirm_addition(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "cancel_add":
        await state.clear()
        await callback.message.delete()
        await bot.send_message(callback.from_user.id, "❌ Bekor qilindi.", reply_markup=get_main_menu(callback.from_user.id))
        return
    data = await state.get_data()
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO phones (category, name, memory, battery, color, condition, price, quantity, photo)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                   (data['category'], data['name'], data['memory'], data['battery'], data['color'], data['condition'], data['price'], data['quantity'], data['photo']))
    conn.commit()
    conn.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await bot.send_message(callback.from_user.id, "✅ Mahsulot qo'shildi!", reply_markup=get_main_menu(callback.from_user.id))
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("del_"))
async def delete_phone_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    phone_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM phones WHERE id = ?", (phone_id,))
    conn.commit()
    conn.close()
    await callback.message.delete()
    await callback.answer("✅ O'chirildi!")

@dp.message()
async def text_handler(message: types.Message):
    if message.text == "🎧 Aksessuarlar":
        await message.answer("Aksessuarlar bo'limiga tez orada mahsulotlar qo'shiladi.")
    elif message.text == "📞 Operator":
        await message.answer("📞 Operator: +998 90 000-00-00\n✍️ Telegram: @AirmaxAdmin")

# --- RENDER SERVER ---
async def run_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot ishlayapti!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    asyncio.create_task(run_server())
    print("Maksimal darajadagi bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
