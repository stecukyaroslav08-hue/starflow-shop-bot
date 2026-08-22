import os
import asyncio
import random
import string
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
CARD_NUMBER = os.getenv("CARD_NUMBER")

# Твой Telegram ID
ADMIN_ID = 7206786301


if not TOKEN:
    raise ValueError("Не найден BOT_TOKEN")

if not CARD_NUMBER:
    raise ValueError("Не найден CARD_NUMBER")


bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================================================
# ЦЕНЫ
# =========================================================

PRICES = {
    "100": 65,
    "500": 300,
    "1000": 570,
    "2500": 1375,
    "5000": 2600,
}


# =========================================================
# БАЗА ДАННЫХ
# =========================================================

db = sqlite3.connect("orders.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    username TEXT,
    stars INTEGER,
    price INTEGER,
    status TEXT
)
""")

db.commit()


# =========================================================
# ID ЗАКАЗА
# =========================================================

def create_order_id():
    characters = string.ascii_uppercase + string.digits
    return "SF-" + "".join(random.choices(characters, k=6))


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def main_menu():

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="⭐ Купить Stars",
        callback_data="buy_stars"
    )

    keyboard.button(
        text="💰 Мои покупки",
        callback_data="my_orders"
    )

    keyboard.button(
        text="🎁 Промокод",
        callback_data="promo"
    )

    keyboard.button(
        text="💬 Поддержка",
        callback_data="support"
    )

    keyboard.adjust(1)

    return keyboard.as_markup()


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "⭐ <b>StarFlow Shop</b>\n\n"
        "Добро пожаловать в магазин Telegram Stars!\n\n"
        "Здесь ты можешь приобрести Stars.\n\n"
        "👇 Выбери нужный раздел:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ПОКУПКА STARS
# =========================================================

@dp.callback_query(F.data == "buy_stars")
async def buy_stars(callback: CallbackQuery):

    keyboard = InlineKeyboardBuilder()

    for stars, price in PRICES.items():

        keyboard.button(
            text=f"⭐ {stars} Stars — {price} грн",
            callback_data=f"stars_{stars}"
        )

    keyboard.button(
        text="🔙 Назад",
        callback_data="back"
    )

    keyboard.adjust(1)

    await callback.message.edit_text(
        "⭐ <b>Покупка Stars</b>\n\n"
        "Выбери нужное количество:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ВЫБОР STARS
# =========================================================

@dp.callback_query(F.data.startswith("stars_"))
async def selected_stars(callback: CallbackQuery):

    stars = callback.data.replace("stars_", "")

    if stars not in PRICES:

        await callback.answer(
            "❌ Такой пакет не найден",
            show_alert=True
        )

        return

    price = PRICES[stars]

    username = callback.from_user.username

    if username:
        telegram_user = f"@{username}"
    else:
        telegram_user = "Username отсутствует"

    order_id = create_order_id()

    cursor.execute(
        """
        INSERT INTO orders
        (id, user_id, username, stars, price, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            order_id,
            callback.from_user.id,
            telegram_user,
            int(stars),
            price,
            "waiting_payment"
        )
    )

    db.commit()

    text = (
        "🏦 <b>Оплата заказа</b>\n\n"

        f"💳 <b>Номер карты:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n\n"

        f"💰 <b>К оплате:</b> {price} грн\n"
        f"⭐ <b>Товар:</b> {stars} Stars\n"
        f"👤 <b>Telegram:</b> {telegram_user}\n\n"

        f"🧾 <b>ID заказа:</b>\n"
        f"<code>{order_id}</code>\n\n"

        "📌 <b>Важно:</b>\n"
        "• Оплату принимаем только от владельца аккаунта.\n"
        "• В комментарии к платежу укажите ID заказа.\n"
        "• После оплаты нажмите кнопку ниже и отправьте чек.\n\n"

        "После проверки платежа заказ будет подтверждён. ✅"
    )

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="💳 Я оплатил",
        callback_data=f"paid_{order_id}"
    )

    keyboard.button(
        text="🔙 Назад",
        callback_data="buy_stars"
    )

    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# Я ОПЛАТИЛ
# =========================================================

@dp.callback_query(F.data.startswith("paid_"))
async def paid(callback: CallbackQuery):

    order_id = callback.data.replace("paid_", "")

    cursor.execute(
        """
        SELECT stars, price, status
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )

    order = cursor.fetchone()

    if not order:

        await callback.answer(
            "❌ Заказ не найден",
            show_alert=True
        )

        return

    stars, price, status = order

    if status != "waiting_payment":

        await callback.answer(
            "Этот заказ уже обрабатывается.",
            show_alert=True
        )

        return

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        ("waiting_receipt", order_id)
    )

    db.commit()

    await callback.message.edit_text(
        "📸 <b>Отправь чек</b>\n\n"
        f"🧾 Заказ: <code>{order_id}</code>\n"
        f"⭐ Stars: {stars}\n"
        f"💰 Сумма: {price} грн\n\n"
        "Отправь сюда фотографию или скриншот чека.\n\n"
        "После этого заказ поступит администратору на проверку. 👨‍💻",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ПОЛУЧЕНИЕ ФОТО ЧЕКА
# =========================================================

@dp.message(F.photo)
async def receipt_photo(message: Message):

    cursor.execute(
        """
        SELECT id, stars, price
        FROM orders
        WHERE user_id = ?
        AND status = 'waiting_receipt'
        ORDER BY rowid DESC
        LIMIT 1
        """,
        (message.from_user.id,)
    )

    order = cursor.fetchone()

    if not order:

        await message.answer(
            "❌ Я не нашёл заказ, который сейчас ожидает чек.\n\n"
            "Сначала создай заказ через ⭐ Купить Stars."
        )

        return

    order_id, stars, price = order

    username = message.from_user.username

    if username:
        telegram_user = f"@{username}"
    else:
        telegram_user = "Username отсутствует"

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        ("checking", order_id)
    )

    db.commit()

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="✅ Подтвердить оплату",
        callback_data=f"approve_{order_id}"
    )

    keyboard.button(
        text="❌ Отклонить",
        callback_data=f"reject_{order_id}"
    )

    keyboard.adjust(1)

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=(
            "🔔 <b>НОВЫЙ ПЛАТЁЖ</b>\n\n"
            f"🧾 <b>Заказ:</b> <code>{order_id}</code>\n"
            f"👤 <b>Пользователь:</b> {telegram_user}\n"
            f"🆔 <b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
            f"⭐ <b>Stars:</b> {stars}\n"
            f"💰 <b>Сумма:</b> {price} грн\n\n"
            "Проверь оплату и выбери действие ниже."
        ),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await message.answer(
        "✅ <b>Чек отправлен!</b>\n\n"
        f"🧾 Заказ: <code>{order_id}</code>\n\n"
        "Ожидай проверки оплаты. 🔎",
        parse_mode="HTML"
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
# =========================================================

@dp.callback_query(F.data.startswith("approve_"))
async def approve_order(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "❌ У тебя нет доступа.",
            show_alert=True
        )

        return

    order_id = callback.data.replace("approve_", "")

    cursor.execute(
        """
        SELECT user_id, stars, price, status
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )

    order = cursor.fetchone()

    if not order:

        await callback.answer(
            "❌ Заказ не найден.",
            show_alert=True
        )

        return

    user_id, stars, price, status = order

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        ("paid", order_id)
    )

    db.commit()

    await bot.send_message(
        user_id,
        "✅ <b>Оплата подтверждена!</b>\n\n"
        f"🧾 Заказ: <code>{order_id}</code>\n"
        f"⭐ Stars: {stars}\n"
        f"💰 Сумма: {price} грн\n\n"
        "Заказ принят в обработку. ⭐\n"
        "Ожидай зачисления Stars.",
        parse_mode="HTML"
    )

    await callback.message.edit_caption(
        caption=(
            "✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА</b>\n\n"
            f"🧾 Заказ: <code>{order_id}</code>\n"
            f"⭐ Stars: {stars}\n"
            f"💰 Сумма: {price} грн"
        ),
        parse_mode="HTML"
    )

    await callback.answer("Оплата подтверждена ✅")


# =========================================================
# ОТКЛОНЕНИЕ ОПЛАТЫ
# =========================================================

@dp.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "❌ У тебя нет доступа.",
            show_alert=True
        )

        return

    order_id = callback.data.replace("reject_", "")

    cursor.execute(
        """
        SELECT user_id, stars, price
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )

    order = cursor.fetchone()

    if not order:

        await callback.answer(
            "❌ Заказ не найден.",
            show_alert=True
        )

        return

    user_id, stars, price = order

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        ("rejected", order_id)
    )

    db.commit()

    await bot.send_message(
        user_id,
        "❌ <b>Оплата отклонена</b>\n\n"
        f"🧾 Заказ: <code>{order_id}</code>\n"
        f"⭐ Stars: {stars}\n"
        f"💰 Сумма: {price} грн\n\n"
        "Платёж не был подтверждён.\n"
        "Если ты уверен, что оплатил заказ, обратись в поддержку.",
        parse_mode="HTML"
    )

    await callback.message.edit_caption(
        caption=(
            "❌ <b>ОПЛАТА ОТКЛОНЕНА</b>\n\n"
            f"🧾 Заказ: <code>{order_id}</code>\n"
            f"⭐ Stars: {stars}\n"
            f"💰 Сумма: {price} грн"
        ),
        parse_mode="HTML"
    )

    await callback.answer("Заказ отклонён ❌")


# =========================================================
# МОИ ПОКУПКИ
# =========================================================

@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):

    cursor.execute(
        """
        SELECT id, stars, price, status
        FROM orders
        WHERE user_id = ?
        ORDER BY rowid DESC
        LIMIT 10
        """,
        (callback.from_user.id,)
    )

    orders = cursor.fetchall()

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🔙 Назад",
        callback_data="back"
    )

    if not orders:

        text = (
            "💰 <b>Мои покупки</b>\n\n"
            "У тебя пока нет заказов."
        )

    else:

        text = "💰 <b>Мои покупки</b>\n\n"

        for order_id, stars, price, status in orders:

            if status == "waiting_payment":
                status_text = "⏳ Ожидает оплаты"

            elif status == "waiting_receipt":
                status_text = "📸 Ожидает чек"

            elif status == "checking":
                status_text = "🔎 Проверяется"

            elif status == "paid":
                status_text = "✅ Оплачено"

            elif status == "rejected":
                status_text = "❌ Отклонено"

            else:
                status_text = status

            text += (
                f"🧾 <code>{order_id}</code>\n"
                f"⭐ {stars} Stars — {price} грн\n"
                f"{status_text}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ПРОМОКОД
# =========================================================

@dp.callback_query(F.data == "promo")
async def promo(callback: CallbackQuery):

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🔙 Назад",
        callback_data="back"
    )

    await callback.message.edit_text(
        "🎁 <b>Промокод</b>\n\n"
        "Функция промокодов пока находится в разработке.",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ПОДДЕРЖКА
# =========================================================

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🔙 Назад",
        callback_data="back"
    )

    await callback.message.edit_text(
        "💬 <b>Поддержка</b>\n\n"
        "Если возникла проблема с заказом,\n"
        "обратись к администратору: @De2vex",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# НАЗАД
# =========================================================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):

    await callback.message.edit_text(
        "⭐ <b>StarFlow Shop</b>\n\n"
        "Добро пожаловать в магазин Telegram Stars!\n\n"
        "👇 Выбери нужный раздел:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    print("StarFlow Shop запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
