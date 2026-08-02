import telebot
from telebot.handler_backends import State, StatesGroup
from telebot.custom_filters import StateFilter
from telebot.types import Message
import os
from dotenv import load_dotenv
from states import BookingStates
from keyboards import *
from database import execute_query, fetch_one
import re
import datetime

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(TOKEN)
user_data = {}

# команда /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Добро пожаловать в BeautyCity! Выберите действие:", reply_markup=main_menu())
    bot.set_state(chat_id, None, chat_id)

# главное меню
@bot.message_handler(state=None, func=lambda m: m.text in ['Записаться в салон', 'Записаться к мастеру', 'Записаться на процедуру', 'Записаться по телефону'])
def handle_main_menu(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == 'Записаться в салон':
        bot.set_state(chat_id, BookingStates.choose_salon, chat_id)
        bot.send_message(chat_id, "Выберите салон:", reply_markup=get_salons_kb())
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = 'salon_first'

    elif choice == 'Записаться к мастеру':
        bot.set_state(chat_id, BookingStates.choose_master, chat_id)
        bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_all_masters_kb())
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = 'master_first'

    elif choice == 'Записаться на процедуру':
        bot.set_state(chat_id, BookingStates.choose_service, chat_id)
        bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_all_services_kb())
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = 'service_first'

    elif choice == 'Записаться по телефону':
        row = fetch_one("SELECT phone FROM salons LIMIT 1")
        if row:
            bot.send_message(chat_id, f"Вы можете позвонить нам по телефону: {row[0]}")
        else:
            bot.send_message(chat_id, "Телефон временно недоступен.")
        bot.set_state(chat_id, None, chat_id)

# выбор салона
@bot.message_handler(state=BookingStates.choose_salon)
def process_salon(message):
    chat_id = message.chat.id
    text = message.text

    if text == 'Отмена':
        bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        if chat_id in user_data:
            del user_data[chat_id]
        return

    try:
        salon_id = int(text.split()[0])
    except:
        bot.send_message(chat_id, "Пожалуйста, выберите салон из предложенных кнопок.")
        return

    row = fetch_one("SELECT id FROM salons WHERE id = %s", (salon_id,))
    if not row:
        bot.send_message(chat_id, "Такого салона нет. Выберите из списка.")
        return

    user_data[chat_id]['salon_id'] = salon_id
    bot.set_state(chat_id, BookingStates.choose_service, chat_id)
    bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_services_kb())

# выбор услуги
@bot.message_handler(state=BookingStates.choose_service)
def process_service(message):
    chat_id = message.chat.id
    text = message.text

    if text == 'Отмена':
        bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        del user_data[chat_id]
        return

    if text == 'Назад':
        scenario = user_data.get(chat_id, {}).get('scenario')
        if scenario == 'salon_first':
            bot.set_state(chat_id, BookingStates.choose_salon, chat_id)
            bot.send_message(chat_id, "Выберите салон:", reply_markup=get_salons_kb())
        elif scenario == 'service_first':
            bot.set_state(chat_id, None, chat_id)
            bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
        else:
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_all_masters_kb())
        return

    try:
        service_id = int(text.split()[0])
    except:
        bot.send_message(chat_id, "Выберите услугу из списка.")
        return

    row = fetch_one("SELECT id, price FROM services WHERE id = %s", (service_id,))
    if not row:
        bot.send_message(chat_id, "Такой услуги нет.")
        return

    user_data[chat_id]['service_id'] = service_id
    user_data[chat_id]['price'] = row[1]

    scenario = user_data.get(chat_id, {}).get('scenario')
    if scenario == 'service_first':
        bot.set_state(chat_id, BookingStates.choose_master, chat_id)
        bot.send_message(chat_id, "Выберите мастера, который оказывает эту услугу:", reply_markup=get_masters_by_service_kb(service_id))
        return
    elif scenario == 'master_first':
        bot.set_state(chat_id, BookingStates.choose_time, chat_id)
        bot.send_message(chat_id, "Введите дату в формате ГГГГ-ММ-ДД (например, 2026-08-01):")
        bot.send_message(chat_id, "Пока доступны только даты с сегодня по +7 дней.")
        return
    else: 
        salon_id = user_data[chat_id]['salon_id']
        masters_kb = get_masters_kb(service_id, salon_id)
        if masters_kb.keyboard:
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=masters_kb)
        else:
            bot.send_message(chat_id, "К сожалению, в этом салоне нет мастеров для данной услуги. Попробуйте выбрать другой салон или услугу.")
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите другую услугу:", reply_markup=get_services_kb())

# выбор мастера
@bot.message_handler(state=BookingStates.choose_master)
def process_master(message):
    chat_id = message.chat.id
    text = message.text

    if text == 'Отмена':
        bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        del user_data[chat_id]
        return

    if text == 'Назад':
        scenario = user_data.get(chat_id, {}).get('scenario')
        if scenario == 'master_first':
            bot.set_state(chat_id, None, chat_id)
            bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
        elif scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_all_services_kb())
        else:  # salon_first
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_services_kb())
        return

    try:
        master_id = int(text.split()[0])
    except:
        bot.send_message(chat_id, "Выберите мастера из списка.")
        return

    master_info = fetch_one("SELECT salon_id FROM masters WHERE id = %s", (master_id,))
    if not master_info:
        bot.send_message(chat_id, "Такого мастера нет.")
        return

    salon_id = master_info[0]
    user_data[chat_id]['master_id'] = master_id
    user_data[chat_id]['salon_id'] = salon_id

    scenario = user_data.get(chat_id, {}).get('scenario')
    if scenario == 'master_first':
        bot.set_state(chat_id, BookingStates.choose_service, chat_id)
        bot.send_message(chat_id, "Выберите услугу, которую оказывает мастер:", reply_markup=get_services_by_master_kb(master_id))
        return

    service_id = user_data[chat_id].get('service_id')
    if not service_id:
        bot.send_message(chat_id, "Сначала выберите услугу.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        return

    row = fetch_one("SELECT 1 FROM master_services WHERE master_id = %s AND service_id = %s", (master_id, service_id))
    if not row:
        bot.send_message(chat_id, "Этот мастер не оказывает выбранную услугу. Выберите другого.")
        if scenario == 'service_first':
            bot.send_message(chat_id, "Выберите другого мастера:", reply_markup=get_masters_by_service_kb(service_id))
        else:
            bot.send_message(chat_id, "Выберите другого мастера:", reply_markup=get_masters_kb(service_id, salon_id))
        return

    bot.set_state(chat_id, BookingStates.choose_time, chat_id)
    bot.send_message(chat_id, "Введите дату в формате ГГГГ-ММ-ДД (например, 2026-08-01):")
    bot.send_message(chat_id, "Пока доступны только даты с сегодня по +7 дней.")

# выбор даты и времени
@bot.message_handler(state=BookingStates.choose_time)
def process_time(message):
    chat_id = message.chat.id
    text = message.text

    if text == 'Отмена':
        bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        if chat_id in user_data:
            del user_data[chat_id]
        return

    if text == 'Назад':
        scenario = user_data.get(chat_id, {}).get('scenario')
        if scenario == 'salon_first':
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            service_id = user_data[chat_id]['service_id']
            salon_id = user_data[chat_id]['salon_id']
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_masters_kb(service_id, salon_id))
        elif scenario == 'master_first':
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            master_id = user_data[chat_id]['master_id']
            bot.send_message(chat_id, "Выберите услугу мастера:", reply_markup=get_services_by_master_kb(master_id))
        elif scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            service_id = user_data[chat_id]['service_id']
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_masters_by_service_kb(service_id))
        return

    if not user_data.get(chat_id, {}).get('date_chosen'):
        try:
            date_obj = datetime.datetime.strptime(text, "%Y-%m-%d").date()
            today = datetime.date.today()
            if date_obj < today or date_obj > today + datetime.timedelta(days=7):
                bot.send_message(chat_id, "Дата должна быть от сегодня до +7 дней. Введите другую дату.")
                return
        except ValueError:
            bot.send_message(chat_id, "Неверный формат. Введите дату в формате ГГГГ-ММ-ДД.")
            return

        user_data[chat_id]['date'] = text
        user_data[chat_id]['date_chosen'] = True

        master_id = user_data[chat_id]['master_id']
        slots_kb = get_time_slots_kb(master_id, text)
        if not slots_kb.keyboard or len(slots_kb.keyboard) == 0:
            bot.send_message(chat_id, "На эту дату нет свободного времени. Попробуйте другую дату.")
            del user_data[chat_id]['date_chosen']
            return

        bot.send_message(chat_id, "Выберите свободное время:", reply_markup=slots_kb)
        return

    if not re.match(r'^\d{2}:\d{2}$', text):
        bot.send_message(chat_id, "Пожалуйста, выберите время из предложенных кнопок.")
        return

    master_id = user_data[chat_id]['master_id']
    date_str = user_data[chat_id]['date']
    occupied = fetch_one(
        "SELECT id FROM appointments WHERE master_id = %s AND appointments_date = %s AND appointments_time = %s AND status != 'cancelled'",
        (master_id, date_str, text)
    )
    if occupied:
        bot.send_message(chat_id, "Это время уже занято. Выберите другое.")
        slots_kb = get_time_slots_kb(master_id, date_str)
        bot.send_message(chat_id, "Свободные слоты:", reply_markup=slots_kb)
        return

    user_data[chat_id]['time'] = text
    bot.set_state(chat_id, BookingStates.enter_phone, chat_id)
    bot.send_message(chat_id, "Укажите ваш номер телефона для подтверждения записи (в формате +7XXXXXXXXXX):")

# ввод телефона
@bot.message_handler(state=BookingStates.enter_phone)
def process_phone(message):
    chat_id = message.chat.id
    text = message.text

    if text == 'Отмена':
        bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        del user_data[chat_id]
        return

    if text == 'Назад':
        bot.set_state(chat_id, BookingStates.choose_time, chat_id)
        bot.send_message(chat_id, "Введите дату в формате ГГГГ-ММ-ДД:")
        return

    if not re.match(r'^\+7\d{10}$', text):
        bot.send_message(chat_id, "Некорректный номер. Введите в формате +7XXXXXXXXXX (10 цифр после +7).")
        return

    user_data[chat_id]['phone'] = text

    required_keys = ['salon_id', 'service_id', 'master_id', 'date', 'time']
    missing_keys = [key for key in required_keys if key not in user_data[chat_id]]
    if missing_keys:
        if 'service_id' in missing_keys and 'master_id' in user_data[chat_id]:
            bot.send_message(
                chat_id,
                "Вы не выбрали услугу. Сейчас мы это исправим.",
                reply_markup=main_menu()
            )
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            master_id = user_data[chat_id]['master_id']
            bot.send_message(chat_id, "Выберите услугу, которую оказывает мастер:", reply_markup=get_services_by_master_kb(master_id))
        else:
            bot.send_message(
                chat_id,
                "Похоже, процесс записи был прерван. Начните заново, пожалуйста.",
                reply_markup=main_menu()
            )
            bot.set_state(chat_id, None, chat_id)
            if chat_id in user_data:
                del user_data[chat_id]
        return

    client = fetch_one("SELECT id FROM clients WHERE id = %s", (chat_id,))
    if client:
        client_id = client[0]
        execute_query("UPDATE clients SET phone = %s WHERE id = %s", (text, chat_id))
    else:
        execute_query(
            "INSERT INTO clients (id, phone) VALUES (%s, %s)",
            (chat_id, text)
        )
        client_id = chat_id

    user_data[chat_id]['client_id'] = client_id
    bot.set_state(chat_id, BookingStates.confirm, chat_id)

    try:
        salon = fetch_one('SELECT address FROM salons WHERE id=%s', (user_data[chat_id]['salon_id'],))[0]
        service = fetch_one('SELECT name FROM services WHERE id=%s', (user_data[chat_id]['service_id'],))[0]
        master = fetch_one('SELECT full_name FROM masters WHERE id=%s', (user_data[chat_id]['master_id'],))[0]
    except Exception as e:
        bot.send_message(chat_id, "Ошибка при получении данных. Попробуйте ещё раз.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        del user_data[chat_id]
        return

    summary = (
        f"Проверьте данные:\n"
        f"Салон: {salon}\n"
        f"Услуга: {service}\n"
        f"Мастер: {master}\n"
        f"Дата: {user_data[chat_id]['date']}\n"
        f"Время: {user_data[chat_id]['time']}\n"
        f"Телефон: {text}"
    )
    bot.send_message(chat_id, summary, reply_markup=get_confirm_kb())

# подтверждение записи
@bot.message_handler(state=BookingStates.confirm)
def process_confirm(message):
    chat_id = message.chat.id
    text = message.text

    required_keys = ['client_id', 'master_id', 'service_id', 'date', 'time']
    if chat_id not in user_data or any(key not in user_data[chat_id] for key in required_keys):
        bot.send_message(chat_id, "Ошибка: данные утеряны. Начните запись заново.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        if chat_id in user_data:
            del user_data[chat_id]
        return

    if text == 'Отмена':
        bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        if chat_id in user_data:
            del user_data[chat_id]
        return

    if text == 'Изменить данные':
        scenario = user_data[chat_id].get('scenario', 'salon_first')
        if chat_id in user_data:
            del user_data[chat_id]
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = scenario

        if scenario == 'salon_first':
            bot.send_message(chat_id, "Начните заново выбор салона.")
            bot.set_state(chat_id, BookingStates.choose_salon, chat_id)
            bot.send_message(chat_id, "Выберите салон:", reply_markup=get_salons_kb())
        elif scenario == 'master_first':
            bot.send_message(chat_id, "Начните заново выбор мастера.")
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_all_masters_kb())
        elif scenario == 'service_first':
            bot.send_message(chat_id, "Начните заново выбор услуги.")
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_all_services_kb())
        return

    if text == 'Подтвердить запись':
        data = user_data[chat_id]
        execute_query(
            """INSERT INTO appointments 
               (client_id, master_id, service_id, appointments_date, appointments_time, status)
               VALUES (%s, %s, %s, %s, %s, 'confirmed')""",
            (data['client_id'], data['master_id'], data['service_id'], data['date'], data['time'])
        )
        bot.send_message(chat_id, "✅ Запись успешно создана! Мы ждём вас.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
        del user_data[chat_id]
        return

    bot.send_message(chat_id, "Пожалуйста, используйте кнопки подтверждения.")