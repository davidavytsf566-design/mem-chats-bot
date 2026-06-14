import asyncio
import sqlite3
import random
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База
conn = sqlite3.connect('memes.db')
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS memes 
               (id INTEGER PRIMARY KEY, file_id TEXT, file_type TEXT)''')
conn.commit()

def random_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Ещё мем", callback_data="random_meme")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ])

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("🤖 Мем-бот готов!\nЖми кнопку ниже 👇", reply_markup=random_kb())

@dp.callback_query(F.data == "random_meme")
async def send_random(callback: types.CallbackQuery):
    cur.execute("SELECT file_id, file_type FROM memes")
    memes = cur.fetchall()
    if not memes:
        return await callback.answer("База пуста! Добавь мемы", show_alert=True)

    file_id, ftype = random.choice(memes)
    if ftype == "photo":
        await callback.message.answer_photo(file_id, reply_markup=random_kb())
    elif ftype == "video":
        await callback.message.answer_video(file_id, reply_markup=random_kb())
    else:
        await callback.message.answer_animation(file_id, reply_markup=random_kb())
    await callback.answer()

@dp.callback_query(F.data == "stats")
async def stats(callback: types.CallbackQuery):
    count = cur.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
    await callback.message.answer(f"В базе сейчас **{count}** мемов 🔥", parse_mode="Markdown")

# Авто-сохранение от админа + любая медиа
@dp.message(F.photo | F.video | F.animation)
async def auto_save(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.photo:
        fid = message.photo[-1].file_id
        ftype = "photo"
    elif message.video:
        fid = message.video.file_id
        ftype = "video"
    else:
        fid = message.animation.file_id
        ftype = "animation"

    cur.execute("INSERT INTO memes (file_id, file_type) VALUES (?, ?)", (fid, ftype))
    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
    await message.answer(f"✅ Мем сохранён! Теперь в базе: **{count}**")

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    count = cur.execute("SELECT COUNT(*) FROM memes").fetchone()[0]
    await msg.answer(f"📊 В базе: **{count}** мемов")

@dp.message(Command("clear"))  # только для админа
async def clear_db(msg: types.Message):
    if msg.from_user.id == ADMIN_ID:
        cur.execute("DELETE FROM memes")
        conn.commit()
        await msg.answer("🗑 База очищена!")

async def main():
    print("🚀 Мем-бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
