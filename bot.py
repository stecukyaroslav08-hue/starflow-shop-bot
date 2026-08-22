import os
import asyncio
import random
import string

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


TOKEN = os.getenv("BOT_TOKEN")
CARD_NUMBER = os.getenv("CARD_NUMBER")

bot = Bot(token=TOKEN)
dp = Dispatcher()


PRICES = {
    "100": 65,
    "500": 300,
    "1000": 570,
    "2500": 1375,
    "5000": 2600,
}


def create_order_id():
    characters = string.ascii_uppercase + string.digits
    return "SF-" + "".join(random.choices(characters, k=6))


def main_menu():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text="⭐ Купить Stars", callback_data="buy_stars")
    keyboard.button(text="💰 Мои покупки", callback_data="my_orders")
    keyboard.button(text="🎁 Промокод", callback_data="promo")
    keyboard.button(text="💬 Поддержка", callback_data="support")

    keyboard.adjust(1)

    return keyboard.as_markup()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "⭐ <b>StarFlow Shop</b>\n\n"
        "Добро пожаловать!\n"
        "Здесь ты можешь приобрести Telegram Stars.\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "buy_stars")
async def buy_stars(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()

    for stars, price in PRICES.items():
        keyboard.button(
            text=f"⭐ {stars} Stars — {price} грн",
            callback_data=f"stars_{stars}"
        )

    keyboard.button(text="🔙 Назад", callback_data="back")
    keyboard.adjust(1)

    await callback.message.edit_text(
        "⭐ <b>Покупка Stars</b>\n\n"
        "Выбери нужный пакет:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("stars_"))
async def selected_stars(callback: CallbackQuery):
    stars = callback.data.replace("stars_", "")
    price = PRICES[stars]

    username = callback.from_user.username

    if username:
        telegram_user = f"@{username}"
    else:
        telegram_user = "Username отсутствует"

    order = create_order_id()

    text = (
        "🏦 <b>Оплата на карту</b>\n\n"
        f"💳 <b>Номер карты:</b> {CARD_NUMBER}\n"
        f"💰 <b>К оплате:</b> {price} грн\n\n"
        f"⭐ <b>Товар:</b> {stars} Stars\n"
        f"👤 <b>Telegram:</b> {telegram_user}\n\n"
        f"🧾 <b>ID заказа:</b> <code>{order}</code>\n\n"
        "⚠️ <b>Важно:</b>\n"
        "• Оплату принимаем только от владельца аккаунта, оформляющего заказ.\n"
        "• Переводы от третьих лиц не принимаются.\n"
        "• В комментарии к платежу укажите: «Претензий не имею».\n"
        "• После оплаты отправьте скриншот чека в этот чат.\n\n"
        "⏰ После отправки чека дождитесь проверки платежа и подтверждения заказа. ✅"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="buy_stars")

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "⭐ <b>StarFlow Shop</b>\n\n"
        "Добро пожаловать!\n"
        "Здесь ты можешь приобрести Telegram Stars.\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


async def main():
    await dp.start_polling(bot)


if name == "__main__":
    asyncio.run(main())
