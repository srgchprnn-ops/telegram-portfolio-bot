# 🤖 Telegram-бот-визитка

Демонстрационный Telegram-бот на **Python / aiogram 3**. Презентует услуги, показывает контакты и содержит небольшой интерактивный инструмент. Работает на сервере 24/7 (systemd).

## ✨ Возможности
- Главное меню на инлайн-кнопках
- 📝 **Приём заявок** — клиент описывает задачу и контакт, заявка приходит владельцу в личный чат
- Разделы: «Услуги», «Контакты», «О боте»
- 🔤 **Перевёртыш** — мини-инструмент (демонстрация работы с состояниями FSM)

## 🛠️ Стек
`Python` · `aiogram 3` · `asyncio` · `systemd`

## 🚀 Запуск локально
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # и вписать токен от @BotFather
python bot.py
```

## ⚙️ Деплой на сервер (Ubuntu + systemd)
1. Скопировать проект в `/opt/telegram-portfolio-bot`
2. Создать venv и установить зависимости
3. Положить токен в `/etc/telegram-portfolio-bot.env` (`BOT_TOKEN=...`, права `600`)
4. Установить unit из `deploy/` и запустить:
   ```bash
   systemctl enable --now telegram-portfolio-bot
   ```

> 🔐 Токен бота хранится вне репозитория (в `.env` локально и в `/etc/...env` на сервере) и никогда не коммитится.
