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


def singup_for_procedure():

    procedure = ReplyKeyboardMarkup(resize_keyboard=True)

    button = [
        'Наращивание ресниц'
    ]




