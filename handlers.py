import telebot
from dotenv import load_dotenv
import os
from Keyboard import get_main_menu, choose_master, choose_address, choose_procedure, choose_time_procedure
import psycopg2
from database_func import connect_to_database
from logic import write_to_database


load_dotenv()

telegram_token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(telegram_token)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Здесь вы можете записаться на прием в наш салон красоты', reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == 'Записаться на прием')
def signup_for_salon(message):
    chat_id = message.chat.id
    conn, cursor = connect_to_database()
    bot.send_message(chat_id, 'Выберите салон для проведения процедуры', reply_markup=choose_address())
    write_to_database('salons', message.text)
    bot.send_message(chat_id, 'Выберите процедуру', reply_markup=choose_procedure())
    write_to_database('services', message.text)
    bot.send_message(chat_id, 'Выберите Мастера', reply_markup=choose_master())
    write_to_database('masters', message.text)
    bot.send_message(chat_id, 'Выберите Время', reply_markup=choose_time_procedure())
    write_to_database('appointments', message.text)


@bot.message_handler(func=lambda message: message.text == 'Записаться к Мастеру')
def signup_for_master(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message.text == 'Записаться на процедуру')
def singup_for_procedure(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message.text == 'Записаться по телефону')
def signuo_for_phone(message):
    chat_id = message.chat.id
