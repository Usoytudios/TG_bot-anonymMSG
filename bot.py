import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN
import db


db.create_tables()


logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    db.add_user(user_id, username)
    agree_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Согласен", callback_data="agree")]
    ])
    text = (
        "Привет! Это бот для анонимного общения.\n\n"
        "📌 Как работает бот:\n"
        "- Ты пишешь сообщение, оно отправляется случайному пользователю.\n"
        "- Сообщения пересылаются анонимно, без имен.\n"
        "- За флуд бот может временно заблокировать тебя.\n\n"
        "❗ Нажимая кнопку «Согласен», ты принимаешь все риски и правила."
    )
    await message.answer(text, reply_markup=agree_button)

@router.callback_query(lambda c: c.data == "agree")
async def agree_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    db.update_agreement(user_id, True)
    db.set_active(user_id, True)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "✅ Ты согласился с условиями. Теперь можешь писать анонимные сообщения!")


@router.message(lambda message: message.text is not None)
async def forward_message(message: types.Message):
    sender_id = message.from_user.id
    receiver_id = db.get_random_active_user(sender_id)
    if receiver_id is None:
        await message.answer("Извините, сейчас нет доступных собеседников. Попробуйте позже.")
        return
    db.add_message(sender_id, receiver_id, message.text)
    await bot.send_message(receiver_id, f"Новое анонимное сообщение:\n\n{message.text}")


dp.include_router(router)


async def monitor_spam():
    from datetime import timedelta, datetime
    CHECK_INTERVAL = 30  
    MAX_MESSAGES_PER_MINUTE = 100
    while True:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE active = 1")
        active_users = cursor.fetchall()
        conn.close()
        for (user_id,) in active_users:
            time_threshold = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE sender_id = ? AND timestamp >= ?", (user_id, time_threshold))
            count = cursor.fetchone()[0]
            conn.close()
            if count > MAX_MESSAGES_PER_MINUTE:
                db.set_active(user_id, False)
                await bot.send_message(user_id, "Вы были временно заблокированы из-за слишком быстрого отправления сообщений.")
        await asyncio.sleep(CHECK_INTERVAL)

async def on_start():
    asyncio.create_task(monitor_spam())
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(on_start())
