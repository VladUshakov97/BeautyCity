import telebot
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup
import os

load_dotenv()

telegram_token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(telegram_token)


def get_main_menu():
    main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        'Записаться в салон',
        'Записаться к мастеру',
        'Записаться на процедуру',
        'Записаться по телефону'
    ]
    main_menu.add(*buttons)
    return main_menu


def signup_for_salon():
    signup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        'Мастер1',
        'Мастер2',
        'Мастер3',
        'Мастер4',
        'Мастер5'
    ]
    
    signup.add(*buttons)
    return signup


def choose_master():
    masters = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        'Иван Васильевич',
        'Никита Кологривый',
        'Джейсон Стетхэм',
        'Алина Владимировна',
        'Стас Простофильский'
    ]
    
    masters.add(*buttons)
    return masters


def choose_procedure():
    procedure = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        'Наращивание ресниц 2000',
        'Ламинирование бровей 1200',
        'Стрижка профессиональная 2500',
        'Стрижка бровей 500',
        'Покраска волос 650'
    ]
    
    procedure.add(*buttons)
    return procedure


def choose_address():
    address = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        'Улица Ленина 22',
        'Улица Спортсменских 14',
        'Строителей 56А'
    ]
    
    address.add(*buttons)
    return address


def choose_time_procedure():
    time_procedure = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        '10:00',
        '11:00',
        '12:00',
        '13:00',
        '14:00',
        '15:00',
        '16:00',
        '17:00',
        '18:00',
        '19:00',
        '20:00'
    ]
    time_procedure.add(*buttons)
    return time_procedure
