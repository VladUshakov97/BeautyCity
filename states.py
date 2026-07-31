from telebot.handler_backends import StatesGroup, State


class BookingStates(StatesGroup):
    choose_salon = State()      # выбор салона
    choose_service = State()    # выбор услуги
    choose_master = State()     # выбор мастера (после услуги)
    choose_time = State()       # выбор даты и времени
    enter_phone = State()       # ввод номера телефона
    confirm = State()           # подтверждение записи

    promo = State()             # ввод промокода
    accept_personal_data = State()  # согласие на обработку ПД (при первом запуске)
    feedback = State()          # отзыв после услуги

    show_phone = State()        # если выбрал "Записаться по телефону" то показать номер