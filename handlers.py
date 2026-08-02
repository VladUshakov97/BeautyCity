import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv
from states import BookingStates
from keyboards import *
from database import execute_query, fetch_one
import re
import datetime


load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
PROMO_CODES = {
    'kid20': 20,
    'birthday': 15,
    'man10': 10
}

bot = telebot.TeleBot(TOKEN)
user_data = {}


def apply_promo(price, code):
    if code in PROMO_CODES:
        discount = PROMO_CODES[code]
        new_price = price - (price * discount // 100)
        return new_price, discount
    return price, 0


# КАЛЕНДАРЬ
def create_calendar(year, month):
    kb = InlineKeyboardMarkup(row_width=7)
    kb.row(
        InlineKeyboardButton("◀", callback_data=f"prev_{year}_{month}"),
        InlineKeyboardButton(f"{month:02d}.{year}", callback_data="ignore"),
        InlineKeyboardButton("▶", callback_data=f"next_{year}_{month}")
    )
    kb.row(*[InlineKeyboardButton(d, callback_data="ignore") for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])
    first_day = datetime.date(year, month, 1)
    start_weekday = first_day.weekday()

    if month == 12:
        next_month = datetime.date(year+1, 1, 1)
    else:
        next_month = datetime.date(year, month+1, 1)
    num_days = (next_month - datetime.timedelta(days=1)).day
    row = []

    for _ in range(start_weekday):
        row.append(InlineKeyboardButton(" ", callback_data="ignore"))

    for day in range(1, num_days+1):
        row.append(InlineKeyboardButton(str(day), callback_data=f"date_{year}-{month:02d}-{day:02d}"))

        if len(row) == 7:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    return kb


def show_calendar(chat_id):
    now = datetime.datetime.now()
    bot.send_message(chat_id, "📅 Выберите дату:", reply_markup=create_calendar(now.year, now.month))


# ОБРАБОТЧИК КАЛЕНДАРЯ
@bot.callback_query_handler(func=lambda call: call.data.startswith(("date_", "prev_", "next_")))
def calendar_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("date_"):
        date_str = data.split("_")[1]
        selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.date.today()

        if selected_date < today or selected_date > today + datetime.timedelta(days=7):
            bot.answer_callback_query(call.id, "Можно записаться только на даты от сегодня до +7 дней.")
            return
        user_data[chat_id]['date'] = date_str
        user_data[chat_id]['date_chosen'] = True
        bot.edit_message_reply_markup(chat_id, call.message.message_id)
        master_id = user_data[chat_id]['master_id']
        slots_kb, free_slots = get_time_slots_kb(master_id, date_str)

        if not free_slots:
            bot.send_message(chat_id, "На эту дату нет свободного времени. Попробуйте другую.")
            del user_data[chat_id]['date_chosen']
            show_calendar(chat_id)
            return
        bot.send_message(chat_id, "Выберите свободное время:", reply_markup=slots_kb)
        bot.answer_callback_query(call.id)
    elif data.startswith("prev_"):
        _, year, month = data.split("_")
        year, month = int(year), int(month)
        month -= 1

        if month == 0:
            month = 12
            year -= 1
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=create_calendar(year, month))
        bot.answer_callback_query(call.id)
    elif data.startswith("next_"):
        _, year, month = data.split("_")
        year, month = int(year), int(month)
        month += 1

        if month == 13:
            month = 1
            year += 1
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=create_calendar(year, month))
        bot.answer_callback_query(call.id)


# КОМАНДА /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    client = fetch_one("SELECT agreed FROM clients WHERE id = %s", (chat_id,))

    if client and client[0]:
        bot.send_message(chat_id, "Добро пожаловать в BeautyCity! Выберите действие:", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
    else:
        file_path = 'agreement.docx'

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            file_path = 'agreement.txt'

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                bot.send_message(chat_id, "Файл с согласием не найден или пуст. Пожалуйста, свяжитесь с администратором.")
                return

        try:
            with open(file_path, 'rb') as f:
                bot.send_document(chat_id, f)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при отправке файла: {e}")
            return

        bot.send_message(
            chat_id,
            "Для использования бота необходимо дать согласие на обработку персональных данных.\n"
            "Ознакомьтесь с документом и нажмите 'Согласен'.",
            reply_markup=agree_kb()
        )
        bot.set_state(chat_id, BookingStates.accept_personal_data, chat_id)


# ОБРАБОТЧИК СОГЛАСИЯ
@bot.message_handler(state=BookingStates.accept_personal_data)
def accept_personal_data(message):
    chat_id = message.chat.id

    if message.text == 'Согласен':
        client = fetch_one("SELECT id FROM clients WHERE id = %s", (chat_id,))

        if client:
            execute_query("UPDATE clients SET agreed = TRUE WHERE id = %s", (chat_id,))
        else:
            execute_query(
                "INSERT INTO clients (id, agreed) VALUES (%s, TRUE)",
                (chat_id,)
            )
        bot.send_message(chat_id, "Спасибо! Теперь вы можете пользоваться ботом.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)
    else:
        bot.send_message(
            chat_id,
            "Для использования бота необходимо дать согласие на обработку данных.",
            reply_markup=agree_kb()
        )


# ГЛАВНОЕ МЕНЮ
@bot.message_handler(state=None, func=lambda m: m.text in ['Записаться в салон', 'Записаться к мастеру', 'Записаться на процедуру', 'Записаться по телефону'])
def handle_main_menu(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == 'Записаться в салон':
        bot.set_state(chat_id, BookingStates.choose_salon, chat_id)
        bot.send_message(chat_id, "Выберите салон:", reply_markup=get_salons_kb())
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = 'salon_first'
        user_data[chat_id]['original_price'] = 0
        user_data[chat_id]['final_price'] = 0
    elif choice == 'Записаться к мастеру':
        bot.set_state(chat_id, BookingStates.choose_master, chat_id)
        bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_all_masters_kb())
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = 'master_first'
        user_data[chat_id]['original_price'] = 0
        user_data[chat_id]['final_price'] = 0
    elif choice == 'Записаться на процедуру':
        bot.set_state(chat_id, BookingStates.choose_service, chat_id)
        bot.send_message(chat_id, "Выберите услугу (или введите промокод):", reply_markup=get_all_services_kb(with_promo=True))
        user_data[chat_id] = {}
        user_data[chat_id]['scenario'] = 'service_first'
        user_data[chat_id]['original_price'] = 0
        user_data[chat_id]['final_price'] = 0
    elif choice == 'Записаться по телефону':
        row = fetch_one("SELECT phone FROM salons LIMIT 1")

        if row:
            bot.send_message(chat_id, f"Вы можете позвонить нам по телефону: {row[0]}")
        else:
            bot.send_message(chat_id, "Телефон временно недоступен.")
        bot.set_state(chat_id, None, chat_id)


# ВЫБОР САЛОНА
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

    if text == 'У меня есть промокод':
        bot.set_state(chat_id, BookingStates.promo, chat_id)
        bot.send_message(chat_id, "Введите ваш промокод:")
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
    services_kb = get_services_kb(salon_id, with_promo=True)

    if not services_kb.keyboard:
        bot.send_message(chat_id, "В этом салоне пока нет доступных услуг. Выберите другой салон.", reply_markup=get_salons_kb())
        return
    bot.send_message(chat_id, "Выберите услугу (или введите промокод):", reply_markup=services_kb)


# ВЫБОР УСЛУГИ
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
        else:  # master_first
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_all_masters_kb())
        return

    if text == 'У меня есть промокод':
        bot.set_state(chat_id, BookingStates.promo, chat_id)
        bot.send_message(chat_id, "Введите ваш промокод:")
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
    user_data[chat_id]['original_price'] = row[1]
    user_data[chat_id]['final_price'] = row[1]

    if 'pending_promo' in user_data[chat_id]:
        pending = user_data[chat_id]['pending_promo']

        if pending in PROMO_CODES:
            discount = PROMO_CODES[pending]
            new_price = row[1] - (row[1] * discount // 100)
            user_data[chat_id]['final_price'] = new_price
            user_data[chat_id]['promo_code'] = pending
            bot.send_message(
                chat_id,
                f"✅ Промокод '{pending}' применён! Скидка {discount}%.\n"
                f"Цена была: {row[1]}₽, стала: {new_price}₽."
            )
        del user_data[chat_id]['pending_promo']

    scenario = user_data.get(chat_id, {}).get('scenario')

    if scenario == 'service_first':
        bot.set_state(chat_id, BookingStates.choose_master, chat_id)
        bot.send_message(chat_id, "Выберите мастера, который оказывает эту услугу:", reply_markup=get_masters_by_service_kb(service_id))
        return
    elif scenario == 'master_first':
        bot.set_state(chat_id, BookingStates.choose_time, chat_id)
        show_calendar(chat_id)
        return
    else:  # salon_first
        salon_id = user_data[chat_id]['salon_id']
        masters_kb = get_masters_kb(service_id, salon_id)

        if masters_kb.keyboard:
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=masters_kb)
        else:
            bot.send_message(chat_id, "К сожалению, в этом салоне нет мастеров для данной услуги. Попробуйте выбрать другой салон или услугу.")
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            services_kb = get_services_kb(salon_id, with_promo=True)
            bot.send_message(chat_id, "Выберите другую услугу:", reply_markup=services_kb)


# ОБРАБОТЧИК ПРОМОКОДА
@bot.message_handler(state=BookingStates.promo)
def process_promo(message):
    chat_id = message.chat.id
    text = message.text.strip().lower()

    if text in ['отмена', 'назад']:
        scenario = user_data.get(chat_id, {}).get('scenario')

        if scenario == 'salon_first':
            salon_id = user_data.get(chat_id, {}).get('salon_id')

            if salon_id:
                bot.set_state(chat_id, BookingStates.choose_service, chat_id)
                services_kb = get_services_kb(salon_id, with_promo=True)
                bot.send_message(chat_id, "Выберите услугу (или введите промокод):", reply_markup=services_kb)
            else:
                bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
                bot.set_state(chat_id, None, chat_id)
        elif scenario == 'master_first':
            master_id = user_data.get(chat_id, {}).get('master_id')

            if master_id:
                bot.set_state(chat_id, BookingStates.choose_service, chat_id)
                bot.send_message(chat_id, "Выберите услугу, которую оказывает мастер (или введите промокод):", reply_markup=get_services_by_master_kb(master_id))
            else:
                bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
                bot.set_state(chat_id, None, chat_id)
        elif scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите услугу (или введите промокод):", reply_markup=get_all_services_kb(with_promo=True))
        else:
            bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
            bot.set_state(chat_id, None, chat_id)
        return
    original_price = user_data.get(chat_id, {}).get('original_price', 0)

    if original_price == 0:
        user_data[chat_id]['pending_promo'] = text
        bot.send_message(chat_id, "Промокод сохранён. Теперь выберите услугу, и скидка применится автоматически.")
        scenario = user_data.get(chat_id, {}).get('scenario')

        if scenario == 'salon_first':
            salon_id = user_data[chat_id].get('salon_id')

            if salon_id:
                bot.set_state(chat_id, BookingStates.choose_service, chat_id)
                services_kb = get_services_kb(salon_id, with_promo=True)
                bot.send_message(chat_id, "Выберите услугу:", reply_markup=services_kb)
            else:
                bot.send_message(chat_id, "Начните запись заново.", reply_markup=main_menu())
                bot.set_state(chat_id, None, chat_id)
        elif scenario == 'master_first':
            master_id = user_data[chat_id].get('master_id')

            if master_id:
                bot.set_state(chat_id, BookingStates.choose_service, chat_id)
                bot.send_message(chat_id, "Выберите услугу, которую оказывает мастер:", reply_markup=get_services_by_master_kb(master_id))
            else:
                bot.send_message(chat_id, "Сначала выберите мастера.", reply_markup=main_menu())
                bot.set_state(chat_id, None, chat_id)
        elif scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_all_services_kb(with_promo=True))
        else:
            bot.send_message(chat_id, "Начните запись заново.", reply_markup=main_menu())
            bot.set_state(chat_id, None, chat_id)
        return

    if text in PROMO_CODES:
        discount = PROMO_CODES[text]
        new_price = original_price - (original_price * discount // 100)
        user_data[chat_id]['final_price'] = new_price
        user_data[chat_id]['promo_code'] = text
        bot.send_message(
            chat_id,
            f"✅ Промокод '{text}' применён! Скидка {discount}%.\n"
            f"Цена была: {original_price}₽, стала: {new_price}₽."
        )
        scenario = user_data.get(chat_id, {}).get('scenario')
        service_id = user_data[chat_id].get('service_id')
        master_id = user_data[chat_id].get('master_id')

        if scenario == 'salon_first' and service_id:
            salon_id = user_data[chat_id]['salon_id']
            masters_kb = get_masters_kb(service_id, salon_id)

            if masters_kb.keyboard:
                bot.set_state(chat_id, BookingStates.choose_master, chat_id)
                bot.send_message(chat_id, "Выберите мастера:", reply_markup=masters_kb)
            else:
                bot.send_message(chat_id, "К сожалению, в этом салоне нет мастеров для данной услуги. Попробуйте выбрать другой салон или услугу.")
                bot.set_state(chat_id, BookingStates.choose_service, chat_id)
                services_kb = get_services_kb(salon_id, with_promo=True)
                bot.send_message(chat_id, "Выберите другую услугу:", reply_markup=services_kb)
        elif scenario == 'master_first' and service_id and master_id:
            bot.set_state(chat_id, BookingStates.choose_time, chat_id)
            show_calendar(chat_id)
        elif scenario == 'service_first' and service_id:
            masters_kb = get_masters_by_service_kb(service_id)

            if masters_kb.keyboard:
                bot.set_state(chat_id, BookingStates.choose_master, chat_id)
                bot.send_message(chat_id, "Выберите мастера, который оказывает эту услугу:", reply_markup=masters_kb)
            else:
                bot.send_message(chat_id, "К сожалению, нет мастеров для данной услуги. Попробуйте выбрать другую услугу.")
                bot.set_state(chat_id, BookingStates.choose_service, chat_id)
                bot.send_message(chat_id, "Выберите другую услугу:", reply_markup=get_all_services_kb(with_promo=True))
        else:
            bot.send_message(chat_id, "Не хватает данных. Начните заново.", reply_markup=main_menu())
            bot.set_state(chat_id, None, chat_id)
    else:
        bot.send_message(chat_id, "❌ Неверный промокод. Попробуйте ещё раз или введите 'Отмена' для выхода.")
        bot.set_state(chat_id, BookingStates.promo, chat_id)


# ВЫБОР МАСТЕРА
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
            bot.send_message(chat_id, "Выберите услугу (или введите промокод):", reply_markup=get_all_services_kb(with_promo=True))
        else:  # salon_first
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            salon_id = user_data[chat_id]['salon_id']
            services_kb = get_services_kb(salon_id, with_promo=True)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=services_kb)
        return

    if text == 'У меня есть промокод':
        bot.set_state(chat_id, BookingStates.promo, chat_id)
        bot.send_message(chat_id, "Введите ваш промокод:")
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
        bot.send_message(chat_id, "Выберите услугу, которую оказывает мастер (или введите промокод):", reply_markup=get_services_by_master_kb(master_id))
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
        else:  # salon_first
            bot.send_message(chat_id, "Выберите другого мастера:", reply_markup=get_masters_kb(service_id, salon_id))
        return
    bot.set_state(chat_id, BookingStates.choose_time, chat_id)
    show_calendar(chat_id)


# FALLBACK ДЛЯ ВЫБОРА ВРЕМЕНИ
@bot.message_handler(state=BookingStates.choose_time)
def process_time_fallback(message):
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
            bot.send_message(chat_id, "Выберите услугу мастера (или введите промокод):", reply_markup=get_services_by_master_kb(master_id))
        elif scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            service_id = user_data[chat_id]['service_id']
            bot.send_message(chat_id, "Выберите мастера (или введите промокод):", reply_markup=get_masters_by_service_kb(service_id))
        return

    if not user_data.get(chat_id, {}).get('date_chosen'):
        show_calendar(chat_id)
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
        slots_kb, free_slots = get_time_slots_kb(master_id, date_str)

        if not free_slots:
            bot.send_message(chat_id, "На эту дату больше нет свободного времени. Попробуйте другую дату.")
            del user_data[chat_id]['date_chosen']
            show_calendar(chat_id)
            return
        bot.send_message(chat_id, "Свободные слоты:", reply_markup=slots_kb)
        return

    user_data[chat_id]['time'] = text
    bot.set_state(chat_id, BookingStates.enter_phone, chat_id)
    bot.send_message(chat_id, "Укажите ваш номер телефона для подтверждения записи (в формате +7XXXXXXXXXX):")


# ВВОД ТЕЛЕФОНА
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
        show_calendar(chat_id)
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
            bot.send_message(chat_id, "Выберите услугу, которую оказывает мастер (или введите промокод):", reply_markup=get_services_by_master_kb(master_id))
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
            "INSERT INTO clients (id, phone, agreed) VALUES (%s, %s, FALSE)",
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
    original_price = user_data[chat_id]['original_price']
    final_price = user_data[chat_id]['final_price']

    if 'promo_code' in user_data[chat_id]:
        summary = (
            f"Проверьте данные:\n"
            f"Салон: {salon}\n"
            f"Услуга: {service}\n"
            f"Мастер: {master}\n"
            f"Дата: {user_data[chat_id]['date']}\n"
            f"Время: {user_data[chat_id]['time']}\n"
            f"Телефон: {text}\n"
            f"Цена: {original_price}₽ → {final_price}₽ (промокод: {user_data[chat_id]['promo_code']})"
        )
    else:
        summary = (
            f"Проверьте данные:\n"
            f"Салон: {salon}\n"
            f"Услуга: {service}\n"
            f"Мастер: {master}\n"
            f"Дата: {user_data[chat_id]['date']}\n"
            f"Время: {user_data[chat_id]['time']}\n"
            f"Телефон: {text}\n"
            f"Цена: {final_price}₽"
        )
    bot.send_message(chat_id, summary, reply_markup=get_confirm_kb())


# ПОДТВЕРЖДЕНИЕ ЗАПИСИ + ПРЕДЛОЖЕНИЕ ОПЛАТЫ
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
        user_data[chat_id]['original_price'] = 0
        user_data[chat_id]['final_price'] = 0

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
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_all_services_kb(with_promo=True))
        return

    if text == 'Подтвердить запись':
        data = user_data[chat_id]
        promo_code = data.get('promo_code', None)
        execute_query(
            """INSERT INTO appointments
               (client_id, master_id, service_id, appointments_date, appointments_time, status, promo_code)
               VALUES (%s, %s, %s, %s, %s, 'confirmed', %s)""",
            (data['client_id'], data['master_id'], data['service_id'], data['date'], data['time'], promo_code)
        )
        bot.send_message(chat_id, "✅ Запись успешно создана! Желаете оплатить онлайн сейчас?", reply_markup=get_payment_choice_kb())
        bot.set_state(chat_id, BookingStates.payment, chat_id)
        return
    bot.send_message(chat_id, "Пожалуйста, используйте кнопки подтверждения.")


# ОБРАБОТЧИК ОПЛАТЫ
@bot.message_handler(state=BookingStates.payment)
def handle_payment(message):
    chat_id = message.chat.id
    text = message.text

    if text == '💳 Оплатить онлайн':
        bot.send_message(
            chat_id,
            "💳 Открыта форма оплаты через банк (демо-режим).\n\n"
            "Введите данные карты:\n"
            "• Номер карты: 1234 5678 9012 3456\n"
            "• Срок: 12/26\n"
            "• CVV: 123\n\n"
            "Нажмите '💳 Оплатить', чтобы завершить демо-оплату.",
            reply_markup=get_payment_form_kb()
        )
    elif text == '⏰ Позже':
        bot.send_message(chat_id, "Хорошо! Вы сможете оплатить позже в личном кабинете.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)

        if chat_id in user_data:
            del user_data[chat_id]
    elif text == '💳 Оплатить':
        bot.send_message(chat_id, "✅ Оплата прошла успешно! Спасибо за заказ.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)

        if chat_id in user_data:
            del user_data[chat_id]
    elif text == 'Отмена':
        bot.send_message(chat_id, "Оплата отменена. Запись сохранена.", reply_markup=main_menu())
        bot.set_state(chat_id, None, chat_id)

        if chat_id in user_data:
            del user_data[chat_id]
    else:
        bot.send_message(chat_id, "Пожалуйста, используйте кнопки.", reply_markup=get_payment_choice_kb())
