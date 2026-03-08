import asyncio
import logging
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- 1. НАСТРОЙКИ ---
BOT_TOKEN = "8504871547:AAGVc8JA4qAJc3wP-qtllya4Ydx5jeajkOI"
ADMIN_IDS = [568876466, 1158607288]  # Замени на реальные ID
TIMEZONE = "Asia/Yekaterinburg"

USERS_FILE = "users.json"
SCHEDULE_FILE = "schedule.json"


# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ДАННЫЕ) ---
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Загружаем базы сразу
users_db = load_json(USERS_FILE, {})
schedule_db = load_json(SCHEDULE_FILE, {
    "2026-03-11 12:00": {"type": "text", "content": "Детка уже совсем скоро this is day, подготовься и сияй", "caption": None},
    "2026-03-12 12:00": {"type": "text", "content": "Baby, с 8 марта! Будь beautiful, неотразимой, amazing и радостной", "caption": None},
    "2026-03-13 12:00": {"type": "text", "content": "Girls, мы проверяем списки и ты уже там, совсем скоро отправим точную date и time", "caption": None},
    "2026-03-14 12:00": {"type": "text", "content": "WELCOME TO CLUB!!! ДА ДА ТЫ НЕ ОСЛЫШАЛАСЬ. Уже завтра состоится наша встреча в ауд. в ", "caption": None},
    "2026-03-15 15:00": {"type": "text", "content": "До финала 3 часа и уже наконец ты будешь на острове)))", "caption": None},
})


# --- 3. ФУНКЦИИ ПРЕДПРОСМОТРА И РАССЫЛКИ ---
# Определяем их ПЕРЕД тем, как использовать в обработчиках
async def send_to_admin_preview(bot: Bot, chat_id: int, slot_key: str):
    """Показывает админу, что сейчас находится в выбранном слоте"""
    item = schedule_db.get(slot_key)
    if not item:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить этот контент", callback_data=f"real_edit_{slot_key}")],
        [InlineKeyboardButton(text="🔙 Назад к списку дат", callback_data="adm_edit_list")]
    ])

    header = f"📅 **СЛОТ: {slot_key}**\n---\n"

    try:
        if item['type'] == 'text':
            await bot.send_message(chat_id, header + item['content'], reply_markup=kb, parse_mode="Markdown")
        elif item['type'] == 'photo':
            await bot.send_photo(chat_id, item['content'], caption=header + (item['caption'] or ""), reply_markup=kb,
                                 parse_mode="Markdown")
        elif item['type'] == 'video':
            await bot.send_video(chat_id, item['content'], caption=header + (item['caption'] or ""), reply_markup=kb,
                                 parse_mode="Markdown")
        elif item['type'] == 'voice':
            await bot.send_voice(chat_id, item['content'], caption=header + (item['caption'] or ""), reply_markup=kb,
                                 parse_mode="Markdown")
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка предпросмотра: {e}", reply_markup=kb)


async def send_broadcast(bot: Bot, slot_key: str):
    """Сама рассылка пользователям"""
    item = schedule_db.get(slot_key)
    if not item: return
    for user_id in list(users_db.keys()):
        try:
            if item['type'] == 'text':
                await bot.send_message(user_id, item['content'])
            elif item['type'] == 'photo':
                await bot.send_photo(user_id, item['content'], caption=item['caption'])
            elif item['type'] == 'video':
                await bot.send_video(user_id, item['content'], caption=item['caption'])
            elif item['type'] == 'voice':
                await bot.send_voice(user_id, item['content'], caption=item['caption'])
        except Exception:
            pass


# --- 4. ИНИЦИАЛИЗАЦИЯ БОТА ---
router = Router()
scheduler = AsyncIOScheduler(timezone=TIMEZONE)


class Registration(StatesGroup):
    name = State()
    photo = State()


class AdminEdit(StatesGroup):
    waiting_for_content = State()


def update_jobs(bot: Bot):
    scheduler.remove_all_jobs()
    for date_str in schedule_db.keys():
        try:
            run_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            if run_date > datetime.now():
                scheduler.add_job(send_broadcast, "date", run_date=run_date, args=[bot, date_str])
        except:
            continue


# --- 5. ОБРАБОТЧИКИ (USER) ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет pussy girl, ты ведь хочешь много money? Тогда ты по address, вводи своё name")
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Детка, ты на пороге big 💵, отправь своё amazing photo:")
    await state.set_state(Registration.photo)


@router.message(Registration.photo, F.photo)
async def reg_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    users_db[str(message.from_user.id)] = {
        "name": data['name'],
        "photo": message.photo[-1].file_id,
        "username": message.from_user.username or "нет"
    }
    save_json(USERS_FILE, users_db)
    await message.answer("Baby this is fantastic, скоро мы направим тебе instruction, чтобы ты попала на нашу закрытую party, где мы расскажем все other")
    await state.clear()


# --- 6. АДМИН ПАНЕЛЬ ---
@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_main(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Список юзеров", callback_data="adm_users")],
        [InlineKeyboardButton(text="📅 Управление рассылкой", callback_data="adm_edit_list")]
    ])
    await message.answer("🛠 Админ-панель", reply_markup=kb)


@router.callback_query(F.data == "adm_edit_list", F.from_user.id.in_(ADMIN_IDS))
async def adm_list_slots(callback: CallbackQuery):
    buttons = []
    for d in sorted(schedule_db.keys()):
        buttons.append([InlineKeyboardButton(text=f"👁 {d}", callback_data=f"view_{d}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    await callback.message.edit_text("Выберите дату для просмотра:",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("view_"), F.from_user.id.in_(ADMIN_IDS))
async def adm_view_content(callback: CallbackQuery, bot: Bot):
    slot = callback.data.replace("view_", "")
    await callback.message.delete()
    await send_to_admin_preview(bot, callback.from_user.id, slot)


@router.callback_query(F.data.startswith("real_edit_"), F.from_user.id.in_(ADMIN_IDS))
async def adm_start_edit(callback: CallbackQuery, state: FSMContext):
    slot = callback.data.replace("real_edit_", "")
    await state.update_data(current_slot=slot)
    await callback.message.answer(f"📝 Пришли новый контент для {slot} (текст, фото, видео или голос):")
    await state.set_state(AdminEdit.waiting_for_content)


@router.message(AdminEdit.waiting_for_content, F.from_user.id.in_(ADMIN_IDS))
async def adm_save_content(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    slot = data['current_slot']

    new_data = {"type": "text", "content": None, "caption": message.caption}
    if message.text:
        new_data.update({"type": "text", "content": message.text})
    elif message.photo:
        new_data.update({"type": "photo", "content": message.photo[-1].file_id})
    elif message.video:
        new_data.update({"type": "video", "content": message.video.file_id})
    elif message.voice:
        new_data.update({"type": "voice", "content": message.voice.file_id})

    schedule_db[slot] = new_data
    save_json(SCHEDULE_FILE, schedule_db)
    update_jobs(bot)

    await message.answer("✅ Обновлено!")
    await send_to_admin_preview(bot, message.from_user.id, slot)
    await state.clear()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await admin_main(callback.message)
    await callback.message.delete()


@router.callback_query(F.data == "adm_users", F.from_user.id.in_(ADMIN_IDS))
async def adm_show_users(callback: CallbackQuery):
    if not users_db:
        await callback.message.answer("Список пуст.")
    else:
        for uid, info in users_db.items():
            await callback.message.answer_photo(info['photo'],
                                                caption=f"👤 {info['name']}\nID: {uid}\nНик: @{info['username']}")
    await callback.answer()


# --- 7. ЗАПУСК ---
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    update_jobs(bot)
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
