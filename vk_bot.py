import vk_api

from vk_api.longpoll import VkLongPoll, VkEventType
from environs import Env
from vk_api.utils import get_random_id

from vk_keybords import get_vk_keyboard


def main():
    env = Env()
    env.read_env()
    vk_token = env.str("VK_BOT_TOKEN")

    vk_session = vk_api.VkApi(token=vk_token)
    longpoll = VkLongPoll(vk_session)

    print("Бот для ВКонтакте запущен. Ожидание сообщений...")

    main_keyboard = get_vk_keyboard()

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_text = event.text
            vk_session.method('messages.send', {
                'user_id': event.user_id,
                'message': user_text,
                'keyboard':main_keyboard.get_keyboard(),
                'random_id': get_random_id()
            })

if __name__ == '__main__':
    main()