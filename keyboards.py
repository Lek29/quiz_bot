from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    keyboard = [
        [KeyboardButton('Новый вопрос')],
        [KeyboardButton('Сдаться'), KeyboardButton('Мой счет')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True,  one_time_keyboard=False)