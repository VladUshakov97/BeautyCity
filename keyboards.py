from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database import fetch_all


def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Записаться в салон', 'Записаться к мастеру')
    kb.row('Записаться на процедуру', 'Записаться по телефону')
    return kb


def get_salons_kb():
    rows = fetch_all("SELECT id, address FROM salons ORDER BY id")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for sid, addr in rows:
        kb.add(KeyboardButton(f"{sid} {addr}"))
    kb.row('Отмена')
    return kb


def get_services_kb(salon_id=None):
    rows = fetch_all("SELECT id, name, price FROM services ORDER BY id")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for sid, name, price in rows:
        kb.add(KeyboardButton(f"{sid} {name} — {price}₽"))
    kb.row('Назад', 'Отмена')
    return kb


def get_masters_kb(service_id, salon_id):
    query = """
        SELECT m.id, m.full_name 
        FROM masters m
        JOIN master_services ms ON m.id = ms.master_id
        WHERE ms.service_id = %s AND m.salon_id = %s
        ORDER BY m.id
    """
    rows = fetch_all(query, (service_id, salon_id))
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for mid, name in rows:
        kb.add(KeyboardButton(f"{mid} {name}"))
    kb.row('Назад', 'Отмена')
    return kb


def get_time_slots_kb(master_id, date_str):
    occupied = fetch_all(
        "SELECT appointments_time FROM appointments WHERE master_id = %s AND appointments_date = %s AND status != 'cancelled'",
        (master_id, date_str)
    )
    occupied_times = [row[0] for row in occupied]

    all_slots = ['10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00']
    free_slots = [t for t in all_slots if t not in occupied_times]

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    row = []
    for i, slot in enumerate(free_slots):
        row.append(KeyboardButton(slot))
        if len(row) == 3:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    kb.row('Назад', 'Отмена')
    return kb


def get_confirm_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Подтвердить запись', 'Изменить данные')
    kb.row('Отмена')
    return kb


def get_back_cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Назад', 'Отмена')
    return kb


def write_feedback(feedback):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Оставить отзыв')
    return kb


def get_all_masters():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    masters = fetch_all("SELECT full_name, id FROM masters")

    for full_name, id in masters:
        kb.add(KeyboardButton(full_name))

    kb.row('Назад', 'Отмена')
