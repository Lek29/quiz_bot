from telegram.ext import CommandHandler, MessageHandler, filters, Updater, Filters
from environs import Env

env = Env()
env.read_env()

TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')


def start(update, context):
    update.message.reply_text('Здраствуйте')


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    """Запускает бота."""

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()