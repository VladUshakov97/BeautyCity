from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database import fetch_all
import datetime
from config import ALL_TIME_SLOTS


def build_menu(buttons, row_width=2, promo=False, back=True, cancel=True):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)

    for btn in buttons:
        kb.add(KeyboardButton(btn))

    if promo:
        kb.row('У меня есть промокод')

    if back and cancel:
        kb.row('Назад', 'Отмена')
    elif back:
        kb.row('Назад')
    elif cancel:
        kb.row('Отмена')
    return kb


def main_menu():
    return build_menu(['Записаться в салон', 'Записаться к мастеру',
                       'Записаться на процедуру', 'Записаться по телефону'],
                       row_width=2, promo=False, back=False, cancel=False)


def get_salons_kb():
    rows = fetch_all("SELECT id, address FROM salons ORDER BY id")
    buttons = [f"{sid} {addr}" for sid, addr in rows]
    return build_menu(buttons, row_width=1, back=False, cancel=True)


def get_all_services_kb(with_promo=False):
    rows = fetch_all("SELECT id, name, price FROM services ORDER BY id")
    buttons = [f"{sid} {name} — {price}₽" for sid, name, price in rows]
    return build_menu(buttons, row_width=1, promo=with_promo, back=True, cancel=True)


def get_services_kb(salon_id=None, with_promo=True):
    if salon_id:
        query = """
            SELECT DISTINCT s.id, s.name, s.price
            FROM services s
            JOIN master_services ms ON ms.service_id = s.id
            JOIN masters m ON m.id = ms.master_id
            WHERE m.salon_id = %s
            ORDER BY s.id
        """
        rows = fetch_all(query, (salon_id,))
    else:
        rows = fetch_all("SELECT id, name, price FROM services ORDER BY id")
    buttons = [f"{sid} {name} — {price}₽" for sid, name, price in rows]
    return build_menu(buttons, row_width=1, promo=with_promo, back=True, cancel=True)


def get_services_by_master_kb(master_id):
    query = """
        SELECT s.id, s.name, s.price
        FROM services s
        JOIN master_services ms ON s.id = ms.service_id
        WHERE ms.master_id = %s
        ORDER BY s.id
    """
    rows = fetch_all(query, (master_id,))
    buttons = [f"{sid} {name} — {price}₽" for sid, name, price in rows]
    return build_menu(buttons, row_width=1, promo=True, back=True, cancel=True)


def get_all_masters_kb():
    rows = fetch_all("SELECT id, full_name FROM masters ORDER BY id")
    buttons = [f"{mid} {name}" for mid, name in rows]
    return build_menu(buttons, row_width=1, promo=False, back=True, cancel=True)


def get_masters_by_service_kb(service_id):
    query = """
        SELECT m.id, m.full_name
        FROM masters m
        JOIN master_services ms ON m.id = ms.master_id
        WHERE ms.service_id = %s
        ORDER BY m.id
    """
    rows = fetch_all(query, (service_id,))
    buttons = [f"{mid} {name}" for mid, name in rows]
    return build_menu(buttons, row_width=1, promo=False, back=True, cancel=True)


def get_masters_kb(service_id, salon_id):
    query = """
        SELECT m.id, m.full_name
        FROM masters m
        JOIN master_services ms ON m.id = ms.master_id
        WHERE ms.service_id = %s AND m.salon_id = %s
        ORDER BY m.id
    """
    rows = fetch_all(query, (service_id, salon_id))
    buttons = [f"{mid} {name}" for mid, name in rows]
    return build_menu(buttons, row_width=1, promo=False, back=True, cancel=True)


def get_time_slots_kb(master_id, date_str):
    """Возвращает клавиатуру со свободными слотами и список свободных слотов."""
    occupied = fetch_all(
        "SELECT to_char(appointments_time, 'HH24:MI') FROM appointments "
        "WHERE master_id = %s AND appointments_date = %s AND status != 'cancelled'",
        (master_id, date_str)
    )
    occupied_times = [row[0] for row in occupied]
    today = datetime.date.today()

    if date_str == today.strftime("%Y-%m-%d"):
        now = datetime.datetime.now()
        current_time_str = now.strftime("%H:%M")
        free_slots = [t for t in ALL_TIME_SLOTS if t not in occupied_times and t > current_time_str]
    else:
        free_slots = [t for t in ALL_TIME_SLOTS if t not in occupied_times]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    for slot in free_slots:
        kb.add(KeyboardButton(slot))
    kb.row('Назад', 'Отмена')
    return kb, free_slots


def get_confirm_kb():
    return build_menu(['Подтвердить запись', 'Изменить данные'], row_width=2,
                      promo=False, back=False, cancel=True)


def agree_kb():
    return build_menu(['Согласен'], row_width=1, promo=False, back=False, cancel=False)


def get_payment_choice_kb():
    return build_menu(['💳 Оплатить онлайн', '⏰ Позже'], row_width=2,
                      promo=False, back=False, cancel=False)


def get_payment_form_kb():
    return build_menu(['💳 Оплатить', 'Отмена'], row_width=2,
                      promo=False, back=False, cancel=False)


def get_back_cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Назад', 'Отмена')
    return kb
