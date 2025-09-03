from telegram import KeyboardButton, ReplyKeyboardMarkup
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_vk_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)

    keyboard.add_line()
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)

    return keyboard


def get_main_keyboard():
    keyboard = [
        [KeyboardButton('Новый вопрос')],
        [KeyboardButton('Сдаться'), KeyboardButton('Мой счет')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True,  one_time_keyboard=False)
