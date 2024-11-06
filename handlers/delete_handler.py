# handlers/delete_handler.py

def delete_equipment(bot, conn, message):
    msg = bot.send_message(message.chat.id, "🔍 *Введите название оборудования для удаления:*")
    bot.register_next_step_handler(msg, lambda m: find_equipment_to_delete(bot, conn, m))


def find_equipment_to_delete(bot, conn, message):
    equipment_name = message.text.strip()
    cursor = conn.cursor()

    # Поиск оборудования по названию
    query = "SELECT id, name, quantity FROM Equipment WHERE name LIKE ?"
    cursor.execute(query, ('%' + equipment_name + '%',))
    results = cursor.fetchall()

    if results:
        response = "📦 *Найдено оборудование:*\n\n"
        for row in results:
            response += (
                f"🔍 *ID:* {row.id}\n"
                f"🛠 *Название:* {row.name}\n"
                f"🔢 *Количество:* {row.quantity}\n"
                f"{'-' * 30}\n"
            )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')

        response += "📥 *Введите ID оборудования, которое хотите удалить:*"
        bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(message, lambda m: confirm_delete_equipment(bot, conn, m, results))
    else:
        bot.send_message(message.chat.id,
                         "❌ *Оборудование не найдено.* Пожалуйста, проверьте название и попробуйте снова.")


def confirm_delete_equipment(bot, conn, message, equipment_list):
    equipment_id = message.text.strip()

    # Проверка, что введено валидное ID
    if not equipment_id.isdigit() or int(equipment_id) not in [row[0] for row in equipment_list]:
        bot.send_message(message.chat.id, "⚠️ *Неверный ID.* Пожалуйста, попробуйте снова.")
        return

    equipment_details = next(row for row in equipment_list if row[0] == int(equipment_id))
    quantity_in_stock = equipment_details[2]  # Количество доступного оборудования

    msg = bot.send_message(message.chat.id,
                           f"🔢 *Текущая доступность:* {quantity_in_stock}.\n"
                           f"📉 *Введите количество для удаления (1 - {quantity_in_stock}):*")
    bot.register_next_step_handler(msg, lambda m: process_deletion(bot, conn, m, equipment_id, quantity_in_stock))


def process_deletion(bot, conn, message, equipment_id, quantity_in_stock):
    quantity_to_delete = message.text.strip()

    # Проверка ввода
    if not quantity_to_delete.isdigit() or int(quantity_to_delete) <= 0:
        bot.send_message(message.chat.id, "⚠️ *Неверное количество.* Пожалуйста, введите положительное число.")
        return

    quantity_to_delete = int(quantity_to_delete)

    if quantity_to_delete > quantity_in_stock:
        bot.send_message(message.chat.id,
                         f"⚠️ *Невозможно удалить указанное количество.* Доступно только {quantity_in_stock} единиц(ы) оборудования.")
        return

    # Уменьшение количества оборудования
    cursor = conn.cursor()

    try:
        # Обновление количества
        update_query = "UPDATE Equipment SET quantity = quantity - ? WHERE id = ?"
        cursor.execute(update_query, (quantity_to_delete, equipment_id))

        # Если количество оборудования после обновления равно нулю, то удаляем оборудование
        if quantity_in_stock - quantity_to_delete == 0:
            # Удаление связанные записи
            delete_related_query = "DELETE FROM Equipment_Cell WHERE equipment_id = ?"
            cursor.execute(delete_related_query, (equipment_id,))

            # Теперь удаляем оборудование
            delete_query = "DELETE FROM Equipment WHERE id = ?"
            cursor.execute(delete_query, (equipment_id,))

        conn.commit()
        bot.send_message(message.chat.id, f"✅ *{quantity_to_delete} единиц(ы) оборудования успешно удалено(ы).*")

    except Exception as e:
        conn.rollback()  # Откат транзакции в случае ошибки
        bot.send_message(message.chat.id, f"❌ *Произошла ошибка при удалении оборудования:* {str(e)}")
