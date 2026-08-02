from telebot import custom_filters
from handlers import bot


def main():
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    print("Бот запущен...")
    bot.infinity_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
