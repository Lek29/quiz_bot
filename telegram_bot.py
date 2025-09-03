import random
from enum import Enum, auto

import redis
from environs import Env
from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from keyboards import get_main_keyboard, get_vk_keyboard
from utils import load_random_questions

env = Env()
env.read_env()

TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')


class States(Enum):
    NEW_QUESTION = auto()
    SOLUTION_ATTEMPT = auto()


def start(update: Update, context: CallbackContext):
    keyboard = get_main_keyboard()
    update.message.reply_text(
        'Здравствуйте! Я бот-викторина. Нажмите "Новый вопрос", чтобы начать.',
        reply_markup=keyboard
    )
    return States.NEW_QUESTION


def handle_new_question(update: Update, context: CallbackContext):
    quiz_items = context.bot_data.get('quiz_questions', [])

    if not quiz_items:
        update.message.reply_text('Извините, вопросы не загружены. Попробуйте позже.')
        return ConversationHandler.END

    random_question = random.choice(quiz_items)
    question = random_question['question']
    answer = random_question['answer']

    r = context.bot_data.get('redis_conn')

    chat_id = update.effective_chat.id
    r.set(chat_id, answer)

    update.message.reply_text(question)
    return States.SOLUTION_ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext):
    user_text = update.message.text

    chat_id = update.effective_chat.id
    r = context.bot_data.get('redis_conn')

    correct_answer = r.get(chat_id)

    if correct_answer:
        dot_pos = correct_answer.find('.')
        bracket_pos = correct_answer.find('(')

        if dot_pos != -1 and bracket_pos != -1:
            end_pos = min(dot_pos, bracket_pos)
        elif dot_pos != -1:
            end_pos = dot_pos
        elif bracket_pos != -1:
            end_pos = bracket_pos
        else:
            end_pos = len(correct_answer)

        clean_answer = correct_answer[:end_pos]

        normalized_user_text = user_text.lower().strip()
        normalized_clean_answer = clean_answer.lower().strip()

        if normalized_user_text == normalized_clean_answer:
            update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
            r.delete(chat_id)
            return States.NEW_QUESTION
        else:
            update.message.reply_text('Неправильно… Попробуешь ещё раз?')

    return States.SOLUTION_ATTEMPT


def handle_surrender(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    r = context.bot_data.get('redis_conn')

    correct_answer = r.get(chat_id)

    if correct_answer:
        update.message.reply_text(f'Правильный ответ: {correct_answer}')
        r.delete(chat_id)

        return handle_new_question(update, context)
    else:
        update.message.reply_text('Вы ещё не получили вопрос. Нажмите «Новый вопрос», чтобы начать игру.')
        return States.NEW_QUESTION


def stop(update, context):
    """Завершает диалог и сбрасывает состояние."""
    update.message.reply_text('Спасибо за игру! До свидания.')
    return ConversationHandler.END


def main():
    """Запускает бота."""
    env = Env()
    env.read_env()
    TELEGRAM_BOT_TOKEN = env.str('TELEGRAM_BOT_TOKEN')

    redis_host = env.str('REDIS_HOST', 'localhost')
    redis_port = env.int('REDIS_PORT', 6379)
    redis_password = env.str('REDIS_PASSWORD', '')

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    try:
        redis_conn = redis.Redis(
                                 host=redis_host,
                                 port=redis_port,
                                 password=redis_password,
                                 db=0,
                                 decode_responses=True)
        dispatcher.bot_data['redis_conn'] = redis_conn
        print('Соединение с Redis успешно установлено!')
    except redis.exceptions.ConnectionError as e:
        print(f'Ошибка подключения к Redis: {e}')
        return

    folder_path = 'extracted_files'

    try:
        quiz_questions = load_random_questions(folder_path)
        if not quiz_questions:
            print("Ошибка: В файлах викторины не найдено ни одного вопроса.")
            return
        dispatcher.bot_data['quiz_questions'] = quiz_questions
    except FileNotFoundError as e:
        print(f'Ошибка: {e}')
        return
    except Exception as e:
        print(f'Произошла непредвиденная ошибка при загрузке вопросов: {e}')
        return

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.NEW_QUESTION: [MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question)],
            States.SOLUTION_ATTEMPT: [
                MessageHandler(Filters.regex('^Сдаться$'), handle_surrender),
                MessageHandler(Filters.text & ~Filters.regex('^Новый вопрос$'), handle_solution_attempt),

            ],

        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
