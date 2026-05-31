"""
Telegram-бот-визитка фрилансера.

Возможности:
- /start  — приветствие и главное меню (инлайн-кнопки)
- Услуги, Контакты, «О боте» — навигация по разделам
- 🔤 Перевёртыш — небольшой интерактивный инструмент (демонстрация FSM)

Стек: aiogram 3.x. Токен берётся из переменной окружения BOT_TOKEN.
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
    Message,
)

# Грузим .env при локальном запуске (на сервере переменные задаёт systemd).
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

# --- Контактные данные (правится в одном месте) ---
OWNER_NAME = "Сергей"
TELEGRAM = "@srgchprnn"
EMAIL = "srg.chprnn@mail.ru"


class Tools(StatesGroup):
    """Состояния мини-инструмента «Перевёртыш»."""

    waiting_text = State()


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧩 Услуги", callback_data="services")],
            [InlineKeyboardButton(text="🔤 Перевёртыш (демо)", callback_data="tool")],
            [InlineKeyboardButton(text="📫 Контакты", callback_data="contacts")],
            [InlineKeyboardButton(text="🤖 О боте", callback_data="about")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    """Кнопка «назад» в главное меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
        ]
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Привет! 👋 Я бот-визитка <b>{OWNER_NAME}</b>.\n\n"
        "Делаю Telegram-ботов, парсеры и лендинги.\n"
        "Выбери раздел в меню ниже 👇",
        reply_markup=main_menu(),
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/start — главное меню\n"
        "/help — эта справка\n\n"
        "Или просто пользуйся кнопками 🙂",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu())
    await callback.answer()


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


@dp.callback_query(F.data == "tool")
async def cb_tool(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Tools.waiting_text)
    await callback.message.edit_text(
        "🔤 <b>Перевёртыш</b>\n\n"
        "Пришли любой текст — я переверну его задом наперёд "
        "и посчитаю количество символов.",
        reply_markup=back_menu(),
    )
    await callback.answer()


@dp.message(StateFilter(Tools.waiting_text), F.text)
async def tool_process(message: Message, state: FSMContext) -> None:
    source = message.text
    reversed_text = source[::-1]
    await message.answer(
        f"🔁 <b>Перевёрнуто:</b>\n{reversed_text}\n\n"
        f"📏 Символов: <b>{len(source)}</b>",
        reply_markup=back_menu(),
    )


@dp.message()
async def fallback(message: Message) -> None:
    """Любое сообщение вне сценария — возвращаем в меню."""
    await message.answer(
        "Не совсем понял 🤔 Воспользуйся меню 👇", reply_markup=main_menu()
    )


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("Бот запускается...")
    # Сбрасываем накопившиеся апдейты и стартуем long polling.
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
