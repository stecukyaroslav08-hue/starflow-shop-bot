import os
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Цены StarFlow Shop
PRICES = {
    "100": 65,
    "500": 300,
    "1000": 570,
    "2500": 1375,
    "5000": 2600,
}


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

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text=f"💳 Оплатить {price} грн",
        callback_data=f"pay_{stars}"
    )
    keyboard.button(text="🔙 Назад", callback_data="buy_stars")
    keyboard.adjust(1)

    await callback.message.edit_text(
        f"⭐ <b>{stars} Telegram Stars</b>\n\n"
        f"Стоимость: <b>{price} грн</b>\n\n"
        "Нажми кнопку ниже, чтобы перейти к оплате.",
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


@dp.callback_query(F.data.startswith("pay_"))
async def payment(callback: CallbackQuery):
    stars = callback.data.replace("pay_", "")
    price = PRICES[stars]

    await callback.message.edit_text(
        f"⭐ Заказ на <b>{stars} Stars</b>\n\n"
        f"💰 К оплате: <b>{price} грн</b>\n\n"
        "💳 Систему оплаты подключим следующим шагом.",
        parse_mode="HTML"
    )
