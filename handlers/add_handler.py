from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
import qrcode
import telebot


def return_to_main_menu(bot, message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)


    keyboard.add(
        telebot.types.KeyboardButton("➕ Добавить"),
        telebot.types.KeyboardButton("🔍 Поиск"),
        telebot.types.KeyboardButton("📦 Инвент")
    )
    keyboard.add(
        telebot.types.KeyboardButton("🆕 Ячейка"),
        telebot.types.KeyboardButton("❌ Удалить"),
        telebot.types.KeyboardButton("♻️ Утиль")
    )
    keyboard.add(
        telebot.types.KeyboardButton("📤 Выдать"),
        telebot.types.KeyboardButton("📸 Сканировать QR-код")
    )

    bot.send_message(
        message.chat.id,
        "Вы вернулись в основное меню! Выберите действие:",
        reply_markup=keyboard
    )

def add_menu(bot, conn, message):

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    create_btn = telebot.types.KeyboardButton("🆕 Создать")
    edit_btn = telebot.types.KeyboardButton("🛠 Изменить")
    markup.add(create_btn, edit_btn)
    bot.send_message(message.chat.id, "📦 Выберите действие:", reply_markup=markup)

    bot.register_next_step_handler(message, lambda msg: handle_add_action(bot, conn, msg))

def handle_add_action(bot, conn, message):

    if message.text.strip() == "🆕 Создать":
        add_equipment(bot, conn, message)
    elif message.text.strip() == "🛠 Изменить":
        update_equipment(bot, conn, message)
    else:
        bot.send_message(message.chat.id, "❌ Неверный выбор, попробуйте снова.")
        add_menu(bot, conn, message)


def update_equipment(bot, conn, message):
    msg = bot.send_message(message.chat.id, "Отправьте фото QR-кода актива, который хотите изменить:")
    bot.register_next_step_handler(msg, lambda m: process_qr_code_for_update(bot, conn, m))


def process_qr_code_for_update(bot, conn, message):
    if message.content_type == 'photo':
        photo = message.photo[-1].file_id
        file_info = bot.get_file(photo)
        downloaded_file = bot.download_file(file_info.file_path)

        # Считывание QR-код с изображения
        image = Image.open(BytesIO(downloaded_file))
        qr_data = decode(image)

        if qr_data:
            equipment_info = qr_data[0].data.decode('utf-8').split(';')

            if len(equipment_info) < 4:
                bot.send_message(message.chat.id, "QR-код некорректный. Убедитесь, что он содержит все необходимые данные.")
                return

            equipment_name, description, added_by, quantity = equipment_info
            bot.send_message(message.chat.id, f"Вы хотите изменить оборудование:\nНазвание: {equipment_name}\nОписание: {description}\nКоличество: {quantity}\n\nВведите новое название оборудования (или оставьте пустым для отсутствия изменений):")
            bot.register_next_step_handler(message, lambda m: process_new_equipment_name(bot, conn, m, equipment_name, description, quantity))
        else:
            bot.send_message(message.chat.id, "Не удалось считать QR-код.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте изображение QR-кода актива.")


def process_new_equipment_name(bot, conn, message, old_name, old_description, old_quantity):
    new_name = message.text
    new_name = new_name if new_name.strip() else old_name

    msg = bot.send_message(message.chat.id, "Введите новое описание (или оставьте пустым для отсутствия изменений):")
    bot.register_next_step_handler(msg, lambda m: process_new_equipment_quantity(bot, conn, m, new_name, old_description, old_quantity))


def process_new_equipment_quantity(bot, conn, message, new_name, old_description, old_quantity):
    new_description = message.text
    new_description = new_description if new_description.strip() else old_description

    msg = bot.send_message(message.chat.id, "Введите новое количество:")
    bot.register_next_step_handler(msg, lambda m: save_updated_equipment(bot, conn, m, new_name, new_description, old_quantity))


def save_updated_equipment(bot, conn, message, new_name, new_description, old_quantity):
    try:
        new_quantity = int(message.text)

        cursor = conn.cursor()
        query = "UPDATE Equipment SET name = ?, description = ?, quantity = ? WHERE name = ? AND quantity = ?"
        cursor.execute(query, (new_name, new_description, new_quantity, new_name, old_quantity))
        conn.commit()

        bot.send_message(message.chat.id, "Оборудование успешно обновлено.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при обновлении оборудования: {str(e)}")
        return_to_main_menu(bot, message)



def add_equipment(bot, conn, message):
    msg = bot.send_message(message.chat.id, "Введите название оборудования:")
    bot.register_next_step_handler(msg, lambda m: process_equipment_name(bot, conn, m))

def process_equipment_name(bot, conn, message):
    equipment_name = message.text
    msg = bot.send_message(message.chat.id, "Введите описание (не обязательно):")
    bot.register_next_step_handler(msg, lambda m: process_equipment_quantity(bot, conn, m, equipment_name))

def process_equipment_quantity(bot, conn, message, equipment_name):
    description = message.text
    msg = bot.send_message(message.chat.id, "Введите количество:")
    bot.register_next_step_handler(msg, lambda m: save_equipment(bot, conn, m, equipment_name, description))

def save_equipment(bot, conn, message, equipment_name, description):
    try:
        quantity = int(message.text)
        added_by = message.from_user.username
        cursor = conn.cursor()
        query = "INSERT INTO Equipment (name, description, quantity, added_by) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (equipment_name, description, quantity, added_by))
        conn.commit()


        qr_data = f"{equipment_name};{description};{added_by};{quantity}"
        qr_code = qrcode.make(qr_data)
        img_byte_arr = BytesIO()
        qr_code.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)


        bot.send_photo(message.chat.id, img_byte_arr, caption="Ваш QR-код для этого оборудования:")


        msg = bot.send_message(message.chat.id,
                               "Теперь просканируйте QR-код ячейки, куда хотите положить это оборудование:")
        bot.register_next_step_handler(msg, lambda m: handle_qr_cell_scan(bot, conn, m))
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при добавлении оборудования: {str(e)}")
        return_to_main_menu(bot, message)


def handle_qr_cell_scan(bot, conn, message):
    if message.content_type == 'photo':
        photo = message.photo[-1].file_id
        file_info = bot.get_file(photo)
        downloaded_file = bot.download_file(file_info.file_path)


        image = Image.open(BytesIO(downloaded_file))
        qr_data = decode(image)

        if qr_data:
            cell_info = qr_data[0].data.decode('utf-8')
            cell_number = cell_info.strip()
            associate_equipment_to_cell(bot, conn, message.chat.id, cell_number)
        else:
            bot.send_message(message.chat.id, "QR-код ячейки не может быть прочитан.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте изображение QR-кода ячейки.")
        return_to_main_menu(bot, message)
def get_last_equipment_id(conn):
    cursor = conn.cursor()
    query = "SELECT MAX(id) FROM Equipment"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result[0] else None
def associate_equipment_to_cell(bot, conn, chat_id, cell_number, message):
    cursor = conn.cursor()


    query = "SELECT id FROM Cells WHERE cell_number = ?"
    cursor.execute(query, (cell_number,))
    cell = cursor.fetchone()

    if cell:
        equipment_id = get_last_equipment_id(conn)

        query = "INSERT INTO Equipment_Cell (equipment_id, cell_id) VALUES (?, ?)"
        cursor.execute(query, (equipment_id, cell[0]))
        conn.commit()
        bot.send_message(chat_id, "Оборудование успешно привязано к ячейке.")
        return_to_main_menu(bot, message)
    else:
        bot.send_message(chat_id, "Ячейка не найдена.")
        return_to_main_menu(bot, message)
