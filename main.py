import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import database as db

# Bot tokeni
TOKEN = "8582520793:AAEJw65DPp780yky_wZHlKFyIQJNkJ3GowM"

# Ruxsat berilgan ID lar
SUPER_ADMIN_ID = 6738533029  # Filial, lokatsiya, kanal, xodimlar
PRODUCT_ADMIN_ID = 5156453500  # Mahsulot qo'shish va o'chirish

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumot kiritish holatlari (FSM)
class SettingsState(StatesGroup):
    waiting_channel = State()
    waiting_branch_name = State()
    waiting_location = State()

class ProductState(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_desc = State()
    waiting_photo = State()

# Klaviaturalar
def get_main_menu(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Mahsulotlar")
    builder.button(text="📍 Filial va Lokatsiya")
    builder.button(text="📢 Bizning kanal")

    if user_id == SUPER_ADMIN_ID:
        builder.button(text="⚙️ Super Admin Panel")
        builder.button(text="📦 Mahsulotlar Paneli")
    elif user_id == PRODUCT_ADMIN_ID:
        builder.button(text="📦 Mahsulotlar Paneli")

    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    text = "Assalomu alaykum! Do'konimiz botiga xush kelibsiz."
    if message.from_user.id == SUPER_ADMIN_ID:
        text += "\n\n👑 *Siz Super Adminsiz.* Filial, lokatsiya va kanalni boshqara olasiz."
    elif message.from_user.id == PRODUCT_ADMIN_ID:
        text += "\n\n📦 *Siz Mahsulot menejerisiz.* Mahsulot qo'shish va o'chirish huquqingiz bor."

    await message.answer(text, reply_markup=get_main_menu(message.from_user.id), parse_mode="Markdown")

# --- FOYDALANUVCHI BO'LIMLARI ---

@dp.message(F.text == "📢 Bizning kanal")
async def show_channel(message: types.Message):
    channel = db.get_setting("channel")
    if channel:
        await message.answer(f"📢 Rasmiy kanalimiz: {channel}")
    else:
        await message.answer("Kanal hali belgilanmagan.")

@dp.message(F.text == "📍 Filial va Lokatsiya")
async def show_branch(message: types.Message):
    branch = db.get_setting("branch")
    loc = db.get_setting("location")
    
    if not branch and not loc:
        await message.answer("Filial ma'lumotlari tez orada qo'shiladi.")
        return

    if branch:
        await message.answer(f"🏢 Filialimiz: {branch}")
    if loc:
        lat, lon = loc.split(",")
        await message.answer_location(latitude=float(lat), longitude=float(lon))

@dp.message(F.text == "📱 Mahsulotlar")
async def show_products(message: types.Message):
    products = db.get_products()
    if not products:
        await message.answer("Hozircha mahsulotlar mavjud emas.")
        return

    for item in products:
        p_id, name, price, desc, photo_id = item
        caption = f"📱 *{name}*\n💰 Narxi: {price}\nℹ️ Ma'lumot: {desc}"
        if photo_id:
            await message.answer_photo(photo=photo_id, caption=caption, parse_mode="Markdown")
        else:
            await message.answer(caption, parse_mode="Markdown")

# --- SUPER ADMIN (6738533029) BOSHQARUVI ---

@dp.message(F.text == "⚙️ Super Admin Panel")
async def super_admin_menu(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Kanalni o'zgartirish", callback_data="set_channel")
    builder.button(text="🏢 Filial nomini kiritish", callback_data="set_branch")
    builder.button(text="📍 Lokatsiya yuborish", callback_data="set_location")
    builder.adjust(1)
    
    await message.answer("Boshqarish uchun bo'limni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "set_channel")
async def set_channel_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    await callback.message.answer("Yangi kanal havolasini yuboring (masalan: @kanal_nomi):")
    await state.set_state(SettingsState.waiting_channel)
    await callback.answer()

@dp.message(SettingsState.waiting_channel)
async def save_channel(message: types.Message, state: FSMContext):
    db.set_setting("channel", message.text.strip())
    await message.answer("✅ Kanal muvaffaqiyatli saqlandi!")
    await state.clear()

@dp.callback_query(F.data == "set_branch")
async def set_branch_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    await callback.message.answer("Filial manzili va ish vaqtini matn ko'rinishida yuboring:")
    await state.set_state(SettingsState.waiting_branch_name)
    await callback.answer()

@dp.message(SettingsState.waiting_branch_name)
async def save_branch(message: types.Message, state: FSMContext):
    db.set_setting("branch", message.text.strip())
    await message.answer("✅ Filial ma'lumoti saqlandi!")
    await state.clear()

@dp.callback_query(F.data == "set_location")
async def set_loc_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    await callback.message.answer("Telegram orqali do'kon Lokatsiyasini (geopozitsiya) yuboring:")
    await state.set_state(SettingsState.waiting_location)
    await callback.answer()

@dp.message(SettingsState.waiting_location, F.location)
async def save_loc(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    db.set_setting("location", f"{lat},{lon}")
    await message.answer("✅ Yangi lokatsiya muvaffaqiyatli saqlandi!")
    await state.clear()

# --- MAHSULOTLAR PANELI (5156453500 va 6738533029) ---

@dp.message(F.text == "📦 Mahsulotlar Paneli")
async def product_admin_menu(message: types.Message):
    if message.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi mahsulot qo'shish", callback_data="add_prod")
    builder.button(text="🗑 Mahsulotni o'chirish", callback_data="del_prod_list")
    builder.adjust(1)

    await message.answer("Mahsulotlar bo'limi:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "add_prod")
async def add_product_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return
    await callback.message.answer("Mahsulot nomini yuboring (masalan: iPhone 15 Pro 128GB):")
    await state.set_state(ProductState.waiting_name)
    await callback.answer()

@dp.message(ProductState.waiting_name)
async def prod_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Mahsulot narxini yozing (masalan: 950$ yoki 12,000,000 so'm):")
    await state.set_state(ProductState.waiting_price)

@dp.message(ProductState.waiting_price)
async def prod_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Mahsulot haqida qisqacha tavsif yozing (Holati, rangi, kafolat):")
    await state.set_state(ProductState.waiting_desc)

@dp.message(ProductState.waiting_desc)
async def prod_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Mahsulot rasmini yuboring (agar rasm bo'lmasa, 'yoq' deb yozing):")
    await state.set_state(ProductState.waiting_photo)

@dp.message(ProductState.waiting_photo)
async def prod_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id if message.photo else None

    db.add_product(
        name=data['name'],
        price=data['price'],
        description=data['description'],
        photo_id=photo_id
    )

    await message.answer(f"✅ '{data['name']}' muvaffaqiyatli saqlandi!")
    await state.clear()

@dp.callback_query(F.data == "del_prod_list")
async def del_product_list(callback: types.CallbackQuery):
    if callback.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return

    products = db.get_products()
    if not products:
        await callback.message.answer("O'chirishga mahsulot yo'q.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for p_id, name, price, _, _ in products:
        builder.button(text=f"❌ {name} ({price})", callback_data=f"del_{p_id}")
    builder.adjust(1)

    await callback.message.answer("O'chirmoqchi bo'lgan mahsulotingizni tanlang:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("del_"))
async def del_product_confirm(callback: types.CallbackQuery):
    if callback.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return

    p_id = int(callback.data.split("_")[1])
    db.delete_product(p_id)
    await callback.message.edit_text("✅ Mahsulot o'chirib tashlandi!")
    await callback.answer()

async def main():
    db.init_db()
    print("Do'kon boti muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
