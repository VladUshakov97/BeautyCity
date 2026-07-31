import telebot
from dotenv import load_dotenv
import os
from Keyboard import get_main_menu, choose_master, choose_address, choose_procedure, choose_time_procedure
import psycopg2
from database import *


load_dotenv()

telegram_token = os.environ['TG_TOKEN']
bot = telebot.TeleBot(telegram_token)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Здесь вы можете записаться на прием в наш салон красоты', reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == 'Записаться в салон')
def signup_for_salon(message):
    chat_id = message.chat.id
    conn, cursor = get_db_connection()
    bot.send_message(chat_id, 'Выберите салон для проведения процедуры', reply_markup=choose_address())
    execute_query('salons', message.text)
    bot.send_message(chat_id, 'Выберите процедуру', reply_markup=choose_procedure())
    execute_query('services', message.text)
    bot.send_message(chat_id, 'Выберите Мастера', reply_markup=choose_master())
    execute_query('masters', message.text)
    bot.send_message(chat_id, 'Выберите Время', reply_markup=choose_time_procedure())
    execute_query('appointments', message.text)


@bot.message_handler(func=lambda message: message.text == 'Записаться к Мастеру')
def signup_for_master(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message.text == 'Записаться на процедуру')
def singup_for_procedure(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message.text == 'Записаться по телефону')
def signup_for_phone(message):
    chat_id = message.chat.id


@bot.message_handler(func=lambda message: message == 'Оставить отзыв')
def write_feedback(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Напишите ваш отзыв: ')
    bot.register_next_step_handler(message, save_feedback)


def save_feedback(message):
    chat_id = message.chat.id
    conn, cursor = get_db_connection()
    query = 'INSERT INTO FEEDBACK(user_id, text) VALUES (%s, %s)'
    values = (chat_id, message.text)
    execute_query(query, values)






bot.polling()
