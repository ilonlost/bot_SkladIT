# handlers/inventory_handler.py
import telebot
from telebot import types

def inventory_start(bot, conn, message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_inventory_all = telebot.types.KeyboardButton("📦 Склад")
    btn_inventory_cell_text = telebot.types.KeyboardButton("🔍 Ячейка")
    btn_return = telebot.types.KeyboardButton("🏠 Меню")

    markup.add(btn_inventory_all, btn_inventory_cell_text, btn_return)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

    # Регистрация следующего шага для обработки выбора
    bot.register_next_step_handler(message, handle_inventory_choice, bot, conn)


def handle_inventory_choice(message, bot, conn):
    if message.text == "📦 Склад":
        inventory_all(bot, conn, message)
    elif message.text == "🔍 Ячейка":
        msg = bot.send_message(message.chat.id, "Введите номер ячейки:")
        bot.register_next_step_handler(msg, get_inventory_by_cell_number, bot, conn)
    elif message.text == "🏠 Меню":
        return_to_main_menu(bot, message)
    else:
        bot.send_message(message.chat.id, "❌ Выбор не распознан. Пожалуйста, выберите действие заново.")
        inventory_start(bot, conn, message)


def inventory_all(bot, conn, message):
    cursor = conn.cursor()
    query = "SELECT * FROM Equipment"
    cursor.execute(query)
    results = cursor.fetchall()

    if results:
        response = "*Инвентаризация всего склада:*\n\n"
        for row in results:
            response += (
                f"🔧 *ID:* {row.id}\n"
                f"📋 *Название:* {row.name}\n"
                f"🔢 *Количество:* {row.quantity}\n"
                f"{'-' * 30}\n"
            )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "📭 Склад пуст.")

    # Возврат в меню после показа инвентаризации
    return_to_main_menu(bot, message)


def get_inventory_by_cell_number(message, bot, conn):
    cell_number = message.text.strip()
    cursor = conn.cursor()

    # Запрос для получения ID ячейки по её номеру
    query = "SELECT id FROM Cells WHERE cell_number = ?"
    cursor.execute(query, (cell_number,))
    cell = cursor.fetchone()

    if cell:
        cell_id = cell[0]

        # Запрос для получения оборудования в указанной ячейке
        query = """SELECT e.id, e.name, e.description, e.quantity 
                   FROM Equipment e
                   INNER JOIN Equipment_Cell ec ON e.id = ec.equipment_id
                   WHERE ec.cell_id = ?"""
        cursor.execute(query, (cell_id,))
        results = cursor.fetchall()

        if results:
            response = f"*Инвентаризация для ячейки '{cell_number}':*\n\n"
            for row in results:
                response += (
                    f"🔍 *ID:* {row.id}\n"
                    f"🛠 *Название:* {row.name}\n"
                    f"📜 *Описание:* {row.description}\n"
                    f"🔢 *Количество:* {row.quantity}\n"
                    f"{'-' * 30}\n"
                )

            bot.send_message(message.chat.id, response, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"😞 В ячейке '{cell_number}' нет оборудования.")
    else:
        bot.send_message(message.chat.id, f"⚠️ Ячейка с номером '{cell_number}' не найдена.")

    # Возврат в меню после показа инвентаризации
    return_to_main_menu(bot, message)


def return_to_main_menu(bot, message):
    # Создание клавиатуры с кнопками
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
        "🤖 Вы вернулись в основное меню! Выберите действие:",
        reply_markup=keyboard
    )
