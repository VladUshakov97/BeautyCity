import telebot
from dotenv import load_dorenv
import os


load_dorenv()

telegram_token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(telegram_token)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Здесь вы можете записаться на прием в наш салон красоты')


@bot.message_handler(func=lambda message: message== 'Записаться на прием')
def signup_for_salon(message):


