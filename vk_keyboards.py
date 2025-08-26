import redis
from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_main_keyboard():
    keyboard = [
        [KeyboardButton('Новый вопрос')],
        [KeyboardButton('Сдаться'), KeyboardButton('Мой счет')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True,  one_time_keyboard=False)


def get_redis_connection():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except redis.exceptions.ConnectionError as e:
        print(f"Ошибка подключения к Redis: {e}")
        return None