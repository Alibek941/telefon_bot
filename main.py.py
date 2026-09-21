import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "8582520793:AAEJw65DPp780yky_wZHlKFyIQJNkJ3GowM"

# Ruxsat berilgan 2 ta admin ID raqami
ADMIN_IDS = [6738533029, 5156453500]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class AddPhone(StatesGroup):
    category = State()
    name = State()
    memory = State()
    battery = State()
    color = State()
    condition = State()
    price = State()
    quantity = State()
    photo = State()

# Asosiy menyu (Xodimlar bilan bog'lanish qo'shildi)
def get_main_menu(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 iPhone")
    builder.button(text="📱 Samsung")
    builder.button(text="📱 HONOR")
    builder.button(text="📱 Redmi")
    builder.button(text="🎧 Aksessuarlar")
    builder.button(text="📍 Bizning filiallar")
    builder.button(text="👥 Xodimlar bilan bog‘lanish")
    builder.button(text="📞 Operator bilan bog‘lanish")
    
    if user_id in ADMIN_IDS:
        builder.button(text="➕ Yangi mahsulot qo'shish (Admin)")
        builder.adjust(2, 2, 2, 2, 2, 1, 1)
    else:
        builder.adjust(2, 2, 2, 2, 2, 1)
        
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    await message.answer(
        "Assalomu alaykum! Airmax Mobile do'konining elektron katalogiga xush kelibsiz. Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu(user_id)
    )

# Xodimlar bilan bog'lanish bo'limi
@dp.message(lambda message: message.text == "👥 Xodimlar bilan bog‘lanish")
async def staff_handler(message: types.Message):
    text = (
        "👨‍💼 <b>Airmax Mobile do'koni xodimlari bilan bog'lanish:</b>\n\n"
        "1️⃣ <b>Olloyorov Rustam</b>\n"
        "📞 Tel: +998 88 505 95 95\n\n"
        "2️⃣ <b>Olloyorov Islombek</b>\n"
        "📞 Tel: +998 88 359 60 60\n\n"
        "3️⃣ <b>Safarboyev Muxtor</b>\n"
        "📞 Tel: +998 95 776 02 22\n\n"
        "4️⃣ <b>Erkayev Alibek</b>\n"
        "📞 Tel: +998 95 775 48 44\n\n"
        "<i>Kerakli xodimning raqamiga qo'ng'iroq qilib yoki yozib bog'lanishingiz mumkin!</i>"
    )
    await message.answer(text, parse_mode="HTML")

# Filiallar menyusi
@dp.message(lambda message: message.text == "📍 Bizning filiallar")
async def branches_handler(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 1-Filial (Markaziy)")
    builder.button(text="📍 2-Filial")
    builder.button(text="📍 3-Filial")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1, 1, 1, 1)
    await message.answer("Bizning filiallarimizdan birini tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text == "📍 1-Filial (Markaziy)")
async def branch_1(message: types.Message):
    text = (
        "🏢 <b>Airmax Mobile — 1-Filial (Markaziy)</b>\n\n"
        "📍 <b>Ko'cha nomi:</b> Toshkent sh., Chilonzor tumani, Bunyodkor ko'chasi, 15-uy\n"
        "👨‍💼 <b>Filial xodimi:</b> Jamshid aka\n"
        "📞 <b>Telefon raqami:</b> +998 90 111-11-11"
    )
    await message.answer(text, parse_mode="HTML")
    await message.answer_location(latitude=41.2995, longitude=69.2401)

@dp.message(lambda message: message.text == "📍 2-Filial")
async def branch_2(message: types.Message):
    text = (
        "🏢 <b>Airmax Mobile — 2-Filial</b>\n\n"
        "📍 <b>Ko'cha nomi:</b> Toshkent sh., Yunusobod tumani, Amir Temur shoh ko'chasi, 42-uy\n"
        "👨‍💼 <b>Filial xodimi:</b> Asqar aka\n"
        "📞 <b>Telefon raqami:</b> +998 90 222-22-22"
    )
    await message.answer(text, parse_mode="HTML")
    await message.answer_location(latitude=41.3340, longitude=69.2840)

@dp.message(lambda message: message.text == "📍 3-Filial")
async def branch_3(message: types.Message):
    text = (
        "🏢 <b>Airmax Mobile — 3-Filial</b>\n\n"
        "📍 <b>Ko'cha nomi:</b> Toshkent sh., Shayxontohur tumani, Beruniy ko'chasi, 8-uy\n"
        "👨‍💼 <b>Filial xodimi:</b> Rustam aka\n"
        "📞 <b>Telefon raqami:</b> +998 90 333-33-33"
    )
    await message.answer(text, parse_mode="HTML")
    await message.answer_location(latitude=41.3250, longitude=69.2150)

# iPhone bo'limi
@dp.message(lambda message: message.text == "📱 iPhone")
async def iphone_menu(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 B/U iPhone")
    builder.button(text="✨ Yangi iPhone")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 1)
    await message.answer("iPhone bo'limini tanladingiz. Holatini tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text == "✨ Yangi iPhone")
async def new_iphone_handler(message: types.Message):
    await message.answer("✨ Yangi iPhone modellari hozircha sotuvda yo'q. **Tez kunda qo'shiladi!**", parse_mode="HTML")

@dp.message(lambda message: message.text == "📦 B/U iPhone")
async def bu_iphone_models(message: types.Message):
    builder = ReplyKeyboardBuilder()
    models = [
        "iPhone 11", "iPhone 12", "iPhone 12 Pro", "iPhone 12 Pro Max",
        "iPhone 13", "iPhone 13 Pro", "iPhone 13 Pro Max",
        "iPhone 14", "iPhone 14 Pro", "iPhone 14 Pro Max",
        "iPhone 15", "iPhone 15 Pro", "iPhone 15 Pro Max",
        "iPhone 16", "iPhone 16 Pro", "iPhone 16 Pro Max",
        "iPhone 17", "iPhone 17 Pro", "iPhone 17 Pro Max",
        "iPhone 18 Pro", "iPhone 18 Pro Max"
    ]
    for model in models:
        builder.button(text=model)
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1)
    await message.answer("Kerakli B/U modelni tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text == "⬅️ Orqaga")
async def back_handler(message: types.Message):
    await message.answer("Bosh menyu:", reply_markup=get_main_menu(message.from_user.id))

# Mahsulot qo'shish jarayoni
@dp.message(lambda message: message.text == "➕ Yangi mahsulot qo'shish (Admin)")
async def start_add_phone(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Kechirasiz, bu buyruq faqat adminlar uchun!")
        return

    builder = ReplyKeyboardBuilder()
    builder.button(text="iPhone (B/U)")
    builder.button(text="Samsung")
    builder.button(text="HONOR")
    builder.button(text="Redmi")
    builder.button(text="Aksessuarlar")
    builder.adjust(2, 2, 1)
    await message.answer("Mahsulot kategoriyasini tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AddPhone.category)

@dp.message(AddPhone.category)
async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Mahsulot nomini yuboring (masalan: iPhone 14 Pro):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddPhone.name)

@dp.message(AddPhone.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Xotirasini yuboring (masalan: 256 GB):")
    await state.set_state(AddPhone.memory)

@dp.message(AddPhone.memory)
async def process_memory(message: types.Message, state: FSMContext):
    await state.update_data(memory=message.text)
    await message.answer("Battery Health miqdorini yuboring (masalan: 90%):")
    await state.set_state(AddPhone.battery)

@dp.message(AddPhone.battery)
async def process_battery(message: types.Message, state: FSMContext):
    await state.update_data(battery=message.text)
    await message.answer("Rangini yuboring (masalan: Space Black):")
    await state.set_state(AddPhone.color)

@dp.message(AddPhone.color)
async def process_color(message: types.Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer("Holatini yuboring (masalan: Ideal / Karobka bor):")
    await state.set_state(AddPhone.condition)

@dp.message(AddPhone.condition)
async def process_condition(message: types.Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Narxini yuboring (masalan: $850):")
    await state.set_state(AddPhone.price)

@dp.message(AddPhone.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Mavjud sonini (qoldiqni) raqamda yuboring (masalan: 2):")
    await state.set_state(AddPhone.quantity)

@dp.message(AddPhone.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("Iltimos, sonini faqat raqam bilan yuboring:")
        return
    await state.update_data(quantity=quantity)
    await message.answer("Endi mahsulotning rasmini yuboring:")
    await state.set_state(AddPhone.photo)

@dp.message(AddPhone.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Iltimos, rasm (foto) ko'rinishida yuboring:")
        return

    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    data = await state.get_data()

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO phones (category, name, memory, battery, color, condition, price, quantity, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['category'], data['name'], data['memory'], data['battery'], data['color'], data['condition'], data['price'], data['quantity'], data['photo']))
    conn.commit()
    
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    await state.clear()
    await message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi va barcha obunachilarga xabar yuborildi!", reply_markup=get_main_menu(message.from_user.id))

    notification_text = (
        f"🚨 <b>DIQQAT! Yangi mahsulot qo'shildi!</b> 🚨\n\n"
        f"📱 <b>{data['name']}</b>\n"
        f"📂 Bo'lim: {data['category']}\n"
        f"💾 Xotira: {data['memory']}\n"
        f"🔋 Battery: {data['battery']}\n"
        f"🎨 Rangi: {data['color']}\n"
        f"🛠 Holati: {data['condition']}\n"
        f"💰 Narxi: {data['price']}\n"
        f"📦 Qoldiq: {data['quantity']} ta\n\n"
        f"❗️ <b>Kelishadigan joyi bor</b> ❗️\n\n"
        f"👉 Ko'rish uchun botga kiring!"
    )

    for user in users:
        u_id = user[0]
        try:
            if photo_id and photo_id != 'none':
                await bot.send_photo(chat_id=u_id, photo=photo_id, caption=notification_text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=u_id, text=notification_text, parse_mode="HTML")
            await asyncio.sleep(0.1)
        except Exception as e:
            logging.info(f"Foydalanuvchiga yuborilmadi {u_id}: {e}")

iphone_models_list = [
    "iPhone 11", "iPhone 12", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13", "iPhone 13 Pro", "iPhone 13 Pro Max",
    "iPhone 14", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Pro", "iPhone 15 Pro Max",
    "iPhone 16", "iPhone 16 Pro", "iPhone 16 Pro Max",
    "iPhone 17", "iPhone 17 Pro", "iPhone 17 Pro Max",
    "iPhone 18 Pro", "iPhone 18 Pro Max"
]

@dp.message(lambda message: message.text in iphone_models_list)
async def show_iphone_model_products(message: types.Message):
    model_name = message.text
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, memory, battery, color, condition, price, quantity, photo FROM phones WHERE name LIKE ?", (f"%{model_name}%",))
    products = cursor.fetchall()
    conn.close()

    if not products:
        await message.answer(f"Hozircha <b>{model_name}</b> bo'yicha e'lonlar mavjud emas.", parse_mode="HTML")
        return

    for prod in products:
        prod_id, name, memory, battery, color, condition, price, quantity, photo = prod
        text = (
            f"📱 <b>{name}</b>\n"
            f"💾 Xotira: {memory}\n"
            f"🔋 Battery: {battery}\n"
            f"🎨 Rangi: {color}\n"
            f"🛠 Holati: {condition}\n"
            f"💰 Narxi: {price}\n"
            f"📦 Qoldiq: {quantity} ta\n\n"
            f"❗️ <b>Kelishadigan joyi bor</b> ❗️"
        )
        
        inline_builder = InlineKeyboardBuilder()
        inline_builder.button(text="🗑 Sotilgan (O'chirish)", callback_data=f"del_{prod_id}")
        
        if photo and photo != 'none':
            await message.answer_photo(photo=photo, caption=text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")

async def show_other_products(message: types.Message, category_name: str):
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, memory, battery, color, condition, price, quantity, photo FROM phones WHERE category=?", (category_name,))
    products = cursor.fetchall()
    conn.close()

    if not products:
        await message.answer(f"Hozircha {category_name} bo'limida mahsulotlar mavjud emas.")
        return

    for prod in products:
        prod_id, name, memory, battery, color, condition, price, quantity, photo = prod
        text = (
            f"📱 <b>{name}</b>\n"
            f"💾 Xotira: {memory}\n"
            f"🔋 Battery: {battery}\n"
            f"🎨 Rangi: {color}\n"
            f"🛠 Holati: {condition}\n"
            f"💰 Narxi: {price}\n"
            f"📦 Qoldiq: {quantity} ta\n\n"
            f"❗️ <b>Kelishadigan joyi bor</b> ❗️"
        )
        
        inline_builder = InlineKeyboardBuilder()
        inline_builder.button(text="🗑 Sotilgan (O'chirish)", callback_data=f"del_{prod_id}")
        
        if photo and photo != 'none':
            await message.answer_photo(photo=photo, caption=text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=inline_builder.as_markup(), parse_mode="HTML")

@dp.message(lambda message: message.text == "📱 Samsung")
async def samsung_handler(message: types.Message):
    await show_other_products(message, "Samsung")

@dp.message(lambda message: message.text == "📱 HONOR")
async def honor_handler(message: types.Message):
    await show_other_products(message, "HONOR")

@dp.message(lambda message: message.text == "📱 Redmi")
async def redmi_handler(message: types.Message):
    await show_other_products(message, "Redmi")

@dp.message(lambda message: message.text == "🎧 Aksessuarlar")
async def accessories_handler(message: types.Message):
    await show_other_products(message, "Aksessuarlar")

@dp.callback_query(lambda c: c.data.startswith("del_"))
async def delete_phone_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Bu amalni faqat adminlar bajara oladi!", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[1])
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM phones WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()
    
    await callback.message.delete()
    await callback.answer("✅ Mahsulot katalogdan o'chirildi!")

@dp.message(lambda message: message.text == "📞 Operator bilan bog‘lanish")
async def contact_handler(message: types.Message):
    await message.answer("Operator bilan bog'lanish uchun: +998 90 000-00-00 ga murojaat qiling.")

async def main():
    print("Xodimlar bo'limi qo'shilgan bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())