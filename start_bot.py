
import random
from pprint import pprint

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, Updater, Filters, CallbackContext
from environs import Env

from keyboards import get_main_keyboard

from utils import load_quiz_data_as_list, load_random_quiz_data


env = Env()
env.read_env()

TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')


def start(update: Update, context: CallbackContext):
    keyboard = get_main_keyboard()
    update.message.reply_text(
        'Здравствуйте! Я бот-викторина.',
        reply_markup=keyboard
    )

def handle_text_message(update: Update, context: CallbackContext):
    user_text = update.message.text

    if user_text == 'Новый вопрос':
        handle_new_question(update, context)
    else:
        update.message.reply_text(user_text)


def handle_new_question(update: Update, context: CallbackContext):
    quiz_items = context.bot_data.get('quiz_questions', [])

    if not quiz_items:
        update.message.reply_text('Извините, вопросы не загружены. Попробуйте позже.')
        return

    random_question = random.choice(quiz_items)
    update.message.reply_text(random_question['question'])


def main():
    """Запускает бота."""

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    file_name = 'extracted_files'
    dispatcher.bot_data['quiz_questions'] = load_random_quiz_data(file_name)


    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_text_message))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()