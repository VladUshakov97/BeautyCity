import telebot
from telebot import custom_filters
from handlers import bot
from states import BookingStates

def main():
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    print("Бот запущен...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()