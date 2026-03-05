import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8230210984:AAGld9gVSXps2zC22qyKH5gKXV946wdS2CM")
API_URL = os.getenv("MINI_APP_URL", "https://connect-u-2.onrender.com")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class RegisterState(StatesGroup):
    role = State()
    full_name = State()
    phone = State()
    university = State()
    faculty = State()
    year = State()

def role_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Abituriyent", callback_data="role_student")],
        [InlineKeyboardButton(text="👨‍🏫 Mentor", callback_data="role_mentor")],
    ])

def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu_keyboard(role="student"):
    if role == "mentor":
        buttons = [
            [KeyboardButton(text="📋 Profilim"), KeyboardButton(text="💰 Balans")],
            [KeyboardButton(text="📅 Sessiyalarim"), KeyboardButton(text="💬 Yordam")],
            [KeyboardButton(text="📷 QR bilan kirish")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="🎓 Mentorlar"), KeyboardButton(text="🏫 Universitetlar")],
            [KeyboardButton(text="👤 Profilim"), KeyboardButton(text="💬 Yordam")],
            [KeyboardButton(text="📷 QR bilan kirish")],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def qr_scanner_keyboard():
    scanner_url = f"{API_URL}/qr-scanner.html"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📷 QR Kodni Skaner Qilish",
            web_app=WebAppInfo(url=scanner_url)
        )
    ]])

def webapp_keyboard(panel_url=None):
    if not panel_url:
        panel_url = f"{API_URL}/login.html"
    
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🚀 ConnectU ilovasini ochish",
            web_app=WebAppInfo(url=panel_url)
        )
    ]])

async def get_user_by_telegram_id(telegram_id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/bot/user/{telegram_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('user')
    except Exception as e:
        log.error(f"get_user xatosi: {e}")
    return None

def get_panel_url(role):
    if role == 'mentor':
        return f"{API_URL}/mentor.html"
    elif role in ['admin', 'superadmin']:
        return f"{API_URL}/admin.html"
    else:
        return f"{API_URL}/abuturyent.html"

async def show_main_menu(msg: types.Message, user: dict):
    role = user.get("role", "student")
    name = user.get("full_name", "Foydalanuvchi")
    
    await msg.answer(
        f"👋 Xush kelibsiz, {name}!\n\n"
        f"ConnectU platformasiga xush kelibsiz.",
        reply_markup=main_menu_keyboard(role)
    )
    
    panel_url = get_panel_url(role)
    
    await msg.answer(
        "📲 Ilovani ochish:",
        reply_markup=webapp_keyboard(panel_url)
    )

async def show_registration_options(msg: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Abituriyent", callback_data="role_student")],
        [InlineKeyboardButton(text="👨‍🏫 Mentor", callback_data="role_mentor")],
    ])
    
    await msg.answer(
        "👋 <b>ConnectU ga xush kelibsiz!</b>\n\n"
        "Iltimos, ro'lingizni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext):
    await state.clear()
    
    args = msg.text.split()
    if len(args) > 1:
        if args[1].startswith('dl_'):
            token = args[1].replace('dl_', '')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_login_{token}")
            ]])
            await msg.answer(
                "🔐 <b>Tizimga kirish</b>\n\n"
                "Akkountingizga kirishni tasdiqlaysizmi?\n\n"
                "⚠️ Eslatma: Bu operatsiya joriy sessiyani yakunlaydi!", 
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return
        elif args[1].startswith('qr_'):
            token = args[1].replace('qr_', '')
            await process_login_token(msg, token, state)
            return
        elif args[1].startswith('login_'):
            token = args[1].replace('login_', '')
            await process_login_token(msg, token, state)
            return
    
    user = await get_user_by_telegram_id(msg.from_user.id)
    
    if user:
        await show_main_menu(msg, user)
    else:
        await show_registration_options(msg)

@dp.callback_query(F.data.startswith("confirm_login_"))
async def process_confirm_login(callback: types.CallbackQuery, state: FSMContext):
    token = callback.data.replace("confirm_login_", "")
    
    await callback.message.edit_text(
        "🔄 <b>Tekshirilmoqda...</b>\n\n"
        "Iltimos, kuting...",
        parse_mode="HTML"
    )
    
    await process_login_token(callback.message, token, state, user=callback.from_user)
    await callback.answer()

async def process_login_token(msg: types.Message, token: str, state: FSMContext, user: types.User = None):
    if user is None:
        user = msg.from_user
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/bot/verify-login", json={
                'token': token,
                'telegram_id': user.id,
                'username': user.username or '',
                'first_name': user.first_name,
                'last_name': user.last_name
            }) as resp:
                
                if resp.status != 200:
                    await msg.answer("❌ Server bilan bog'lanib bo'lmadi")
                    return
                
                result = await resp.json()
                
                if result.get('success'):
                    user_data = result.get('user', {})
                    full_name = user_data.get('full_name', 'Foydalanuvchi')
                    role = user_data.get('role', 'student')
                    
                    success_text = (
                        f"✅ <b>Muvaffaqiyatli!</b>\n\n"
                        f"🎉 Web saytda akkauntingizga kirildi!\n\n"
                        f"Xush kelibsiz, {full_name}!\n"
                        f"Rolingiz: {'🎓 Abituriyent' if role == 'student' else '👨‍🏫 Mentor'}"
                    )
                    
                    if hasattr(msg, 'edit_text'):
                        await msg.edit_text(success_text, parse_mode="HTML")
                    else:
                        await msg.answer(success_text, parse_mode="HTML")
                    
                    panel_url = get_panel_url(role)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text="🚀 Ilovani ochish",
                            web_app=WebAppInfo(url=panel_url)
                        )
                    ]])
                    
                    await msg.answer(
                        "📲 Endi web saytga qaytishingiz mumkin:",
                        reply_markup=keyboard
                    )
                    
                    if result.get('session_replaced'):
                        await msg.answer(
                            "⚠️ <b>Diqqat!</b>\n\n"
                            "Boshqa qurilmadagi eski sessiya tugatildi.",
                            parse_mode="HTML"
                        )
                else:
                    error_msg = result.get('error', 'Noma\'lum xatolik')
                    error_text = f"❌ <b>Xatolik</b>\n\n{error_msg}"
                    
                    if hasattr(msg, 'edit_text'):
                        await msg.edit_text(error_text, parse_mode="HTML")
                    else:
                        await msg.answer(error_text, parse_mode="HTML")
                    
    except Exception as e:
        log.error(f"process_login_token xatosi: {e}")
        await msg.answer(f"❌ Xatolik: {str(e)}")

@dp.callback_query(F.data.startswith("role_"))
async def process_role(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.replace("role_", "")
    await state.update_data(role=role)
    
    await callback.message.delete()
    
    if role == "mentor":
        await callback.message.answer(
            "👨‍🏫 Mentor ro'yxatdan o'tishi\n\n"
            "Ism va familiyangizni kiriting:"
        )
    else:
        await callback.message.answer(
            "🎓 Abituriyent ro'yxatdan o'tishi\n\n"
            "Ism va familiyangizni kiriting:"
        )
    
    await state.set_state(RegisterState.full_name)
    await callback.answer()

@dp.message(RegisterState.full_name)
async def process_full_name(msg: types.Message, state: FSMContext):
    full_name = msg.text.strip()
    
    if len(full_name) < 3:
        await msg.answer("❌ Ism kamida 3 harf bo'lishi kerak. Qayta kiriting:")
        return
    
    await state.update_data(full_name=full_name)
    data = await state.get_data()
    
    if data.get("role") == "mentor":
        await msg.answer(
            "🏛 Qaysi universitetda o'qiysiz?\n"
            "Masalan: Toshkent Davlat Yuridik Universiteti"
        )
        await state.set_state(RegisterState.university)
    else:
        await msg.answer(
            "📱 Telefon raqamingizni yuboring:",
            reply_markup=phone_keyboard()
        )
        await state.set_state(RegisterState.phone)

@dp.message(RegisterState.university)
async def process_university(msg: types.Message, state: FSMContext):
    university = msg.text.strip()
    await state.update_data(university=university)
    
    await msg.answer(
        "📚 Fakultetingizni kiriting:\n"
        "Masalan: Huquqshunoslik"
    )
    await state.set_state(RegisterState.faculty)

@dp.message(RegisterState.faculty)
async def process_faculty(msg: types.Message, state: FSMContext):
    faculty = msg.text.strip()
    await state.update_data(faculty=faculty)
    
    await msg.answer(
        "📅 Nechanchi kursdasiz?\n"
        "Masalan: 3"
    )
    await state.set_state(RegisterState.year)

@dp.message(RegisterState.year)
async def process_year(msg: types.Message, state: FSMContext):
    try:
        year = int(msg.text.strip())
        if year < 1 or year > 5:
            await msg.answer("❌ Kurs 1-5 oralig'ida bo'lishi kerak. Qayta kiriting:")
            return
    except ValueError:
        await msg.answer("❌ Noto'g'ri format. Raqam kiriting (masalan: 3):")
        return
    
    await state.update_data(year=year)
    
    await msg.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard()
    )
    await state.set_state(RegisterState.phone)

@dp.message(RegisterState.phone, F.contact)
async def process_phone_contact(msg: types.Message, state: FSMContext):
    phone = msg.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    await complete_registration(msg, state, phone)

@dp.message(RegisterState.phone)
async def process_phone_text(msg: types.Message, state: FSMContext):
    phone = msg.text.strip().replace(" ", "").replace("-", "")
    
    if not phone.startswith("+998") or len(phone) < 13:
        await msg.answer(
            "❌ Noto'g'ri format. Telefon raqam +998901234567 formatida kiriting\n"
            "Yoki pastdagi tugmani bosing:",
            reply_markup=phone_keyboard()
        )
        return
    
    await complete_registration(msg, state, phone)

async def complete_registration(msg: types.Message, state: FSMContext, phone: str):
    data = await state.get_data()
    
    user_data = {
        "telegram_id": msg.from_user.id,
        "phone": phone,
        "full_name": data.get("full_name"),
        "username": msg.from_user.username or "",
        "role": data.get("role", "student")
    }
    
    if data.get("role") == "mentor":
        user_data["university"] = data.get("university")
        user_data["faculty"] = data.get("faculty")
        user_data["year"] = data.get("year")
    
    log.info(f"Ro'yxatdan o'tish: {user_data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/api/bot/register", json=user_data) as resp:
                result = await resp.json()
                
                if result.get("success"):
                    role = data.get("role", "student")
                    name = data.get("full_name", "Foydalanuvchi")
                    
                    if role == "mentor":
                        await msg.answer(
                            "⚠️ MUHIM!\n\n"
                            "Mentor paneliga kirgandan so'ng, 3 kun ichida\n"
                            "talabalik guvohnomasini yuklashingiz kerak.\n"
                            "Aks holda akkauntingiz o'chiriladi!"
                        )
                    
                    role_label = "🎓 Abituriyent" if role == "student" else "👨‍🏫 Mentor"
                    await msg.answer(
                        f"✅ Tabriklaymiz, {name}!\n\n"
                        f"Ro'yxatdan o'tish muvaffaqiyatli yakunlandi.\n"
                        f"Telefon raqamingiz: {phone}",
                        reply_markup=main_menu_keyboard(role)
                    )
                    
                    panel_url = get_panel_url(role)
                    
                    await msg.answer(
                        "📲 Ilovani ochish:",
                        reply_markup=webapp_keyboard(panel_url)
                    )
                else:
                    error_msg = result.get('error', "Noma'lum xatolik")
                    await msg.answer(
                        f"❌ Xatolik yuz berdi: {error_msg}\n\n"
                        f"Qayta urinib ko'ring: /start"
                    )
    except Exception as e:
        log.error(f"complete_registration xatosi: {e}")
        await msg.answer("❌ Server bilan bog'lanishda xatolik")
    
    await state.clear()

@dp.message(F.text == "👤 Profilim")
async def show_profile(msg: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/bot/user/{msg.from_user.id}") as resp:
                result = await resp.json()
                
                if result.get("success") and result.get("user"):
                    user = result["user"]
                    
                    role_text = "🎓 Abituriyent" if user.get("role") == "student" else "👨‍🏫 Mentor"
                    
                    text = "👤 Profilim\n\n"
                    text += f"Ism: {user.get('full_name')}\n"
                    text += f"Telefon: {user.get('phone')}\n"
                    text += f"Rol: {role_text}\n"
                    
                    if user.get("role") == "mentor" and user.get("mentor_profile"):
                        mp = user["mentor_profile"]
                        text += "\nMentor ma'lumotlari:\n"
                        text += f"Universitet: {mp.get('university')}\n"
                        text += f"Fakultet: {mp.get('faculty')}\n"
                        text += f"Kurs: {mp.get('year')}-kurs\n"
                        
                        status = "✅ Tasdiqlangan" if mp.get('is_verified') else "⏳ Kutilmoqda"
                        text += f"Holat: {status}\n"
                    
                    await msg.answer(text)
                else:
                    await msg.answer("❌ Profil topilmadi. /start ni bosing.")
    except Exception as e:
        log.error(f"show_profile xatosi: {e}")
        await msg.answer("❌ Xatolik yuz berdi")

@dp.message(F.text == "💬 Yordam")
async def help_handler(msg: types.Message):
    await msg.answer(
        "💬 Yordam\n\n"
        "📞 Admin: @connectu_admin\n"
        "🌐 Sayt: connectu.uz\n\n"
        "Agar muammo bo'lsa, admin bilan bog'lanishingiz mumkin."
    )


@dp.message(F.text == "📷 QR bilan kirish")
async def qr_login_handler(msg: types.Message):
    await msg.answer(
        "📷 <b>QR bilan kirish</b>\n\n"
        "Kompyuteringizda ConnectU login sahifasini oching va \"QR Kod\" tabini tanlang.\n\n"
        "Keyin quyidagi tugmani bosib, QR kodni skanerlang:",
        reply_markup=qr_scanner_keyboard(),
        parse_mode="HTML"
    )

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())

async def main():
    log.info("ConnectU Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())