import telebot
import psycopg2
from database_func import connect_to_database


def write_to_database(column, values):
    conn, cursor = connect_to_database()
    query = f'INSERT INTO appointments({column}) VALUES(%s)'
    cursor.execute(query, (values,))
    conn.commit()
    conn.close()


def read_data(column):
    conn, cursor = connect_to_database()
    query = f'SELECT {column} FROM appointments'
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

