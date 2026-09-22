import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import database as db

# SIZNING TOKEN VA ID RAQAMLARINGIZ (TEGILMADI)
TOKEN = "8582520793:AAEJw65DPp780yky_wZHlKFyIQJNkJ3GowM"
SUPER_ADMIN_ID = 6738533029  # To'liq boshqaruv
PRODUCT_ADMIN_ID = 5156453500  # Faqat mahsulot boshqaruvi

IPHONE_MODELS = [
    "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
    "iPhone 12", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13", "iPhone 13 Pro", "iPhone 13 Pro Max",
    "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max",
    "iPhone 16", "iPhone 16 Plus", "iPhone 16 Pro", "iPhone 16 Pro Max",
    "iPhone 17", "iPhone 17 Air", "iPhone 17 Pro", "iPhone 17 Pro Max",
    "iPhone 18", "iPhone 18 Air", "iPhone 18 Pro", "iPhone 18 Pro Max"
]

ACCESSORIES_TYPES = [
    "Zaryadchik", "Sichqoncha (Mishka)", "Quloqchin (Naushnik)", 
    "Kalonka", "Klaviatura", "Holder (Ushlagich)", 
    "Powerbank", "Chexol", "Himoya oynasi"
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SuperAdminState(StatesGroup):
    channel = State()
    branch_name = State()
    branch_location = State()
    staff_name = State()
    staff_phone = State()

class ProductState(StatesGroup):
    category = State()
    subcategory = State()
    model = State()
    name = State()
    memory = State()
    battery = State()
    color = State()
    condition = State()
    price = State()
    quantity = State()
    photo = State()

# --- KLAVIATURALAR ---
def get_main_menu(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📦 Mahsulotlar")
    builder.button(text="📍 Filial va Lokatsiya")
    builder.button(text="👥 Xodimlar")
    builder.button(text="📢 Bizning kanal")

    if user_id == SUPER_ADMIN_ID:
        builder.button(text="👑 Super Admin Paneli")
        builder.button(text="⚙️ Mahsulotlar Paneli")
        builder.adjust(1, 2, 1, 2)
    elif user_id == PRODUCT_ADMIN_ID:
        builder.button(text="⚙️ Mahsulotlar Paneli")
        builder.adjust(1, 2, 1, 1)
    else:
        builder.adjust(1, 2, 1)

    return builder.as_markup(resize_keyboard=True)

def get_category_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 iPhone")
    builder.button(text="📱 Samsung")
    builder.button(text="📱 HONOR")
    builder.button(text="📱 Redmi")
    builder.button(text="🎧 Aksessuarlar")
    builder.button(text="🔙 Bosh menyuga qaytish")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

def get_cancel_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)

def format_product_caption(p):
    return (
        f"📱 <b>{p['name']}</b>\n"
        f"💾 Xotira: {p['memory']}\n"
        f"🔋 Battery: {p['battery']}\n"
        f"🎨 Rangi: {p['color']}\n"
        f"🛠 Holati: {p['condition']}\n"
        f"💰 Narxi: {p['price']}\n"
        f"📦 Qoldiq: {p['quantity']} ta\n\n"
        f"❗️ <b>Kelishadigan joyi bor</b> ❗️"
    )

# --- BEKOR QILISH VA BOSH MENYU ---
@dp.message(F.text.in_(["❌ Bekor qilish", "🔙 Bosh menyuga qaytish"]))
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=get_main_menu(message.from_user.id))

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    db.add_user(uid)
    text = "Assalomu alaykum! Airmax Mobile do'koniga xush kelibsiz."
    await message.answer(text, reply_markup=get_main_menu(uid))

# --- FOYDALANUVCHI BO'LIMLARI ---
@dp.message(F.text == "📦 Mahsulotlar")
async def show_categories(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Kategoriyani tanlang:", reply_markup=get_category_menu())

# iPhone ko'rish
@dp.message(F.text == "📱 iPhone")
async def show_iphone_subcategories(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="Yangi", callback_data="viewsub_Yangi")
    builder.button(text="B/U", callback_data="viewsub_BU")
    builder.adjust(2)
    await message.answer("Holatini tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("viewsub_"))
async def show_iphone_models(call: types.CallbackQuery):
    subcat = call.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    for idx, model in enumerate(IPHONE_MODELS):
        builder.button(text=model, callback_data=f"viewmod_{subcat}_{idx}")
    builder.adjust(2)
    await call.message.edit_text(f"{subcat} iPhone modellarini tanlang:", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("viewmod_"))
async def show_iphone_final(call: types.CallbackQuery):
    data = call.data.split("_")
    subcat = data[1]
    model = IPHONE_MODELS[int(data[2])]
    products = db.get_products_by_model("iPhone", subcat, model)
    
    if not products:
        await call.message.answer(f"Hozircha <b>{model} ({subcat})</b> bo'yicha mahsulot yo'q. Tez orada qo'shiladi ⏳", parse_mode="HTML")
        await call.answer()
        return

    for p in products:
        caption = format_product_caption(p)
        if p['photo_id'] and p['photo_id'] != "none":
            await call.message.answer_photo(photo=p['photo_id'], caption=caption, parse_mode="HTML")
        else:
            await call.message.answer(caption, parse_mode="HTML")
    await call.answer()

# Aksessuarlar ko'rish
@dp.message(F.text == "🎧 Aksessuarlar")
async def show_accessories_types(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for idx, acc in enumerate(ACCESSORIES_TYPES):
        builder.button(text=acc, callback_data=f"viewacc_{idx}")
    builder.adjust(2)
    await message.answer("Aksessuar turini tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("viewacc_"))
async def show_accessories_final(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    acc_type = ACCESSORIES_TYPES[idx]
    products = db.get_products_by_subcategory("Aksessuarlar", acc_type)
    
    if not products:
        await call.message.answer(f"Hozircha <b>{acc_type}</b> bo'yicha mahsulot yo'q. Tez orada qo'shiladi ⏳", parse_mode="HTML")
        await call.answer()
        return

    for p in products:
        caption = format_product_caption(p)
        if p['photo_id'] and p['photo_id'] != "none":
            await call.message.answer_photo(photo=p['photo_id'], caption=caption, parse_mode="HTML")
        else:
            await call.message.answer(caption, parse_mode="HTML")
    await call.answer()

# Boshqa telefonlar
@dp.message(F.text.in_(["📱 Samsung", "📱 HONOR", "📱 Redmi"]))
async def show_category_products(message: types.Message, state: FSMContext):
    await state.clear()
    cat_name = message.text.replace("📱 ", "")
    products = db.get_products_by_category(cat_name)
    if not products:
        await message.answer(f"Hozircha <b>{cat_name}</b> bo'limida mahsulot yo'q. Tez orada qo'shiladi ⏳", parse_mode="HTML")
        return

    for p in products:
        caption = format_product_caption(p)
        if p['photo_id'] and p['photo_id'] != "none":
            await message.answer_photo(photo=p['photo_id'], caption=caption, parse_mode="HTML")
        else:
            await message.answer(caption, parse_mode="HTML")

# --- QO'SHIMCHA MA'LUMOT BO'LIMLARI ---
@dp.message(F.text == "📢 Bizning kanal")
async def show_channel(message: types.Message, state: FSMContext):
    await state.clear()
    ch = db.get_setting("channel")
    if ch:
        await message.answer(f"📢 <b>Bizning rasmiy kanalimiz:</b>\n👉 {ch}", parse_mode="HTML")
    else:
        await message.answer("Rasmiy kanal havolasi kiritilmagan.")

@dp.message(F.text == "📍 Filial va Lokatsiya")
async def show_branch(message: types.Message, state: FSMContext):
    await state.clear()
    branch = db.get_setting("branch")
    loc = db.get_setting("location")
    if not branch and not loc:
        await message.answer("Filial ma'lumotlari hali kiritilmagan.")
        return
    if branch:
        await message.answer(f"🏢 <b>Bizning filial:</b>\n{branch}", parse_mode="HTML")
    if loc:
        lat, lon = loc.split(",")
        await message.answer_location(latitude=float(lat), longitude=float(lon))

@dp.message(F.text == "👥 Xodimlar")
async def show_staff(message: types.Message, state: FSMContext):
    await state.clear()
    staffs = db.get_staff_list()
    if not staffs:
        await message.answer("Xodimlar ro'yxati hali kiritilmagan.")
        return
    text = "👨‍💼 <b>Xodimlarimiz bilan bog'lanish:</b>\n\n"
    for s in staffs:
        text += f"👤 <b>{s['name']}</b>\n📞 Tel: {s['phone']}\n\n"
    await message.answer(text, parse_mode="HTML")

# --- SUPER ADMIN PANELI ---
@dp.message(F.text == "👑 Super Admin Paneli")
async def super_admin_panel(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Bot statistikasi", callback_data="sa_stats")
    builder.button(text="📢 Kanalni sozlash", callback_data="sa_channel")
    builder.button(text="🏢 Filial nomini sozlash", callback_data="sa_branch")
    builder.button(text="📍 Lokatsiyani yuborish", callback_data="sa_location")
    builder.button(text="➕ Xodim qo'shish", callback_data="sa_add_staff")
    builder.button(text="🗑 Xodimni o'chirish", callback_data="sa_del_staff")
    builder.adjust(1)
    await message.answer("👑 <b>Super Admin Paneli:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sa_stats")
async def sa_show_stats(call: types.CallbackQuery):
    count = db.get_users_count()
    await call.message.answer(f"📊 <b>Botdan foydalanuvchilar soni:</b> {count} ta odam.", parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "sa_channel")
async def sa_ch_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Yangi kanal havolasini yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(SuperAdminState.channel)
    await call.answer()

@dp.message(SuperAdminState.channel)
async def sa_ch_finish(message: types.Message, state: FSMContext):
    db.set_setting("channel", message.text.strip())
    await message.answer("✅ Kanal saqlandi!", reply_markup=get_main_menu(message.from_user.id))
    await state.clear()

@dp.callback_query(F.data == "sa_branch")
async def sa_br_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Filial manzilini yozing:", reply_markup=get_cancel_menu())
    await state.set_state(SuperAdminState.branch_name)
    await call.answer()

@dp.message(SuperAdminState.branch_name)
async def sa_br_finish(message: types.Message, state: FSMContext):
    db.set_setting("branch", message.text.strip())
    await message.answer("✅ Filial manzili saqlandi!", reply_markup=get_main_menu(message.from_user.id))
    await state.clear()

@dp.callback_query(F.data == "sa_location")
async def sa_loc_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Telegram orqali Lokatsiyani yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(SuperAdminState.branch_location)
    await call.answer()

@dp.message(SuperAdminState.branch_location, F.location)
async def sa_loc_finish(message: types.Message, state: FSMContext):
    lat, lon = message.location.latitude, message.location.longitude
    db.set_setting("location", f"{lat},{lon}")
    await message.answer("✅ Lokatsiya saqlandi!", reply_markup=get_main_menu(message.from_user.id))
    await state.clear()

@dp.callback_query(F.data == "sa_add_staff")
async def sa_staff_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Xodim ismini yuboring:", reply_markup=get_cancel_menu())
    await state.set_state(SuperAdminState.staff_name)
    await call.answer()

@dp.message(SuperAdminState.staff_name)
async def sa_staff_name(message: types.Message, state: FSMContext):
    await state.update_data(staff_name=message.text.strip())
    await message.answer("Xodim telefon raqamini yuboring:")
    await state.set_state(SuperAdminState.staff_phone)

@dp.message(SuperAdminState.staff_phone)
async def sa_staff_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.add_staff(data['staff_name'], message.text.strip())
    await message.answer("✅ Xodim qo'shildi!", reply_markup=get_main_menu(message.from_user.id))
    await state.clear()

@dp.callback_query(F.data == "sa_del_staff")
async def sa_del_staff_list(call: types.CallbackQuery):
    staffs = db.get_staff_list()
    if not staffs:
        await call.answer("Xodimlar yo'q.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for s in staffs:
        builder.button(text=f"❌ {s['name']}", callback_data=f"delstaff_{s['id']}")
    builder.adjust(1)
    await call.message.answer("O'chirish uchun tanlang:", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("delstaff_"))
async def sa_del_staff_confirm(call: types.CallbackQuery):
    db.delete_staff(int(call.data.split("_")[1]))
    await call.message.edit_text("✅ Xodim o'chirildi!")

# --- MAHSULOTLAR PANELI ---
@dp.message(F.text == "⚙️ Mahsulotlar Paneli")
async def prod_panel_open(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in [SUPER_ADMIN_ID, PRODUCT_ADMIN_ID]:
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Mahsulot qo'shish", callback_data="pr_add")
    builder.button(text="🗑 Mahsulotni o'chirish", callback_data="pr_del")
    builder.adjust(1)
    await message.answer("📦 <b>Boshqaruv paneli:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "pr_add")
async def pr_add_start(call: types.CallbackQuery, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    builder.button(text="iPhone")
    builder.button(text="Samsung")
    builder.button(text="HONOR")
    builder.button(text="Redmi")
    builder.button(text="Aksessuarlar")
    builder.button(text="❌ Bekor qilish")
    builder.adjust(2, 2, 1, 1)
    await call.message.answer("Kategoriyani tanlang:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(ProductState.category)
    await call.answer()

@dp.message(ProductState.category)
async def pr_cat(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    
    if message.text == "iPhone":
        builder = InlineKeyboardBuilder()
        builder.button(text="Yangi", callback_data="prsub_Yangi")
        builder.button(text="B/U", callback_data="prsub_BU")
        builder.adjust(2)
        await message.answer("Holatini tanlang:", reply_markup=builder.as_markup())
        await state.set_state(ProductState.subcategory)
        
    elif message.text == "Aksessuarlar":
        builder = InlineKeyboardBuilder()
        for idx, acc in enumerate(ACCESSORIES_TYPES):
            builder.button(text=acc, callback_data=f"pracc_{idx}")
        builder.adjust(2)
        await message.answer("Aksessuar turini tanlang:", reply_markup=builder.as_markup())
        await state.set_state(ProductState.subcategory)
        
    else:
        await state.update_data(subcategory=None, model=None)
        await message.answer("Mahsulot nomini kiriting:", reply_markup=get_cancel_menu())
        await state.set_state(ProductState.name)

# iPhone holatini tanlaganda
@dp.callback_query(ProductState.subcategory, F.data.startswith("prsub_"))
async def pr_subcat_iphone(call: types.CallbackQuery, state: FSMContext):
    subcat = call.data.split("_")[1]
    await state.update_data(subcategory=subcat)
    
    builder = InlineKeyboardBuilder()
    for idx, model in enumerate(IPHONE_MODELS):
        builder.button(text=model, callback_data=f"prmod_{idx}")
    builder.adjust(2)
    
    await call.message.edit_text("Modelni tanlang:", reply_markup=builder.as_markup())
    await state.set_state(ProductState.model)
    await call.answer()

# iPhone modelini tanlaganda
@dp.callback_query(ProductState.model, F.data.startswith("prmod_"))
async def pr_model_iphone(call: types.CallbackQuery, state: FSMContext):
    idx = int(call.data.split("_")[1])
    model = IPHONE_MODELS[idx]
    await state.update_data(model=model)
    
    await call.message.delete()
    await call.message.answer(f"Siz {model} tanladingiz.\nTo'liq nomini kiriting (masalan, iPhone 15 Pro Max 256GB):", reply_markup=get_cancel_menu())
    await state.set_state(ProductState.name)
    await call.answer()

# Aksessuar turini tanlaganda
@dp.callback_query(ProductState.subcategory, F.data.startswith("pracc_"))
async def pr_subcat_acc(call: types.CallbackQuery, state: FSMContext):
    idx = int(call.data.split("_")[1])
    acc_type = ACCESSORIES_TYPES[idx]
    await state.update_data(subcategory=acc_type, model=None)
    
    await call.message.delete()
    await call.message.answer(f"Siz {acc_type} tanladingiz.\nMahsulot nomini kiriting (masalan, Hoco AirPods Pro 2):", reply_markup=get_cancel_menu())
    await state.set_state(ProductState.name)
    await call.answer()

@dp.message(ProductState.name)
async def pr_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Xotirasini kiriting (Aksessuar yoki oddiy telefon bo'lsa '-' yozing):")
    await state.set_state(ProductState.memory)

@dp.message(ProductState.memory)
async def pr_mem(message: types.Message, state: FSMContext):
    await state.update_data(memory=message.text)
    await message.answer("Battery Health (Aksessuar bo'lsa '-' yozing):")
    await state.set_state(ProductState.battery)

@dp.message(ProductState.battery)
async def pr_bat(message: types.Message, state: FSMContext):
    await state.update_data(battery=message.text)
    await message.answer("Rangini kiriting:")
    await state.set_state(ProductState.color)

@dp.message(ProductState.color)
async def pr_col(message: types.Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer("Holatini kiriting (masalan, Ideal, Yangi):")
    await state.set_state(ProductState.condition)

@dp.message(ProductState.condition)
async def pr_cond(message: types.Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Narxini kiriting (masalan, $1000 yoki 150.000 so'm):")
    await state.set_state(ProductState.price)

@dp.message(ProductState.price)
async def pr_prc(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Soni (faqat raqam):")
    await state.set_state(ProductState.quantity)

@dp.message(ProductState.quantity)
async def pr_qty(message: types.Message, state: FSMContext):
    try:
        q = int(message.text)
    except ValueError:
        await message.answer("Faqat raqam kiriting:")
        return
    await state.update_data(quantity=q)
    await message.answer("Rasmini yuboring (yoki rasm yo'q bo'lsa biron nima yozing):")
    await state.set_state(ProductState.photo)

@dp.message(ProductState.photo)
async def pr_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id if message.photo else "none"
    
    data = await state.get_data()
    db.add_product(
        category=data['category'], 
        subcategory=data.get('subcategory'), 
        model=data.get('model'),
        name=data['name'], 
        memory=data['memory'],
        battery=data['battery'], 
        color=data['color'], 
        condition=data['condition'],
        price=data['price'], 
        quantity=data['quantity'], 
        photo_id=photo_id
    )
    
    await message.answer("✅ Mahsulot bazaga qo'shildi!", reply_markup=get_main_menu(message.from_user.id))
    
    # SMS (BROADCAST) YUBORISH QISMI
    users = db.get_all_users()
    if users:
        broadcast_msg = (
            f"🔔 <b>Yangi mahsulot keldi!</b>\n\n"
            f"📱 <b>{data['name']}</b>\n"
            f"💰 Narxi: {data['price']}\n\n"
            f"<i>Katalogimizga kirib to'liq tanishib chiqing!</i>"
        )
        for u in users:
            try:
                if photo_id != "none":
                    await bot.send_photo(u['user_id'], photo=photo_id, caption=broadcast_msg, parse_mode="HTML")
                else:
                    await bot.send_message(u['user_id'], text=broadcast_msg, parse_mode="HTML")
                await asyncio.sleep(0.05)
            except Exception as e:
                pass

    await state.clear()

@dp.callback_query(F.data == "pr_del")
async def pr_del_list(call: types.CallbackQuery):
    prods = db.get_all_products()
    if not prods:
        await call.answer("Mahsulotlar yo'q.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for p in prods:
        builder.button(text=f"❌ {p['name']} ({p['price']})", callback_data=f"delp_{p['id']}")
    builder.adjust(1)
    await call.message.answer("O'chirish uchun tanlang:", reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("delp_"))
async def pr_del_confirm(call: types.CallbackQuery):
    db.delete_product(int(call.data.split("_")[1]))
    await call.message.edit_text("✅ Mahsulot o'chirildi!")

# --- 24/7 VEB-SERVER (RENDER UCHUN) ---
async def handle_ping(request):
    return web.Response(text="Bot 24/7 ishlayapti!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    db.init_db()
    await start_web_server()
    print("Bot va Server ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
