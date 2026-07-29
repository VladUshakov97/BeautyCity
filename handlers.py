import telebot
from dotenv import load_dotenv
import os
import Keyboard


load_dorenv()

telegram_token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(telegram_token)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Здесь вы можете записаться на прием в наш салон красоты', reply_markup=Keyboard.get_main_menu)


@bot.message_handler(func=lambda message: message.text == 'Записаться на прием')
def signup_for_salon(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Выберите салон для проведения процедуры', reply_markup=Keyboard.choose_address)
    bot.send_message(chat.id, 'Выберите процедуру', reply_markup=Keyboard.choose_procedure)
    bot.send_message(chat.id, 'Выберите Мастера', reply_markup=Keyboard.choose_procedure)
    bot.send_message(chat.id, 'Выберите Время', reply_markup=Keyboard.choose_procedure)


@bot.message_handler(func=lambda message: message.text == 'Записаться к Мастеру')
def signup_for_master(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message.text == 'Записаться на процедуру')
def singup_for_procedure(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message.text == 'Записаться по телефону')
def signuo_for_phone(message):
    chat_id = message.chat.id
