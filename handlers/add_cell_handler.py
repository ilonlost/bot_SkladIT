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


def cell_menu(bot, conn, message):

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    create_btn = telebot.types.KeyboardButton("🆕 Создать")
    edit_btn = telebot.types.KeyboardButton("🛠 Изменить")
    markup.add(create_btn, edit_btn)
    bot.send_message(message.chat.id, "📦 Выберите действие:", reply_markup=markup)

    bot.register_next_step_handler(message, lambda msg: handle_cell_action(bot, conn, msg))


def handle_cell_action(bot, conn, message):

    if message.text.strip() == "🆕 Создать":
        add_cell(bot, conn, message)
    elif message.text.strip() == "🛠 Изменить":
        request_cell_image(bot, conn, message)
    else:
        bot.send_message(message.chat.id, "❌ Неверный выбор, попробуйте снова.")
        cell_menu(bot, conn, message)


def request_cell_image(bot, conn, message):

    msg = bot.send_message(message.chat.id,
                           "📸 Пожалуйста, отправьте изображение QR-кода ячейки, которую вы хотите изменить.")
    bot.register_next_step_handler(msg, lambda msg: process_cell_image(bot, conn, msg))


def process_cell_image(bot, conn, message):

    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)


        image = Image.open(BytesIO(downloaded_file))
        decoded_objects = decode(image)

        if decoded_objects:
            cell_number = decoded_objects[0].data.decode('utf-8')
            request_cell_change(bot, conn, message, cell_number)
        else:
            bot.send_message(message.chat.id, "❌ Невозможно прочитать QR-код. Пожалуйста, попробуйте еще раз.")
            request_cell_image(bot, conn, message)
    else:
        bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте изображение QR-кода.")
        request_cell_image(bot, conn, message)


def request_cell_change(bot, conn, message, cell_number):

    cursor = conn.cursor()

    try:


        cursor.execute("SELECT * FROM Cells WHERE cell_number = ?", (cell_number,))
        row = cursor.fetchone()

        if row:
            msg = bot.send_message(message.chat.id, "📝 *Введите новое краткое наименование ячейки:*")
            bot.register_next_step_handler(msg, lambda m: process_update_cell(bot, conn, m, cell_number))
        else:
            bot.send_message(message.chat.id, "❌ Ячейка с таким номером не найдена. Пожалуйста, попробуйте еще раз.")
            request_cell_image(bot, conn, message)
    except Exception as e:
        bot.send_message(message.chat.id, f"🚫 Произошла ошибка: {str(e)}")
        return_to_main_menu(bot, message)

    def process_update_cell(bot, conn, message, cell_number):

        short_name = message.text.strip()


        update_cell(bot, conn, message, cell_number, short_name)

    def update_cell(bot, conn, message, cell_number, short_name):

        cursor = conn.cursor()

        try:

            query = "UPDATE Cells SET short_name = ? WHERE cell_number = ?"
            cursor.execute(query, (short_name, cell_number))
            conn.commit()


            bot.send_message(message.chat.id, "✅ *Ячейка успешно изменена.*")
            return_to_main_menu(bot, message)
        except Exception as e:
            bot.send_message(message.chat.id, f"🚫 Не удалось обновить ячейку: {str(e)}")
            return_to_main_menu(bot, message)
def add_cell(bot, conn, message):

        msg = bot.send_message(message.chat.id, "🏷 *Введите номер ячейки:*")
        bot.register_next_step_handler(msg, lambda m: process_cell_number(bot, conn, m))

def process_cell_number(bot, conn, message):

        cell_number = message.text.strip()
        msg = bot.send_message(message.chat.id, "📝 *Введите краткое наименование ячейки:*")
        bot.register_next_step_handler(msg, lambda m: process_cell_description(bot, conn, m, cell_number))

def process_cell_description(bot, conn, message, cell_number):

        short_name = message.text.strip()


        save_cell(bot, conn, message, cell_number, short_name)

def save_cell(bot, conn, message, cell_number, short_name):

        cursor = conn.cursor()

        try:

            query = "INSERT INTO Cells (cell_number, short_name) VALUES (?, ?)"
            cursor.execute(query, (cell_number, short_name))
            conn.commit()


            bot.send_message(message.chat.id, "✅ *Ячейка успешно добавлена.*")


            qr_data = f"{cell_number}"
            qr_code = qrcode.make(qr_data)
            img_byte_arr = BytesIO()

            qr_code.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)


            bot.send_photo(message.chat.id, img_byte_arr, caption="📸 *Ваш QR-код для этой ячейки:*")
            return_to_main_menu(bot, message)
        except Exception as e:
            bot.send_message(message.chat.id, f"🚫 Не удалось сохранить ячейку: {str(e)}")
            return_to_main_menu(bot, message)
