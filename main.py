import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import database as db

TOKEN = "8582520793:AAEJw65DPp780yky_wZHlKFyIQJNkJ3GowM"

# 1. SUPER ADMIN: Barcha vakolatlar (Filial, Lokatsiya, Kanal, Xodimlar, Mahsulotlar)
SUPER_ADMIN_ID = 6738533029

# 2. MAHSULOT ADMINI: FAQAT mahsulot qo'shish va o'chirish
PRODUCT_ADMIN_ID = 5156453500

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM holatlari
class SuperAdminState(StatesGroup):
    channel = State()
    branch_name = State()
    branch_location = State()
    staff_name = State()
    staff_phone = State()

class ProductState(StatesGroup):
    category = State()
    name = State()
    memory = State()
    battery = State()
    color = State()
    condition = State()
    price = State()
    quantity = State()
    photo = State()

# Asosiy menyu
def get_main_menu(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 iPhone")
    builder.button(text="📱 Samsung")
    builder.button(text="📱 HONOR")
    builder.button(text="📱 Redmi")
    builder.button(text="🎧 Aksessuarlar")
    builder.button(text="📍 Filial va Lokatsiya")
    builder.button(text="👥 Xodimlar bilan bog‘lanish")
    builder.button(text="📢 Bizning kanal")

    if user_id == SUPER_ADMIN_ID:
        builder.button(text="👑 Super Admin Paneli")
        builder.button(text="📦 Mahsulotlar Paneli")
        builder.adjust(2, 2, 2, 2, 2)
    elif user_id == PRODUCT_ADMIN_ID:
        builder.button(text="📦 Mahsulotlar Paneli")
        builder.adjust(2, 2, 2, 2, 1)
    else:
        builder.adjust(2, 2, 2, 2)

    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()
    conn.close()

    text = "Assalomu alaykum! Do'konimiz botiga xush kelibsiz."
    if uid == SUPER_ADMIN_ID:
        text += "\n\n👑 <b>Siz Super Adminsiz.</b> Do'kon barcha ma'lumotlarini to'liq boshqara olasiz."
    elif uid == PRODUCT_ADMIN_ID:
        text += "\n\n📦 <b>Siz Mahsulot menejerisiz.</b> Faqat mahsulot qo'shish va o'chirish ruxsatingiz bor."

    await message.answer(text, reply_markup=get_main_menu(uid), parse_mode="HTML")

# --- FOYDALANUVCHILAR UCHUN BO'LIMLAR ---

@dp.message(F.text == "📢 Bizning kanal")
async def show_channel(message: types.Message):
    ch = db.get_setting("channel")
    if ch:
        await message.answer(f"📢 <b>Bizning rasmiy kanalimiz:</b>\n👉 {ch}", parse_mode="HTML")
    else:
        await message.answer("Rasmiy kanal havolasi tez orada joylanadi.")

@dp.message(F.text == "📍 Filial va Lokatsiya")
async def show_branch(message: types.Message):
    branch = db.get_setting("branch")
    loc = db.get_setting("location")
    if not branch and not loc:
        await message.answer("Filial ma'lumotlari hozircha mavjud emas.")
        return
    if branch:
        await message.answer(f"🏢 <b>Bizning filial:</b>\n{branch}", parse_mode="HTML")
    if loc:
        lat, lon = loc.split(",")
        await message.answer_location(latitude=float(lat), longitude=float(lon))

@dp.message(F.text == "👥 Xodimlar bilan bog‘lanish")
async def show_staff(message: types.Message):
    staffs = db.get_staff_list()
    if not staffs:
        await message.answer("Xodimlar ro'yxati hali kiritilmagan.")
        return
    text = "👨‍💼 <b>Xodimlarimiz bilan bog'lanish:</b>\n\n"
    for s in staffs:
        text += f"👤 <b>{s['name']}</b>\n📞 Tel: {s['phone']}\n\n"
    await message.answer(text, parse_mode="HTML")

# Katalog ko'rish
@dp.message(F.text.in_(["📱 iPhone", "📱 Samsung", "📱 HONOR", "📱 Redmi", "🎧 Aksessuarlar"]))
async def show_category_products(message: types.Message):
    cat_name = message.text.replace("📱 ", "").replace("🎧 ", "")
    products = db.get_products_by_category(cat_name)
    if not products:
        await message.answer(f"Hozircha <b>{cat_name}</b> bo'limida mahsulot yo'q.", parse_mode="HTML")
        return

    for p in products:
        caption = (
            f"📱 <b>{p['name']}</b>\n"
            f"💾 Xotira: {p['memory']}\n"
            f"🔋 Battery: {p['battery']}\n"
            f"🎨 Rangi: {p['color']}\n"
            f"🛠 Holati: {p['condition']}\n"
            f"💰 Narxi: {p['price']}\n"
            f"📦 Qoldiq: {p['quantity']} ta\n\n"
            f"❗️ <b>Kelishadigan joyi bor</b> ❗️"
        )
        if p['photo_id'] and p['photo_id'] != "none":
            await message.answer_photo(photo=p['photo_id'], caption=caption, parse_mode="HTML")
        else:
            await message.answer(caption, parse_mode="HTML")

# --- SUPER ADMIN BOSHQARUVI (FAQAT 6738533029) ---

@dp.message(F.text == "👑 Super Admin Paneli")
async def super_admin_panel(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        await message.answer("❌ Bu bo'lim faqat Bosh Admin uchun!")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Kanal havolasini sozlash", callback_data="sa_channel")
    builder.button(text="🏢 Filial nomini sozlash", callback_data="sa_branch")
    builder.button(text="📍 Filial Lokatsiyasini yuborish", callback_data="sa_location")
    builder.button(text="➕ Xodim qo'shish", callback_data="sa_add_staff")
    builder.button(text="🗑 Xodimni o'chirish", callback_data="sa_del_staff")
    builder.adjust(1)
    await message.answer("👑 <b>Super Admin boshqaruv paneli:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# Kanalni o'zgartirish
@dp.callback_query(F.data == "sa_channel")
async def sa_ch_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN_ID:
        return
    await call.message.answer("Yangi kanal havolasini yuboring (masalan: https://t.me/kanal yoki @kanal):")
    await state.set_state(SuperAdminState.channel)
    await call.answer()

@dp.message(SuperAdminState.channel)
async def sa_ch_finish(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    db.set_setting("channel", message.text.strip())
    await message.answer("✅ Kanal havolasi muvaffaqiyatli saqlandi!")
    await state.clear()

# Filial nomini kiritish
@dp.callback_query(F.data == "sa_branch")
async def sa_br_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN_ID:
        return
    await call.message.answer("Filial manzili va qisqacha ma'lumotini yozib yuboring:")
    await state.set_state(SuperAdminState.branch_name)
    await call.answer()

@dp.message(SuperAdminState.branch_name)
async def sa_br_finish(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    db.set_setting("branch", message.text.strip())
    await message.answer("✅ Filial manzili saqlandi!")
    await state.clear()

# Lokatsiya yuborish
@dp.callback_query(F.data == "sa_location")
async def sa_loc_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN_ID:
        return
    await call.message.answer("Telegram orqali filialning haqiqiy Geopozitsiyasini (Lokatsiyasini) yuboring:")
    await state.set_state(SuperAdminState.branch_location)
    await call.answer()

@dp.message(SuperAdminState.branch_location, F.location)
async def sa_loc_finish(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    lat = message.location.latitude
    lon = message.location.longitude
    db.set_setting("location", f"{lat},{lon}")
    await message.answer("✅ Filial lokatsiyasi saqlandi!")
    await state.clear()

# Xodim qo'shish
@dp.callback_query(F.data == "sa_add_staff")
async def sa_staff_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != SUPER_ADMIN_ID:
        return
    await call.message.answer("Xodimning ism-sharifini yuboring:")
    await state.set_state(SuperAdminState.staff_name)
    await call.answer()

@dp.message(SuperAdminState.staff_name)
async def sa_staff_name(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    await state.update_data(staff_name=message.text.strip())
    await message.answer("Xodimning telefon raqamini yuboring (masalan: +998 90 123 45 67):")
    await state.set_state(SuperAdminState.staff_phone)

@dp.message(SuperAdminState.staff_phone)
async def sa_staff_phone(message: types.Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    data = await state.get_data()
    db.add_staff(data['staff_name'], message.text.strip())
    await message.answer(f"✅ Xodim <b>{data['staff_name']}</b> ro'yxatga qo'shildi!", parse_mode="HTML")
    await state.clear()

# Xodimni o'chirish
@dp.callback_query(F.data == "sa_del_staff")
async def sa_del_staff_list(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN_ID:
        return
    staffs = db.get_staff_list()
    if not staffs:
        await call.message.answer("O'chirish uchun xodimlar yo'q.")
        await call.answer()
        return
    builder = InlineKeyboardBuilder()
    for s in staffs:
        builder.button(text=f"❌ {s['name']}", callback_data=f"delstaff_{s['id']}")
    builder.adjust(1)
    await call.message.answer("O'chirmoqchi bo'lgan xodimni tanlang:", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("delstaff_"))
async def sa_del_staff_confirm(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN_ID:
        return
    sid = int(call.data.split("_")[1])
    db.delete_staff(sid)
    await call.message.edit_text("✅ Xodim ro'yxatdan o'chirildi!")
    await call.answer()

# --- MAHSULOTLAR PANELI (Ruxsat: 5156453500 va 6738533029) ---

@dp.message(F.text == "📦 Mahsulotlar Paneli")
async def prod_panel_open(message: types.Message):
    if message.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Mahsulot qo'shish", callback_data="pr_add")
    builder.button(text="🗑 Mahsulotni o'chirish", callback_data="pr_del")
    builder.adjust(1)
    await message.answer("📦 <b>Mahsulotlarni boshqarish:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

# Mahsulot qo'shish
@dp.callback_query(F.data == "pr_add")
async def pr_add_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return
    
    builder = ReplyKeyboardBuilder()
    builder.button(text="iPhone")
    builder.button(text="Samsung")
    builder.button(text="HONOR")
    builder.button(text="Redmi")
    builder.button(text="Aksessuarlar")
    builder.adjust(2, 2, 1)

    await call.message.answer("Mahsulot kategoriyasini tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(ProductState.category)
    await call.answer()

@dp.message(ProductState.category)
async def pr_cat(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Mahsulot nomini kiriting (masalan: iPhone 14 Pro):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ProductState.name)

@dp.message(ProductState.name)
async def pr_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Xotirasini kiriting (masalan: 128 GB yoki -):")
    await state.set_state(ProductState.memory)

@dp.message(ProductState.memory)
async def pr_mem(message: types.Message, state: FSMContext):
    await state.update_data(memory=message.text)
    await message.answer("Battery Health (masalan: 88% yoki Yangi):")
    await state.set_state(ProductState.battery)

@dp.message(ProductState.battery)
async def pr_bat(message: types.Message, state: FSMContext):
    await state.update_data(battery=message.text)
    await message.answer("Rangini kiriting (masalan: Deep Purple):")
    await state.set_state(ProductState.color)

@dp.message(ProductState.color)
async def pr_col(message: types.Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer("Holatini kiriting (masalan: Ideal / Karobka bor):")
    await state.set_state(ProductState.condition)

@dp.message(ProductState.condition)
async def pr_cond(message: types.Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Narxini kiriting (masalan: 720$):")
    await state.set_state(ProductState.price)

@dp.message(ProductState.price)
async def pr_prc(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Mavjud sonini raqamda yuboring (masalan: 1):")
    await state.set_state(ProductState.quantity)

@dp.message(ProductState.quantity)
async def pr_qty(message: types.Message, state: FSMContext):
    try:
        q = int(message.text)
    except ValueError:
        await message.answer("Iltimos, sonini faqat butun raqamda kiriting:")
        return
    await state.update_data(quantity=q)
    await message.answer("Endi mahsulot fotosuratini (rasmini) yuboring:")
    await state.set_state(ProductState.photo)

@dp.message(ProductState.photo)
async def pr_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Iltimos, rasmni foto ko'rinishida yuboring:")
        return
    
    photo_id = message.photo[-1].file_id
    data = await state.get_data()

    db.add_product(
        category=data['category'],
        name=data['name'],
        memory=data['memory'],
        battery=data['battery'],
        color=data['color'],
        condition=data['condition'],
        price=data['price'],
        quantity=data['quantity'],
        photo_id=photo_id
    )

    await message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=get_main_menu(message.from_user.id))
    await state.clear()

# Mahsulotni o'chirish
@dp.callback_query(F.data == "pr_del")
async def pr_del_list(call: types.CallbackQuery):
    if call.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return
    prods = db.get_all_products()
    if not prods:
        await call.message.answer("O'chirish uchun mahsulotlar mavjud emas.")
        await call.answer()
        return

    builder = InlineKeyboardBuilder()
    for p in prods:
        builder.button(text=f"❌ {p['name']} ({p['price']})", callback_data=f"delp_{p['id']}")
    builder.adjust(1)
    await call.message.answer("O'chirmoqchi bo'lgan mahsulotingizni tanlang:", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("delp_"))
async def pr_del_confirm(call: types.CallbackQuery):
    if call.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return
    pid = int(call.data.split("_")[1])
    db.delete_product(pid)
    await call.message.edit_text("✅ Mahsulot bazadan muvaffaqiyatli o'chirildi!")
    await call.answer()

async def main():
    db.init_db()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
