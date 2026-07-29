import telebot
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup


def get_main_menu():
    main_menu = ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = [
        'Записаться в салон'
        'Записаться к мастеру'
        'Записаться на процедуру'
        'Записаться по телефону'
    ]
    main_menu.add(*buttons)
    return main_menu


def signup_for_salon():
    signup = ReplyKeyboardMarkup(resize_keyboard=True)

    button = [
        'Мастер1'
        'Мастер2'
        'Мастер3'
        'Мастер4'
        'Мастер5'
    ]

    signup.add(*button)
    return signup


def choose_master():
    masters = ReplyKeyboardMarkup(resize_keyboard=True)

    button = [
        'Иван Васильевич'
        'Никита Кологривый'
        'Джейсон Стетхэм'
        'Алина Владимировна'
        'Стас Простофильский'
    ]

    masters.add(*button)
    return masters

def choose_procedure():
    procedure = ReplyKeyboardMarkup(resize_keyboard=True)

    button = [
        'Наращивание ресниц 2000'
        'Ламинирование бровей 1200'
        'Стрижка профессиональная 2500'
        'Стрижка бровей 500'
        'Покраска волос 650'
    ]

    procedure.add(*button)
    return procedure


def choose_address():
    address = ReplyKeyboardMarkup(resize_keyboard=True)

    button = [
        'Улица Ленина 22'
        'Улица Спортсменских 14'
        'Строителей 56А'
    ]

    procedure.add(*button)
    return address


def choose_time_procedure():
    time_procedure = ReplyKeyboardMarkup(resize_keyboard=True)

    button = [
        '10 00'
        '11 00'
        '12 00'
        '13 00'
        '14 00'
        '15 00'
        '16 00'
        '17 00'
        '18 00'
        '19 00'
        '20 00'
    ]
    time_procedure.add(*button)
    return time_procedure
