import glob
import random

import redis
import vk_api
from environs import Env
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from keyboards import get_vk_keyboard
from utils import get_redis_connection, load_quiz_questions


def send_message(session, user_id, message, keyboard):
    session.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard.get_keyboard(),
        'random_id': get_random_id()
    })


def handle_new_question(session, user_id, redis_conn, quiz_questions, main_keyboard):
    random_question = random.choice(quiz_questions)
    question = random_question['question']
    answer = random_question['answer']
    redis_conn.set(user_id, answer)
    send_message(session, user_id, question, main_keyboard)


def handle_surrender(session, user_id, redis_conn, correct_answer, quiz_questions, main_keyboard):
    if correct_answer:
        send_message(session, user_id, f'Правильный ответ: {correct_answer}', main_keyboard)
        redis_conn.delete(user_id)
        handle_new_question(session, user_id, redis_conn, quiz_questions, main_keyboard)
    else:
        send_message(session, user_id, 'Вы ещё не получили вопрос. Нажмите «Новый вопрос», чтобы начать игру.', main_keyboard)


def handle_solution_attempt(session, user_id, redis_conn, user_text, correct_answer, main_keyboard):
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

    if user_text.lower().strip() == clean_answer.lower().strip():
        send_message(session, user_id, 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».', main_keyboard)
        redis_conn.delete(user_id)
    else:
        send_message(session, user_id, 'Неправильно… Попробуешь ещё раз?', main_keyboard)


def main():
    env = Env()
    env.read_env()
    vk_token = env.str('VK_BOT_TOKEN')

    redis_host = env.str('REDIS_HOST', 'localhost')
    redis_port = env.int('REDIS_PORT', 6379)
    redis_password = env.str('REDIS_PASSWORD', '')

    vk_session = vk_api.VkApi(token=vk_token)
    longpoll = VkLongPoll(vk_session)

    try:
        redis_conn = get_redis_connection(redis_host, redis_port, redis_password)
        if not redis_conn:
            print('Не удалось подключиться к Redis. Выход.')
            return
    except redis.exceptions.ConnectionError as e:
        print(f'Ошибка подключения к Redis: {e}')
        return

    folder_path = 'extracted_files'

    try:
        file_paths = glob.glob(f'{folder_path}/*.txt')
        quiz_questions = []
        for file_path in file_paths:
            quiz_questions.extend(load_quiz_questions(file_path))

        if not quiz_questions:
            print('Ошибка: В файлах викторины не найдено ни одного вопроса.')
            return
    except FileNotFoundError:
        print(f'Ошибка: Не удалось найти файлы викторины в папке {folder_path}.')
        return
    except Exception as e:
        print(f'Произошла ошибка при загрузке вопросов: {e}')
        return

    print('Бот для ВКонтакте запущен. Ожидание сообщений...')

    main_keyboard = get_vk_keyboard()

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_text = event.text
            user_id = event.user_id
            correct_answer = redis_conn.get(user_id)

            if user_text == 'Новый вопрос':
                handle_new_question(vk_session, user_id, redis_conn, quiz_questions, main_keyboard)
            elif user_text == 'Сдаться':
                handle_surrender(vk_session, user_id, redis_conn, correct_answer, quiz_questions, main_keyboard)
            elif correct_answer:
                handle_solution_attempt(vk_session, user_id, redis_conn, user_text, correct_answer, main_keyboard)
            else:
                send_message(vk_session, user_id, 'Привет! Нажми «Новый вопрос», чтобы начать викторину.',
                             main_keyboard)


if __name__ == '__main__':
    main()
