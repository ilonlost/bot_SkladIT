import telebot
import logging
import time
import traceback
from telebot import types
from config.conn_TG import bot_token
from config.conn_DB import connection_string
from handlers.add_handler import add_menu
from handlers.utill_handler import add_write_off
from handlers.add_cell_handler import cell_menu
from handlers.delete_handler import delete_equipment
from handlers.search_handler import search_equipment
from handlers.inventory_handler import inventory_start
from handlers.add_asset_handler import add_asset
from handlers.scan_qr_handler import request_photo
from config.conn_id import ADMIN_CHAT_ID


conn = connection_string()
bot = telebot.TeleBot(bot_token)



def send_error_message(error_message):
    """
    Функция для отправки сообщения об ошибке администратору.
    """
    bot.send_message(ADMIN_CHAT_ID, error_message)

@bot.message_handler(commands=['a'])
def start(message):
    # Искусственная ошибка
    raise Exception("Тестовая ошибка для проверки функции отправки ошибок")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Используем эмодзи для кнопок
    keyboard.add(
        types.KeyboardButton("➕ Добавить"),
        types.KeyboardButton("🔍 Поиск"),
        types.KeyboardButton("📦 Инвент")
    )
    keyboard.add(
        types.KeyboardButton("🆕 Ячейка"),
        types.KeyboardButton("❌ Удалить"),
        types.KeyboardButton("♻️ Утиль")
    )
    keyboard.add(
        types.KeyboardButton("📤 Выдать"),
        types.KeyboardButton("📸 QR-код")
    )

    bot.send_message(
        message.chat.id,
        " Добро пожаловать на склад! Выберите действие:",
        reply_markup=keyboard
    )

# Обработчик функции "Выдать"
@bot.message_handler(func=lambda message: message.text == "📤 Выдать")
def start_add_process(message):
    add_asset(bot, None, message)

@bot.message_handler(func=lambda message: message.text == "📸 QR-код")
def start_qr_scan_process(message):
    request_photo(message, bot)

# Обработчик функции "Добавить"
@bot.message_handler(func=lambda message: message.text == "➕ Добавить")
def start_add_process(message):
    add_menu(bot, conn, message)

# Обработчик функции "Утиль"
@bot.message_handler(func=lambda message: message.text == "♻️ Утиль")
def start_write_off_process(message):
    add_write_off(bot, conn, message)

# Обработчик функции "Добавить ячейку"
@bot.message_handler(func=lambda message: message.text == "🆕 Ячейка")
def start_add_cell_process(message):
    cell_menu(bot, conn, message)

# Обработчик функции "Удалить"
@bot.message_handler(func=lambda message: message.text == "❌ Удалить")
def start_delete_process(message):
    delete_equipment(bot, conn, message)

# Обработчик функции "Поиск"
@bot.message_handler(func=lambda message: message.text == "🔍 Поиск")
def start_search_process(message):
    search_equipment(bot, conn, message)

# Обработчик функции "Инвентаризация"
@bot.message_handler(func=lambda message: message.text == "📦 Инвент")
def start_inventory_process(message):
    inventory_start(bot, conn, message)

# Обработчик функции "Инвентаризация"
@bot.message_handler(func=lambda message: message.text == "Меню")
def return_to_main_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)


    # Используем эмодзи для кнопок
    keyboard.add(
        types.KeyboardButton("➕ Добавить"),
        types.KeyboardButton("🔍 Поиск"),
        types.KeyboardButton("📦 Инвент")
    )
    keyboard.add(
        types.KeyboardButton("🆕 Ячейка"),
        types.KeyboardButton("❌ Удалить"),

        types.KeyboardButton("♻️ Утиль")
    )
    keyboard.add(
        types.KeyboardButton("📤 Выдать"),
        types.KeyboardButton("📸 Сканировать QR-код")
    )

    bot.send_message(
        message.chat.id,
        " Вы вернулись в основное меню! Выберите действие:",
        reply_markup=keyboard
    )

def main():
    while True:
        try:
            logging.info("Bot started")
            bot.polling(none_stop=True)
        except Exception as e:
            error_message = f"Произошла ошибка: {str(e)}\n{traceback.format_exc()}"
            send_error_message(error_message)
            logging.error(f"Bot crashed: {e}")
            time.sleep(5)  # Ждем перед перезапуском

if __name__ == '__main__':
    main()
