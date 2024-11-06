import os
from telebot import types
from PIL import Image
from pyzbar.pyzbar import decode

def request_photo(message, bot):
    msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте фото с QR-кодом.")

    bot.register_next_step_handler(msg, bot, handle_photo)


def handle_photo(message, bot):

    if message.content_type == 'photo':

        file_info = bot.get_file(message.photo[-1].file_id)
        file = bot.download_file(file_info.file_path)


        temp_file_path = "temp_qr.jpg"
        with open(temp_file_path, "wb") as new_file:
            new_file.write(file)

        try:
            image = Image.open(temp_file_path)
            decoded_objects = decode(image)
            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                bot.send_message(message.chat.id, f"Содержимое QR-кода: {qr_data}")
            else:
                bot.send_message(message.chat.id, "QR-код не удалось расшифровать.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при обработке изображения: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


def main_menu(bot, message):

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

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