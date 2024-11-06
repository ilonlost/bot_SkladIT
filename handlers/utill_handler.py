from datetime import datetime
from io import BytesIO
import qrcode


def add_write_off(bot, conn, message):
    msg = bot.send_message(message.chat.id,
                           "🔍 *Введите название оборудования для списания (или его часть):*",
                           parse_mode='Markdown')
    bot.register_next_step_handler(msg, lambda m: process_write_off_equipment_name(bot, conn, m))


def process_write_off_equipment_name(bot, conn, message):
    equipment_name = message.text.strip()
    cursor = conn.cursor()


    query = "SELECT id, name, quantity FROM Equipment WHERE name LIKE ?"
    cursor.execute(query, ('%' + equipment_name + '%',))
    equipment = cursor.fetchall()

    if equipment:

        response = "📦 *Найдено оборудование:*\n\n"
        for row in equipment:
            response += (
                f"🔍 *ID:* {row.id}\n"
                f"🛠 *Название:* {row.name}\n"
                f"🔢 *Количество:* {row.quantity}\n"
                f"{'-' * 30}\n"
            )
        msg = bot.send_message(
            message.chat.id,
            response + "✏️ *Введите ID оборудования для списания:*",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, lambda m: save_write_off(bot, conn, m,
                                                                     equipment))
    else:
        bot.send_message(message.chat.id,
                         "❌ *Оборудование не найдено. Пожалуйста, проверьте введенное название и попробуйте снова.*",
                         parse_mode='Markdown')


def save_write_off(bot, conn, message, equipment):
    equipment_id = int(message.text.strip())
    cursor = conn.cursor()


    selected_equipment = next((item for item in equipment if item[0] == equipment_id), None)

    if not selected_equipment:
        bot.send_message(message.chat.id,
                         "❌ *Ошибка: Указан неверный ID. Пожалуйста, попробуйте снова.*",
                         parse_mode='Markdown')
        return

    # Запрашиваем причину списания
    msg = bot.send_message(message.chat.id,
                           "✏️ *Введите причину списания:*",
                           parse_mode='Markdown')


    bot.register_next_step_handler(msg, lambda m: perform_write_off(bot, conn, m, selected_equipment, equipment_id))


def perform_write_off(bot, conn, message, selected_equipment, equipment_id):
    reason = message.text.strip()  # Получаем причину списания
    written_off_by = message.from_user.username
    written_off_on = datetime.now()
    current_quantity = selected_equipment[2]


    query = """
    INSERT INTO WriteOffs (equipment_id, reason, written_off_by, written_off_on) 
    VALUES (?, ?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(query, (equipment_id, reason, written_off_by, written_off_on))


    if current_quantity > 1:
        new_quantity = current_quantity - 1
        update_query = "UPDATE Equipment SET quantity = ? WHERE id = ?"
        cursor.execute(update_query, (new_quantity, equipment_id))
    else:
        delete_query = "DELETE FROM Equipment WHERE id = ?"
        cursor.execute(delete_query, (equipment_id,))

    conn.commit()


    qr_data = f"Причина: {reason}; Кем: {written_off_by}; Когда: {written_off_on.strftime('%Y-%m-%d %H:%M')}"
    qr_code = qrcode.make(qr_data)
    img_byte_arr = BytesIO()
    qr_code.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    bot.send_photo(message.chat.id,
                   img_byte_arr,
                   caption="✅ *Ваш QR-код причины списания оборудования:*",
                   parse_mode='Markdown')

    bot.send_message(message.chat.id,
                     "✅ *Оборудование успешно списано!*",
                     parse_mode='Markdown')
