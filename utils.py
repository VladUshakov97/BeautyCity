from keyboards import (main_menu, get_salons_kb, get_all_masters_kb,
                       get_all_services_kb, get_services_kb,
                       get_services_by_master_kb, get_masters_kb,
                       get_masters_by_service_kb, get_back_cancel_kb)
from states import BookingStates
from config import PROMO_CODES
from handlers import show_calendar


user_data = {}


def cancel_booking(chat_id, bot):
    """Отменяет текущую запись, очищает данные и возвращает главное меню."""
    bot.send_message(chat_id, "Запись отменена.", reply_markup=main_menu())
    bot.set_state(chat_id, None, chat_id)
    user_data.pop(chat_id, None)


def go_back(chat_id, current_state, bot):
    """
    Возвращает пользователя на предыдущий шаг в зависимости от текущего состояния и сценария.
    """
    scenario = user_data.get(chat_id, {}).get('scenario', 'salon_first')
    data = user_data.get(chat_id, {})

    if current_state == BookingStates.choose_salon:
        bot.set_state(chat_id, None, chat_id)
        bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
    elif current_state == BookingStates.choose_service:
        if scenario == 'salon_first':
            bot.set_state(chat_id, BookingStates.choose_salon, chat_id)
            bot.send_message(chat_id, "Выберите салон:", reply_markup=get_salons_kb())
        elif scenario == 'master_first':
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=get_all_masters_kb())
        else:
            bot.set_state(chat_id, None, chat_id)
            bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
    elif current_state == BookingStates.choose_master:
        if scenario == 'salon_first':
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            salon_id = data.get('salon_id')
            kb = get_services_kb(salon_id, with_promo=True)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=kb)
        elif scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите услугу:", reply_markup=get_all_services_kb(with_promo=True))
        else:
            bot.set_state(chat_id, None, chat_id)
            bot.send_message(chat_id, "Выберите действие:", reply_markup=main_menu())
    elif current_state == BookingStates.choose_time:
        if scenario == 'salon_first' or scenario == 'service_first':
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            service_id = data.get('service_id')
            if scenario == 'salon_first':
                salon_id = data.get('salon_id')
                kb = get_masters_kb(service_id, salon_id)
            else:
                kb = get_masters_by_service_kb(service_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=kb)
        else:
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            master_id = data.get('master_id')
            kb = get_services_by_master_kb(master_id)
            bot.send_message(chat_id, "Выберите услугу мастера:", reply_markup=kb)
    elif current_state == BookingStates.enter_phone:
        bot.set_state(chat_id, BookingStates.choose_time, chat_id)
        show_calendar(chat_id)
    elif current_state == BookingStates.confirm:
        bot.set_state(chat_id, BookingStates.enter_phone, chat_id)
        bot.send_message(
            chat_id,
            "Измените номер телефона (или нажмите 'Назад' для возврата к выбору данных):",
            reply_markup=get_back_cancel_kb()
        )
    else:
        bot.set_state(chat_id, None, chat_id)
        bot.send_message(chat_id, "Начните заново.", reply_markup=main_menu())


def ensure_data(chat_id, required_keys, bot):
    data = user_data.get(chat_id, {})
    missing = [k for k in required_keys if k not in data]

    if missing:
        bot.send_message(chat_id, f"Не хватает данных: {', '.join(missing)}. Начните запись заново.",
                         reply_markup=main_menu())
        user_data.pop(chat_id, None)
        bot.set_state(chat_id, None, chat_id)
        return False
    return True


def apply_promo_code(chat_id, code):
    """
    Применяет промокод к текущей услуге, обновляет final_price в user_data.
    """
    data = user_data.get(chat_id, {})
    original = data.get('original_price', 0)

    if original == 0:
        user_data[chat_id]['pending_promo'] = code
        return None, 0

    if code in PROMO_CODES:
        discount = PROMO_CODES[code]
        new_price = original - (original * discount // 100)
        user_data[chat_id]['final_price'] = new_price
        user_data[chat_id]['promo_code'] = code
        return new_price, discount
    return None, 0


def navigate_to_next_step(chat_id, bot):
    """
    Определяет, куда перейти после выбора услуги/мастера в зависимости от сценария.
    Вызывается после того, как установлены необходимые ключи.
    """
    data = user_data.get(chat_id, {})
    scenario = data.get('scenario', 'salon_first')

    if scenario == 'salon_first':
        service_id = data.get('service_id')
        salon_id = data.get('salon_id')
        kb = get_masters_kb(service_id, salon_id)

        if kb.keyboard:
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера:", reply_markup=kb)
        else:
            bot.send_message(chat_id, "К сожалению, в этом салоне нет мастеров для данной услуги. Попробуйте другую услугу.")
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            kb_services = get_services_kb(salon_id, with_promo=True)
            bot.send_message(chat_id, "Выберите другую услугу:", reply_markup=kb_services)
    elif scenario == 'master_first':
        bot.set_state(chat_id, BookingStates.choose_time, chat_id)
        show_calendar(chat_id)
    else:
        service_id = data.get('service_id')
        kb = get_masters_by_service_kb(service_id)

        if kb.keyboard:
            bot.set_state(chat_id, BookingStates.choose_master, chat_id)
            bot.send_message(chat_id, "Выберите мастера, который оказывает эту услугу:", reply_markup=kb)
        else:
            bot.send_message(chat_id, "К сожалению, нет мастеров для данной услуги. Попробуйте другую.")
            bot.set_state(chat_id, BookingStates.choose_service, chat_id)
            bot.send_message(chat_id, "Выберите другую услугу:", reply_markup=get_all_services_kb(with_promo=True))
