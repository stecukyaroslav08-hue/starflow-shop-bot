import os
import asyncio
import random
import string
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
CARD_NUMBER = os.getenv("CARD_NUMBER")

ADMIN_ID = 7206786301
SUPPORT_USERNAME = "@Bevseev"

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
# БАЗА
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    rating INTEGER,
    text TEXT,
    status TEXT
)
""")

db.commit()


# =========================================================
# ПРИМЕРЫ ОТЗЫВОВ
# =========================================================
# Это именно демонстрационные отзывы, чтобы раздел
# не был пустым до появления реальных отзывов.

DEMO_REVIEWS = [
    ("@Alex", 5, "Всё быстро, оплату проверили без проблем ⭐"),
    ("@maks", 5, "Удобный бот, всё понятно и быстро."),
    ("@dima", 5, "Stars получил, спасибо! Буду пользоваться ещё."),
    ("@user", 4, "Всё хорошо, заказ обработали быстро 👍"),
]


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
        text="⭐ Отзывы",
        callback_data="reviews"
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
        "Добро пожаловать в магазин Telegram Stars! 🚀\n\n"
        "⚡ Быстрая обработка заказов\n"
        "💳 Удобная оплата\n"
        "⭐ Telegram Stars\n\n"
        "👇 Выбери нужный раздел:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================================================
# TELEGRAM ID
# =========================================================

@dp.message(Command("id"))
async def get_id(message: Message):

    await message.answer(
        "🆔 Твой Telegram ID:\n\n"
        f"<code>{message.from_user.id}</code>",
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
# ВЫБОР ПАКЕТА
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

    telegram_user = (
        f"@{username}"
        if username
        else "Username отсутствует"
    )

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
        f"⭐ <b>Товар:</b> {stars} Stars\n"
        f"💰 <b>К оплате:</b> {price} грн\n"
        f"👤 <b>Telegram:</b> {telegram_user}\n\n"
        f"🧾 <b>ID заказа:</b>\n"
        f"<code>{order_id}</code>\n\n"
        "📌 <b>Важно:</b>\n"
        "• Оплату принимаем только от владельца аккаунта.\n"
        "• В комментарии к платежу укажите ID заказа.\n"
        "• После оплаты нажмите «Я оплатил».\n\n"
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
# ПОЛУЧЕНИЕ ЧЕКА
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

    telegram_user = (
        f"@{username}"
        if username
        else "Username отсутствует"
    )

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
            f"🆔 <b>Telegram ID:</b> "
            f"<code>{message.from_user.id}</code>\n"
            f"⭐ <b>Stars:</b> {stars}\n"
            f"💰 <b>Сумма:</b> {price} грн\n\n"
            "Проверь оплату:"
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
        ("paid", order_id)
    )

    db.commit()

    await bot.send_message(
        user_id,
        "✅ <b>Оплата подтверждена!</b>\n\n"
        f"🧾 Заказ: <code>{order_id}</code>\n"
        f"⭐ Stars: {stars}\n"
        f"💰 Сумма: {price} грн\n\n"
        "Заказ принят в обработку. ⭐",
        parse_mode="HTML"
    )

    review_keyboard = InlineKeyboardBuilder()

    review_keyboard.button(
        text="⭐ Оставить отзыв",
        callback_data=f"new_review_{order_id}"
    )

    await bot.send_message(
        user_id,
        "💬 <b>Спасибо за покупку!</b>\n\n"
        "Оцени работу StarFlow Shop 👇",
        reply_markup=review_keyboard.as_markup(),
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
        f"🧾 Заказ: <code>{order_id}</code>\n\n"
        "Если ты уверен, что оплатил заказ, "
        "обратись в поддержку.",
        parse_mode="HTML"
    )

    await callback.message.edit_caption(
        caption=(
            "❌ <b>ОПЛАТА ОТКЛОНЕНА</b>\n\n"
            f"🧾 Заказ: <code>{order_id}</code>\n"
            f"⭐ {stars} Stars\n"
            f"💰 {price} грн"
        ),
        parse_mode="HTML"
    )

    await callback.answer("Заказ отклонён ❌")


# =========================================================
# ОТЗЫВЫ
# =========================================================

@dp.callback_query(F.data == "reviews")
async def reviews(callback: CallbackQuery):

    cursor.execute(
        """
        SELECT rating, username, text
        FROM reviews
        WHERE status = 'published'
        ORDER BY id DESC
        LIMIT 10
        """
    )

    real_reviews = cursor.fetchall()

    cursor.execute(
        """
        SELECT AVG(rating), COUNT(*)
        FROM reviews
        WHERE status = 'published'
        """
    )

    average, count = cursor.fetchone()

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="✍️ Оставить отзыв",
        callback_data="new_review"
    )

    keyboard.button(
        text="🔙 Назад",
        callback_data="back"
    )

    keyboard.adjust(1)

    text = (
        "⭐ <b>Отзывы StarFlow Shop</b>\n\n"
    )

    if count:
        text += (
            f"📊 <b>Рейтинг:</b> {average:.1f}/5\n"
            f"💬 <b>Реальных отзывов:</b> {count}\n\n"
        )

    else:
        text += (
            "📊 <b>Рейтинг:</b> пока формируется\n\n"
        )

    # Демонстрационные отзывы
    text += "💬 <b>Примеры отзывов:</b>\n\n"

    for username, rating, review_text in DEMO_REVIEWS:

        text += (
            f"{'⭐' * rating}\n"
            f"👤 <b>{username}</b>\n"
            f"💬 {review_text}\n\n"
        )

    # Реальные отзывы
    if real_reviews:

        text += "━━━━━━━━━━━━━━\n"
        text += "⭐ <b>Отзывы покупателей:</b>\n\n"

        for rating, username, review_text in real_reviews:

            text += (
                f"{'⭐' * rating}\n"
                f"👤 <b>{username}</b>\n"
                f"💬 {review_text}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# НОВЫЙ ОТЗЫВ
# =========================================================

@dp.callback_query(F.data.startswith("new_review"))
async def new_review(callback: CallbackQuery):

    pending_reviews[callback.from_user.id] = {}

    keyboard = InlineKeyboardBuilder()

    for rating in range(5, 0, -1):

        keyboard.button(
            text="⭐" * rating,
            callback_data=f"rating_{rating}"
        )

    keyboard.button(
        text="🔙 Назад",
        callback_data="reviews"
    )

    keyboard.adjust(1)

    await callback.message.edit_text(
        "⭐ <b>Оцени StarFlow Shop</b>\n\n"
        "Выбери свою оценку:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ВРЕМЕННЫЕ ОТЗЫВЫ
# =========================================================

pending_reviews = {}


# =========================================================
# ВЫБОР ОЦЕНКИ
# =========================================================

@dp.callback_query(F.data.startswith("rating_"))
async def select_rating(callback: CallbackQuery):

    rating = int(
        callback.data.replace("rating_", "")
    )

    pending_reviews[callback.from_user.id] = {
        "rating": rating
    }

    await callback.message.edit_text(
        f"⭐ <b>Твоя оценка:</b> {'⭐' * rating}\n\n"
        "Теперь напиши свой отзыв одним сообщением.",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ТЕКСТ ОТЗЫВА
# =========================================================

@dp.message(F.text)
async def review_text(message: Message):

    user_id = message.from_user.id

    if user_id not in pending_reviews:
        return

    review_data = pending_reviews[user_id]

    if "rating" not in review_data:
        return

    rating = review_data["rating"]

    review_text_value = message.text.strip()

    if len(review_text_value) < 3:
        await message.answer(
            "❌ Напиши отзыв хотя бы из нескольких слов."
        )
        return

    if len(review_text_value) > 500:
        await message.answer(
            "❌ Максимальная длина отзыва — 500 символов."
        )
        return

    username = message.from_user.username

    display_name = (
        f"@{username}"
        if username
        else message.from_user.full_name
    )

    cursor.execute(
        """
        INSERT INTO reviews
        (user_id, username, rating, text, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            display_name,
            rating,
            review_text_value,
            "pending"
        )
    )

    db.commit()

    review_id = cursor.lastrowid

    del pending_reviews[user_id]

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="✅ Опубликовать",
        callback_data=f"publish_review_{review_id}"
    )

    keyboard.button(
        text="❌ Отклонить",
        callback_data=f"reject_review_{review_id}"
    )

    keyboard.adjust(1)

    await bot.send_message(
        ADMIN_ID,
        "📝 <b>НОВЫЙ ОТЗЫВ</b>\n\n"
        f"👤 <b>Пользователь:</b> {display_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"⭐ <b>Оценка:</b> {'⭐' * rating}\n\n"
        f"💬 <b>Отзыв:</b>\n{review_text_value}",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await message.answer(
        "✅ <b>Спасибо за отзыв!</b>\n\n"
        "Отзыв отправлен на проверку.",
        parse_mode="HTML"
    )


# =========================================================
# ПУБЛИКАЦИЯ ОТЗЫВА
# =========================================================

@dp.callback_query(F.data.startswith("publish_review_"))
async def publish_review(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True
        )
        return

    review_id = int(
        callback.data.replace(
            "publish_review_",
            ""
        )
    )

    cursor.execute(
        """
        UPDATE reviews
        SET status = ?
        WHERE id = ?
        """,
        ("published", review_id)
    )

    db.commit()

    await callback.message.edit_text(
        "✅ <b>Отзыв опубликован!</b>",
        parse_mode="HTML"
    )

    await callback.answer("Опубликовано ✅")


# =========================================================
# ОТКЛОНЕНИЕ ОТЗЫВА
# =========================================================

@dp.callback_query(F.data.startswith("reject_review_"))
async def reject_review(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True
        )
        return

    review_id = int(
        callback.data.replace(
            "reject_review_",
            ""
        )
    )

    cursor.execute(
        """
        UPDATE reviews
        SET status = ?
        WHERE id = ?
        """,
        ("rejected", review_id)
    )

    db.commit()

    await callback.message.edit_text(
        "❌ <b>Отзыв отклонён.</b>",
        parse_mode="HTML"
    )

    await callback.answer("Отклонено ❌")


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

    statuses = {
        "waiting_payment": "⏳ Ожидает оплаты",
        "waiting_receipt": "📸 Ожидает чек",
        "checking": "🔎 Проверяется",
        "paid": "✅ Оплачено",
        "rejected": "❌ Отклонено"
    }

    if not orders:

        text = (
            "💰 <b>Мои покупки</b>\n\n"
            "У тебя пока нет заказов."
        )

    else:

        text = "💰 <b>Мои покупки</b>\n\n"

        for order_id, stars, price, status in orders:

            status_text = statuses.get(
                status,
                status
            )

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
        text="👨‍💻 Написать в поддержку",
        url="https://t.me/Bevseev"
    )

    keyboard.button(
        text="🔙 Назад",
        callback_data="back"
    )

    keyboard.adjust(1)

    await callback.message.edit_text(
        "💬 <b>Поддержка StarFlow Shop</b>\n\n"
        "Если возникла проблема с заказом,\n"
        "напиши нашей поддержке.\n\n"
        f"👨‍💻 {SUPPORT_USERNAME}",
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
        "Добро пожаловать в магазин Telegram Stars! 🚀\n\n"
        "⚡ Быстрая обработка заказов\n"
        "💳 Удобная оплата\n"
        "⭐ Telegram Stars\n\n"
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
