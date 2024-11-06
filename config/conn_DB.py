import pyodbc

def connection_string():
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};Server="Сервер базы данных";Database="База данных";UID="логин";PWD="пароль";"
    )
    return pyodbc.connect(connection_string)