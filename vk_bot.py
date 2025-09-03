import random
import glob

import redis
import vk_api
from environs import Env
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from utils import get_redis_connection,  load_quiz_questions
from keyboards import get_vk_keyboard


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
        file_paths = glob.glob(f"{folder_path}/*.txt")
        quiz_questions = []
        for file_path in file_paths:
            quiz_questions.extend(load_quiz_questions(file_path))

        if not quiz_questions:
            print("Ошибка: В файлах викторины не найдено ни одного вопроса.")
            return
    except FileNotFoundError:
        print(f"Ошибка: Не удалось найти файлы викторины в папке {folder_path}.")
        return
    except Exception as e:
        print(f"Произошла ошибка при загрузке вопросов: {e}")
        return

    print('Бот для ВКонтакте запущен. Ожидание сообщений...')

    main_keyboard = get_vk_keyboard()

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_text = event.text
            user_id = event.user_id

            correct_answer = redis_conn.get(user_id)

            if user_text == 'Новый вопрос':
                random_question = random.choice(quiz_questions)
                question = random_question['question']
                answer = random_question['answer']

                redis_conn.set(user_id, answer)

                vk_session.method('messages.send', {
                    'user_id': event.user_id,
                    'message': question,
                    'keyboard': main_keyboard.get_keyboard(),
                    'random_id': get_random_id()
                })
            elif user_text == 'Сдаться':
                if correct_answer:
                    vk_session.method(
                        'messages.send', {
                            'user_id': user_id,
                            'message': f'Правильный ответ: {correct_answer}',
                            'keyboard': main_keyboard.get_keyboard(),
                            'random_id': get_random_id()
                        })
                    redis_conn.delete(user_id)

                    random_question = random.choice(quiz_questions)
                    question = random_question['question']
                    answer = random_question['answer']

                    redis_conn.set(user_id, answer)
                    vk_session.method(
                        'messages.send', {
                            'user_id': user_id,
                            'message': question,
                            'keyboard': main_keyboard.get_keyboard(),
                            'random_id': get_random_id()
                        })
                else:
                    vk_session.method(
                        'messages.send', {
                            'user_id': user_id,
                            'message': 'Вы ещё не получили вопрос. Нажмите «Новый вопрос», чтобы начать игру.',
                            'keyboard': main_keyboard.get_keyboard(),
                            'random_id': get_random_id()
                        })
            elif correct_answer:
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
                    vk_session.method(
                        'messages.send', {
                            'user_id': user_id,
                            'message': 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
                            'keyboard': main_keyboard.get_keyboard(),
                            'random_id': get_random_id()
                        })
                    redis_conn.delete(user_id)
                else:
                    vk_session.method(
                        'messages.send', {
                            'user_id': user_id,
                            'message': 'Неправильно… Попробуешь ещё раз?',
                            'keyboard': main_keyboard.get_keyboard(),
                            'random_id': get_random_id()
                        })
            else:
                vk_session.method(
                    'messages.send', {
                        'user_id': user_id,
                        'message': 'Привет! Нажми «Новый вопрос», чтобы начать викторину.',
                        'keyboard': main_keyboard.get_keyboard(),
                        'random_id': get_random_id()
                    })


if __name__ == '__main__':
    main()
