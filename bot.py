"""
Telegram-бот-визитка фрилансера с приёмом заявок.

Возможности:
- /start  — приветствие и главное меню (инлайн-кнопки)
- Услуги, Контакты, «О боте» — навигация по разделам
- 📝 Оставить заявку — клиент описывает задачу и контакт, заявка приходит владельцу в личку
- /id — узнать свой Telegram chat_id (нужно для настройки ADMIN_ID)

Стек: aiogram 3.x. Токен — из BOT_TOKEN, владелец заявок — из ADMIN_ID.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "Не задан BOT_TOKEN. Укажите его в переменной окружения или в файле .env"
    )

# ID владельца (куда слать заявки). Если 0 — заявки только логируются.
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# --- Контактные данные ---
OWNER_NAME = "Сергей"
TELEGRAM = "@srgchprnn"
EMAIL = "srg.chprnn@mail.ru"


class Lead(StatesGroup):
    """Состояния сбора заявки."""

    waiting_task = State()
    waiting_contact = State()


def start_kb() -> ReplyKeyboardMarkup:
    """Постоянная нижняя кнопка «Старт» — всегда под рукой."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Старт")]],
        resize_keyboard=True,
        is_persistent=True,
    )


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="lead")],
            [InlineKeyboardButton(text="🧩 Услуги", callback_data="services")],
            [InlineKeyboardButton(text="📫 Контакты", callback_data="contacts")],
            [InlineKeyboardButton(text="🤖 О боте", callback_data="about")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]]
    )


def cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✖️ Отмена", callback_data="menu")]]
    )


dp = Dispatcher()


@dp.message(CommandStart())
@dp.message(F.text == "▶️ Старт")
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! 👋 Я бот-визитка)\n\n"
        "Делаю Telegram-ботов, парсеры и лендинги.",
        reply_markup=start_kb(),
    )
    await message.answer("Выберите раздел 👇", reply_markup=main_menu())


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n/start — меню\n/help — справка\n/id — узнать свой chat_id",
        reply_markup=main_menu(),
    )


@dp.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(
        f"Ваш chat_id: <code>{message.chat.id}</code>\n"
        "Этот номер используется для настройки получателя заявок (ADMIN_ID)."
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено. Возвращаю в меню 👇", reply_markup=main_menu())


@dp.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu())
    await callback.answer()


# ===== Приём заявки =====
@dp.callback_query(F.data == "lead")
async def cb_lead(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Lead.waiting_task)
    await callback.message.edit_text(
        "📝 <b>Оставить заявку</b>\n\n"
        "Опишите кратко вашу задачу — что нужно сделать?\n"
        "<i>(например: бот для приёма заказов, парсер каталога, лендинг для услуги)</i>",
        reply_markup=cancel_menu(),
    )
    await callback.answer()


@dp.message(StateFilter(Lead.waiting_task), F.text)
async def lead_task(message: Message, state: FSMContext) -> None:
    await state.update_data(task=message.text)
    await state.set_state(Lead.waiting_contact)
    await message.answer(
        "Принял! 👍\n\nКак с вами связаться? Оставьте контакт — "
        "телефон, @username или email.",
        reply_markup=cancel_menu(),
    )


@dp.message(StateFilter(Lead.waiting_contact), F.text)
async def lead_contact(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task = data.get("task", "—")
    contact = message.text
    user = message.from_user
    username = f"@{user.username}" if user.username else "—"

    lead_text = (
        "🔔 <b>Новая заявка!</b>\n\n"
        f"<b>Задача:</b> {task}\n"
        f"<b>Контакт:</b> {contact}\n"
        f"<b>От:</b> {user.full_name} ({username}, id <code>{user.id}</code>)"
    )

    delivered = False
    if ADMIN_ID:
        try:
            await message.bot.send_message(ADMIN_ID, lead_text)
            delivered = True
        except Exception as exc:  # noqa: BLE001
            logger.error("Не удалось отправить заявку владельцу: %s", exc)
    else:
        logger.warning("ADMIN_ID не задан — заявка не отправлена: %s", lead_text)

    if not delivered:
        logger.info("ЗАЯВКА: %s", lead_text)

    await state.clear()
    await message.answer(
        "Спасибо! 🙌 Заявка принята — я свяжусь с вами в ближайшее время.",
        reply_markup=back_menu(),
    )


@dp.callback_query(F.data == "services")
async def cb_services(callback: CallbackQuery) -> None:
    text = (
        "🧩 <b>Чем могу быть полезен</b>\n\n"
        "🤖 <b>Telegram-боты на Python</b>\n"
        "от простых до ботов с интеграциями, оплатой и базой данных\n\n"
        "🕸️ <b>Парсинг сайтов</b>\n"
        "сбор, очистка и структурирование данных в нужном формате\n\n"
        "🎨 <b>Вёрстка лендингов</b>\n"
        "адаптивные страницы на HTML и CSS"
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


@dp.callback_query(F.data == "contacts")
async def cb_contacts(callback: CallbackQuery) -> None:
    text = (
        "📫 <b>Связаться со мной</b>\n\n"
        f"💬 Telegram: {TELEGRAM}\n"
        f"✉️ Email: {EMAIL}\n\n"
        "Напишите — обсудим вашу задачу 🙌"
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


@dp.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery) -> None:
    text = (
        "🤖 <b>О боте</b>\n\n"
        "Этот бот написан на Python с использованием библиотеки <b>aiogram</b> "
        "и работает на собственном сервере 24/7.\n\n"
        "Это пример того, какого бота я могу сделать под вашу задачу."
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


@dp.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Не совсем понял 🤔 Воспользуйся меню 👇", reply_markup=main_menu()
    )


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logger.info("Бот запускается... ADMIN_ID=%s", ADMIN_ID or "не задан")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
