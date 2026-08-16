import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text="⭐ Купить Stars", callback_data="buy_stars")
    keyboard.button(text="💰 Мои покупки", callback_data="my_orders")
    keyboard.button(text="🎁 Промокод", callback_data="promo")
    keyboard.button(text="💬 Поддержка", callback_data="support")

    keyboard.adjust(1)

    await message.answer(
        "⭐ <b>StarFlow Shop</b>\n\n"
        "Добро пожаловать!\n"
        "Здесь ты можешь приобрести Telegram Stars.\n\n"
        "Выбери нужный раздел:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
