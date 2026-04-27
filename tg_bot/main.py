import hashlib

import telebot
from dotenv import load_dotenv
import os
from datetime import datetime

import requests
from tg_bot.controller import request_check_password, request_add_habit, get_habits, request_edit_name, \
    request_edit_time, request_get_count, request_delete_habit, request_up_count, get_habit_name
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.utils_bot import init_db, add_token_to_db, get_token_jwt

current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, '.env')

load_dotenv(dotenv_path=dotenv_path)
TOKEN_TG = os.environ.get("TOKEN_TG")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
bot = telebot.TeleBot(TOKEN_TG, parse_mode=None, threaded=True, num_threads=10)


@bot.message_handler(commands=['start'])
def handle_start(message):
    msg = bot.send_message(message.chat.id, f"Приветствую, {message.chat.first_name}!")
    enter_password(message)


def enter_password(message):
    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(msg, process_password)


def process_password(message):
    password = hashlib.sha256(message.text.encode()).hexdigest().encode() # сразу хэшируем пароль
    user_id = message.chat.id
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as exception:
        print(f"Не удалось удалить сообщение: {exception}")
    try:
        username = message.chat.username
        if username is None:
            username = "No username"
        response = request_check_password(username=username,
                                          user_id=user_id,
                                          password=password)
        try:
            token = response.json()
            add_token_to_db(user_id=user_id, token=token)
        except AttributeError:
            bot.send_message(message.chat.id, "❌ Ошибка: неверный пароль. Попробуйте еще раз")
            enter_password(message)
        if response.status_code == 200:
            bot.send_message(message.chat.id, "✅ Авторизация успешна! Пароль удален из истории.")
            bot.send_message(message.chat.id, f"Время жизни вашего токена - "
                                              f"{ACCESS_TOKEN_EXPIRE_MINUTES} минут")
    except requests.exceptions.ConnectionError:
        bot.send_message(message.chat.id, "🔌 Ошибка связи с сервером.")


@bot.message_handler(commands=['add', ])
def add_habit_request(message):
    habit_data_add = dict()
    bot.reply_to(message, "Напишите, какую привычку вы хотите добавить")
    habit_data_add["id_telegram"] = message.chat.id
    bot.register_next_step_handler(message, add_habit_name_func, habit_data_add)


def add_habit_name_func(message, habit_data_add):
    name = message.text
    bot.send_message(message.chat.id, f"Добавляю {name} в список ваших привычек!")
    habit_data_add["name"] = name
    bot.reply_to(message, "Напишите время напоминания в формате XX:XX")
    bot.register_next_step_handler(message, add_habit_time_func, habit_data_add)


def add_habit_time_func(message, habit_dict):
    time_str = message.text  # Получаем текст сообщения
    time_obj = None
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        habit_dict["time"] = time_str
        required_fields = ["id_telegram", "name", "time"]
        if all(field in habit_dict for field in required_fields):
            token = get_token_jwt(user_id=message.chat.id)
            result = request_add_habit(habit_dict, token)
            if result.status_code == 401 or result.status_code == 403:
                bot.send_message(message.chat.id,
                                 "Ваш токен либо устарел, либо не создан. "
                                 "Введите пароль заново")
                enter_password(message)
            try:
                bot.reply_to(message, f"Время напоминания установлено на {time_obj.time()}")
            except AttributeError:
                print("Ошибка сбора данных, неверный формат введенного времени")
        else:
            bot.reply_to(message, "Произошла ошибка при сборе данных. Попробуйте еще раз /add")
            print("Произошла ошибка при сборе данных")
    except ValueError:
        bot.reply_to(message, "Не верный формат ввода. Напишите, время напоминания в формате XX:XX")
        bot.register_next_step_handler(message, add_habit_time_func, habit_dict)


@bot.message_handler(commands=['edit', ])
def add_habit_edit(message):
    token = get_token_jwt(user_id=message.chat.id)
    bot.reply_to(message, "Выберите привычку, которую хотите изменить")
    habit_response = get_habits(user_id=message.chat.id, token=token)
    if habit_response.status_code == 401 or habit_response.status_code == 403:
        bot.send_message(message.chat.id,
                         "Ваш токен либо устарел, либо не создан. "
                         "Введите пароль заново")
        enter_password(message)
    hab_json = habit_response.json()
    for habit_data in hab_json:
        keyboard = InlineKeyboardMarkup()
        # 2. Создаем кнопки (text - что видит юзер, callback_data - что получает бот)
        button1 = InlineKeyboardButton(text='Изменить название', callback_data=f"edit_name;{habit_data['id']}")
        button2 = InlineKeyboardButton(text='Изменить время', callback_data=f"edit_time;{habit_data['id']}")
        button3 = InlineKeyboardButton(text='Удалить привычку', callback_data=f"delete_habit;{habit_data['id']}")
        button4 = InlineKeyboardButton(text='Посмотреть счетчик', callback_data=f"view_count;{habit_data['id']}")
        # 3. Добавляем кнопки в клавиатуру
        keyboard.add(button1, button2, button3, button4)
        # 4. Отправляем сообщение с клавиатурой
        bot.send_message(message.chat.id,
                         f"Название: {habit_data['name']}, время: {habit_data['time']}",
                         reply_markup=keyboard)


def set_new_name_message(message, data):
    msg = bot.send_message(message, "Введите новое название привычки")
    bot.register_next_step_handler(msg, set_new_name_func, data=data)


def set_new_name_func(message, data):
    data['name'] = message.text
    token = get_token_jwt(user_id=message.chat.id)
    result = request_edit_name(data=data, token=token)
    if result.status_code == 401 or result.status_code == 403:
        bot.send_message(message.chat.id,
                         "Ваш токен либо устарел, либо не создан. "
                         "Введите пароль заново")
        enter_password(message)
    bot.send_message(message.chat.id, f"Название изменено на {message.text}")


def set_new_time_message(message, data):
    msg = bot.send_message(message, "Введите новое время напоминания, в формате ХХ:ХХ")
    bot.register_next_step_handler(msg, set_new_time_func, data=data)


def set_new_time_func(message, data):
    try:
        datetime.strptime(message.text, "%H:%M")
        data['time'] = message.text
        token = get_token_jwt(user_id=message.chat.id)
        result = request_edit_time(data=data, token=token)
        if result.status_code == 401 or result.status_code == 403:
            bot.send_message(message.chat.id,
                             "Ваш токен либо устарел, либо не создан. "
                             "Введите пароль заново")
            enter_password(message)
        bot.send_message(message.chat.id, f"Время напоминания изменено на {message.text}")
    except ValueError:
        bot.reply_to(message, "Не верный формат ввода. Напишите, время напоминания в формате XX:XX")
        set_new_time_message(message.chat.id, data=data)


def delete_habit_message(message, data):
    bot.send_message(message, f"Ваша привычка {data['name']} была удалена")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data.split(';')
    habit_info_data = dict()
    habit_info_data['id_telegram'] = call.message.chat.id
    habit_id = data[1]
    token = get_token_jwt(user_id=call.message.chat.id)

    if data[0] == 'edit_name':
        update_data = dict()
        update_data['id'] = habit_id
        bot.answer_callback_query(call.id, text="Изменим название привычки")
        set_new_name_message(call.message.chat.id, data=update_data)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)

    elif data[0] == 'edit_time':
        bot.answer_callback_query(call.id, text="Изменим время напоминания")
        update_data = dict()
        update_data['id'] = habit_id
        set_new_time_message(call.message.chat.id, data=update_data)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)

    elif data[0] == 'delete_habit':
        habit_name = get_habit_name(id_habit=habit_id, token=token)
        habit_info_data['name'] = habit_name.text
        data_delete = dict()
        data_delete['id_habit'] = habit_id
        result = request_delete_habit(data_delete=data_delete, token=token)
        if result.status_code == 401 or result.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            enter_password(call.message)
        delete_habit_message(call.message.chat.id, data=habit_info_data)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)

    elif data[0] == "view_count":
        habit_name = get_habit_name(id_habit=habit_id, token=token)
        count_result = request_get_count(habit_id=habit_id, token=token)
        if count_result.status_code == 401 or count_result.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан. "
                             "Введите пароль заново")
            enter_password(call.message)
        bot.send_message(call.message.chat.id,
                         f"Количество выполнений '{habit_name.text}': {count_result.json()}")

    elif data[0] == 'completed':
        id_habit = data[1]
        response_up_count = request_up_count(id_habit=id_habit, token=token)
        bot.send_message(call.message.chat.id, "Выполнение привычки засчитано.")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        if response_up_count.status_code == 226:
            response_json = response_up_count.json()
            habit_name = response_json['habit_name']

            bot.send_message(call.message.chat.id,
                             f"Вы успешно привили '{habit_name}', привычка будет удалена из списка.")
    elif data[0] == 'not_completed':
        bot.send_message(call.message.chat.id, "Выполнение привычки не засчитано.")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)


def send_message_reminder(user_id, name, habit_id):
    keyboard = InlineKeyboardMarkup()
    # 2. Создаем кнопки (text - что видит юзер, callback_data - что получает бот)
    button1 = InlineKeyboardButton(text='Выполнено', callback_data=f'completed;{habit_id}')
    button2 = InlineKeyboardButton(text='Не выполнено', callback_data=f'not_completed;')
    # 3. Добавляем кнопки в клавиатуру
    keyboard.add(button1, button2)
    # 4. Отправляем сообщение с клавиатурой
    bot.send_message(user_id, f"Напоминаю, что нужно выполнить '{name}'", reply_markup=keyboard)


if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
