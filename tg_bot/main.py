import hashlib

import telebot
from dotenv import load_dotenv
import os
from datetime import datetime

import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, '.env')

load_dotenv(dotenv_path=dotenv_path)
TOKEN_TG = os.environ.get("TOKEN_TG")

bot = telebot.TeleBot(TOKEN_TG, parse_mode=None, threaded=True, num_threads=10)


class TokenManager:
    def __init__(self):
        self._tokens = {}  # {user_id: token_string}

    def set_token(self, user_id: int, token: str):
        self._tokens[user_id] = token

    def get_token(self, user_id: int):
        return self._tokens.get(user_id)


token_store = TokenManager()


@bot.message_handler(commands=['start'])
def handle_start(message):
    msg = bot.send_message(message.chat.id, f"Приветствую, {message.chat.first_name}!")
    enter_password(message)


def enter_password(message):
    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(msg, process_password)


def process_password(message):
    password = hashlib.sha256(message.text.encode()).hexdigest().encode()
    user_id = message.chat.id
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as exception:
        print(f"Не удалось удалить сообщение: {exception}")
    try:
        # Отправляем данные на FastAPI
        username = message.chat.username
        if username is None:
            username = "No username"
        response = requests.post(url="http://api:8000/check_user", json={
            'username': username,
            'id_telegram': int(user_id),
            'password': str(password)
        })
        token = response.json()
        token_store.set_token(user_id=user_id, token=token)
        if response.status_code == 200:
            bot.send_message(message.chat.id, "✅ Авторизация успешна! Пароль удален из истории.")
            bot.send_message(message.chat.id, "Время жизни вашего токена - 5 минут")
        else:
            bot.send_message(message.chat.id, "❌ Ошибка: неверный логин или пароль. Попробуйте еще раз")
            enter_password(message)
    except requests.exceptions.ConnectionError:
        bot.send_message(message.chat.id, "🔌 Ошибка связи с сервером.")


@bot.message_handler(commands=['add', ])
def add_habit_request(message):
    habit_dict = dict()
    bot.reply_to(message, "Напишите, какую привычку вы хотите добавить")
    habit_dict["id_telegram"] = message.chat.id
    bot.register_next_step_handler(message, add_habit_name_func, habit_dict)


def add_habit_name_func(message, habit_dict):
    name = message.text  # Получаем текст сообщения
    bot.send_message(message.chat.id, f"Добавляю {name} в список ваших привычек!")
    # получаем имя привычки для добавления в бд
    habit_dict["name"] = name
    bot.reply_to(message, "Напишите, время напоминания в формате XX:XX")
    bot.register_next_step_handler(message, add_habit_time_func, habit_dict)


@bot.message_handler(commands=['auth'])
def test_auth_func(message):
    token = token_store.get_token(message.chat.id)
    bot.send_message(message.chat.id, "Сейчас выполним проверку работы токена")
    response = requests.post(url="http://api:8000/check_auth/",
                             json={"user_id": message.chat.id},
                             headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 401 or response.status_code == 403:
        bot.send_message(message.chat.id,
                         "Ваш токен либо устарел, либо не создан."
                         " Нажмите /start для устранения проблемы")
        return


def add_habit_time_func(message, habit_dict):
    time_str = message.text  # Получаем текст сообщения
    time_obj = None
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
    except ValueError:
        bot.reply_to(message, "Не верный формат ввода. Напишите, время напоминания в формате XX:XX")
        bot.register_next_step_handler(message, add_habit_time_func, habit_dict)
        return
    habit_dict["time"] = time_str
    required_fields = ["id_telegram", "name", "time"]
    if all(field in habit_dict for field in required_fields):
        token = token_store.get_token(message.chat.id)
        result = requests.post(url="http://api:8000/add_habit/",
                               json=habit_dict,
                               headers={"Authorization": f"Bearer {token}"})
        if result.status_code == 401 or result.status_code == 403:
            bot.send_message(message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы"
                             " и проведите добавление заново")
            return
        try:
            bot.reply_to(message, f"Время напоминания установлено на {time_obj.time()}")
        except AttributeError:
            pass
    else:
        bot.reply_to(message, "Произошла ошибка при сборе данных. Попробуйте еще раз /add")
        print("Произошла ошибка при сборе данных")


@bot.message_handler(commands=['edit', ])
def add_habit_edit(message):
    token = token_store.get_token(message.chat.id)
    bot.reply_to(message, "Выберите привычку, которую хотите изменить")
    hub_response = requests.get(url="http://api:8000/get_habit",
                                json={'id': message.chat.id},
                                headers={"Authorization": f"Bearer {token}"})
    if hub_response.status_code == 401 or hub_response.status_code == 403:
        bot.send_message(message.chat.id,
                         "Ваш токен либо устарел, либо не создан."
                         " Нажмите /start для устранения проблемы")
        return
    hab_json = hub_response.json()
    for hab_data in hab_json:
        keyboard = InlineKeyboardMarkup()
        # 2. Создаем кнопки (text - что видит юзер, callback_data - что получает бот)
        button1 = InlineKeyboardButton(text='Изменить название', callback_data=f"edit_name;{hab_data['name']}")
        button2 = InlineKeyboardButton(text='Изменить время', callback_data=f"edit_time;{hab_data['name']}")
        button3 = InlineKeyboardButton(text='Удалить привычку', callback_data=f"delete_habit;{hab_data['name']}")
        button4 = InlineKeyboardButton(text='Посмотреть счетчик', callback_data=f"view_count;{hab_data['name']}")
        # 3. Добавляем кнопки в клавиатуру
        keyboard.add(button1, button2, button3, button4)
        # 4. Отправляем сообщение с клавиатурой
        bot.send_message(message.chat.id,
                         f"Название: {hab_data['name']}, время: {hab_data['time']}",
                         reply_markup=keyboard)


def set_new_name_message(message, data):
    msg = bot.send_message(message, "Введите новое название привычки")
    bot.register_next_step_handler(msg, set_new_name_func, data=data)


def set_new_name_func(message, data):
    data['name'] = message.text
    token = token_store.get_token(message.chat.id)
    result = requests.post(url="http://api:8000/edit_habit/name",
                           json=data,
                           headers={"Authorization": f"Bearer {token}"})
    if result.status_code == 401 or result.status_code == 403:
        bot.send_message(message.chat.id,
                         "Ваш токен либо устарел, либо не создан."
                         " Нажмите /start для устранения проблемы")
        return
    bot.send_message(message.chat.id, f"Название изменено на {message.text}")


def set_new_time_message(message, data):
    msg = bot.send_message(message, "Введите новое время напоминания, в формате ХХ:ХХ")
    print(data)
    bot.register_next_step_handler(msg, set_new_time_func, data=data)


def set_new_time_func(message, data):
    try:
        datetime.strptime(message.text, "%H:%M")
        data['time'] = message.text
        token = token_store.get_token(message.chat.id)
        result = requests.post(url="http://api:8000/edit_habit/time",
                               json=data,
                               headers={"Authorization": f"Bearer {token}"})
        if result.status_code == 401 or result.status_code == 403:
            bot.send_message(message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            return
        bot.send_message(message.chat.id, f"Время напоминания изменено на {message.text}")
    except ValueError:
        bot.reply_to(message, "Не верный формат ввода. Напишите, время напоминания в формате XX:XX")
        set_new_time_message(message.chat.id, data=data)


def delete_habit_message(message, data):
    bot.send_message(message, f"Ваша привычка {data['name']} была удалена")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data.split(';')
    temp_dict = dict()
    temp_dict['id_telegram'] = call.message.chat.id
    temp_dict['name'] = data[1]
    token = token_store.get_token(call.message.chat.id)
    if data[0] == 'edit_name':
        hab_id = requests.post(url="http://api:8000/get_habit/id",
                               json=temp_dict,
                               headers={"Authorization": f"Bearer {token}"})
        if hab_id.status_code == 401 or hab_id.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            return
        update_dict = dict()
        update_dict['id'] = hab_id.text
        update_dict['name'] = data[1]
        bot.answer_callback_query(call.id, text="Изменим название привычки")
        set_new_name_message(call.message.chat.id, data=update_dict)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
    elif data[0] == 'edit_time':
        bot.answer_callback_query(call.id, text="Изменим время напоминания")
        update_dict = dict()
        hab_id = requests.post(url="http://api:8000/get_habit/id",
                               json=temp_dict,
                               headers={"Authorization": f"Bearer {token}"})
        if hab_id.status_code == 401 or hab_id.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            return
        update_dict['id'] = hab_id.text
        update_dict['name'] = data[1]
        set_new_time_message(call.message.chat.id, data=update_dict)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
    elif data[0] == 'delete_habit':
        temp_dict['name'] = data[1]
        hab_id = requests.post(url="http://api:8000/get_habit/id",
                               json=temp_dict,
                               headers={"Authorization": f"Bearer {token}"})
        if hab_id.status_code == 401 or hab_id.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            return
        data_delete = dict()
        data_delete['id_habit'] = hab_id.text
        result = requests.delete(url="http://api:8000/get_habit/id",
                                 json=data_delete,
                                 headers={"Authorization": f"Bearer {token}"})
        if result.status_code == 401 or result.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            return
        delete_habit_message(call.message.chat.id, data=temp_dict)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
    elif data[0] == "view_count":
        count_result = requests.post(
            url="http://api:8000/get_count",
            json={'user_id': temp_dict['id_telegram'], 'name': temp_dict['name']},
            headers={"Authorization": f"Bearer {token}"})
        if count_result.status_code == 401 or count_result.status_code == 403:
            bot.send_message(call.message.chat.id,
                             "Ваш токен либо устарел, либо не создан."
                             " Нажмите /start для устранения проблемы")
            return
        bot.send_message(call.message.chat.id,
                         f"Количество выполнений '{temp_dict['name']}': {count_result.json()}")
    elif data[0] == 'completed':
        raw_data = data[1].split(':')
        request_up_count = requests.post(
            url="http://api:8000/edit_habit/up_count",
            json={'user_id': raw_data[0], 'name': raw_data[1]},
            headers={"Authorization": f"Bearer {token}"})
        bot.send_message(call.message.chat.id, "Выполнение привычки засчитано.")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        if request_up_count.json() is True:
            bot.send_message(call.message.chat.id,
                             "Вы успешно привили привычку, привычка будет удалена из списка.")
    elif data[0] == 'not_completed':
        bot.send_message(call.message.chat.id, "Выполнение привычки не засчитано.")
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)


def send_mes_for_user(user_id):
    bot.send_message(user_id, "Бот запущен и готов к работе")


def send_message_test(user_id, name):
    keyboard = InlineKeyboardMarkup()
    # 2. Создаем кнопки (text - что видит юзер, callback_data - что получает бот)
    button1 = InlineKeyboardButton(text='Выполнено', callback_data=f'completed;{user_id}:{name}')
    button2 = InlineKeyboardButton(text='Не выполнено', callback_data=f'not_completed;{user_id}:{name}')
    # 3. Добавляем кнопки в клавиатуру
    keyboard.add(button1, button2)
    # 4. Отправляем сообщение с клавиатурой
    bot.send_message(user_id, f"Напоминаю, что нужно выполнить '{name}'", reply_markup=keyboard)


if __name__ == "__main__":
    bot.infinity_polling()
