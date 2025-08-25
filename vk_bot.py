import random

import redis
import vk_api


from vk_api.longpoll import VkLongPoll, VkEventType
from environs import Env
from vk_api.utils import get_random_id

from vk_keybords import get_vk_keyboard
from utils import load_random_quiz_data, get_redis_connection


def main():
    env = Env()
    env.read_env()
    vk_token = env.str("VK_BOT_TOKEN")

    redis_host = env.str('REDIS_HOST', 'localhost')
    redis_port = env.int('REDIS_PORT', 6379)
    redis_password = env.str('REDIS_PASSWORD', '')

    vk_session = vk_api.VkApi(token=vk_token)
    longpoll = VkLongPoll(vk_session)

    try:
        redis_conn = get_redis_connection(redis_host, redis_port, redis_password)
        if not redis_conn:
            print("Не удалось подключиться к Redis. Выход.")
            return
    except redis.exceptions.ConnectionError as e:
        print(f"Ошибка подключения к Redis: {e}")
        return

    quiz_questions = load_random_quiz_data('extracted_files')

    print("Бот для ВКонтакте запущен. Ожидание сообщений...")

    main_keyboard = get_vk_keyboard()

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_text = event.text
            user_id = event.user_id

            correct_answer = redis_conn.get(user_id)

            if user_text == "Новый вопрос":
                random_question = random.choice(quiz_questions)
                question = random_question['question']
                answer = random_question['answer']

                redis_conn.set(user_id, answer)

                vk_session.method('messages.send', {
                    'user_id': event.user_id,
                    'message': question,
                    'keyboard':main_keyboard.get_keyboard(),
                    'random_id': get_random_id()
                })
            elif user_text == "Сдаться":
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
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': question,
                        'keyboard': main_keyboard.get_keyboard(),
                        'random_id': get_random_id()
                    })
                else:
                    vk_session.method('messages.send', {
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
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
                        'keyboard': main_keyboard.get_keyboard(),
                        'random_id': get_random_id()
                    })
                    redis_conn.delete(user_id)
                else:
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': 'Неправильно… Попробуешь ещё раз?',
                        'keyboard': main_keyboard.get_keyboard(),
                        'random_id': get_random_id()
                    })
            else:
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': 'Привет! Нажми «Новый вопрос», чтобы начать викторину.',
                    'keyboard': main_keyboard.get_keyboard(),
                    'random_id': get_random_id()
                })


if __name__ == '__main__':
    main()