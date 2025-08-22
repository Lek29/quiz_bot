import os
import random
from pprint import pprint


def load_quiz_data_as_list(file_path):
    """
    Загружает вопросы и ответы из файла и возвращает их в виде списка словарей.
    Каждый словарь содержит ключи "question" и "answer".
    """
    quiz_list = []

    try:
        with open(file_path, 'r', encoding='koi8-r') as file:
            content = file.read()


            blocks = content.split('\n\nВопрос ')


            for block in blocks[1:]:
                full_block = 'Вопрос ' + block

                answer_label_pos = full_block.find('\nОтвет:')

                if answer_label_pos == -1:
                    continue


                question_start_pos = full_block.find(':') + 1
                question_text = full_block[question_start_pos:answer_label_pos].strip()


                answer_block_start = answer_label_pos + len('\nОтвет:')
                answer_text_block = full_block[answer_block_start:].strip()
                answer = answer_text_block.split('\n')[0].strip()


                if question_text and answer:
                    quiz_item = {
                        "question": question_text,
                        "answer": answer
                    }
                    quiz_list.append(quiz_item)

    except FileNotFoundError:
        print(f"Ошибка: файл {file_path} не найден.")
    except Exception as e:
        print(f"Произошла ошибка при чтении файла: {e}")

    return quiz_list


def load_random_quiz_data(folder_path):
    quiz_files = os.listdir(folder_path)

    txt_files = [file for file in quiz_files if file.endswith('.txt')]

    if not txt_files:
        print(f"Ошибка: в папке '{folder_path}' не найдено .txt файлов.")
        return []

    random_file = random.choice(txt_files)

    file_path = os.path.join(folder_path, random_file)

    return load_quiz_data_as_list(file_path)