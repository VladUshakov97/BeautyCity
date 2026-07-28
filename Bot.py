from telebot import TeleBot
from dotenv import load_dorenv
import os


@bot.message_handler(commands=['start'])
def main():

    load_dorenv()

    telegram_token = os.environ['TELEGRAM_TOKEN']
    bot = telebot.TeleBot(telegram_token)





    bot.polling()

