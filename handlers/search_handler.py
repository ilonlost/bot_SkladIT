def search_equipment(bot, conn, message):
    msg = bot.send_message(message.chat.id, "Введите название оборудования для поиска:")
    bot.register_next_step_handler(msg, lambda m: handle_search(bot, conn, m))

def handle_search(bot, conn, message):
    search_query = message.text.strip()
    cursor = conn.cursor()

    # Запрос с LIKE для поиска по разным полям
    query = """SELECT e.*, c.short_name, c.description
               FROM Equipment e
               LEFT JOIN Equipment_Cell ec ON e.id = ec.equipment_id
               LEFT JOIN Cells c ON ec.cell_id = c.id
               WHERE e.name LIKE ? OR e.description LIKE ? OR c.short_name LIKE ? OR c.description LIKE ?"""

    cursor.execute(query, (
        '%' + search_query + '%',
        '%' + search_query + '%',
        '%' + search_query + '%',
        '%' + search_query + '%'
    ))
    results = cursor.fetchall()

    if results:
        response = "📦 *Найдено оборудование:*\n\n"
        for row in results:
            cell_info = row.short_name if row.short_name else "Не привязано"
            response += (
                f"🔍 *ID:* {row.id}\n"
                f"🛠 *Название:* {row.name}\n"
                f"📜 *Описание:* {row.description}\n"
                f"🔢 *Количество:* {row.quantity}\n"
                f"👤 *Добавил:* {row.added_by}\n"
                f"📅 *Когда:* {row.added_on}\n"
                f"🏷 *Ячейка:* {cell_info}\n"
                f"{'-' * 30}\n"
            )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Оборудование не найдено.")
