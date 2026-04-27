import requests
from requests.exceptions import Timeout
from fastapi import Response


# добавить отработку таймаутов в try except

def request_check_password(username, user_id, password):
    try:
        response = requests.post(url="http://api:8000/check_user",
                                 json={
                                     'username': username,
                                     'id_telegram': int(user_id),
                                     'password': str(password)
                                 },
                                 timeout=(3, 10))
        response.raise_for_status()
        print(response.text)
        return response
    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def request_add_habit(habit_data, token):
    try:
        response = requests.post(url="http://api:8000/add_habit/",
                                 json=habit_data,
                                 headers={"Authorization": f"Bearer {token}"},
                                 timeout=(3, 10))
        response.raise_for_status()
        print(response.text)
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def get_habits(user_id, token):
    try:
        response = requests.get(url="http://api:8000/get_habits",
                                json={'user_id': user_id},
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=(3, 10))
        response.raise_for_status()
        return response
    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def get_habit_name(id_habit, token):
    try:
        response = requests.get(url="http://api:8000/get_name_habit",
                                json={'id_habit': id_habit},
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=(3, 10))
        response.raise_for_status()
        print(response.text)
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def request_edit_name(data, token):
    try:
        response = requests.post(url="http://api:8000/edit_habit/name",
                                 json=data,
                                 headers={"Authorization": f"Bearer {token}"},
                                 timeout=(3, 10))
        response.raise_for_status()
        print(response.text)
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def request_edit_time(data, token):
    try:
        response = requests.post(url="http://api:8000/edit_habit/time",
                                 json=data,
                                 headers={"Authorization": f"Bearer {token}"},
                                 timeout=(3, 10))
        response.raise_for_status()
        print(response.text)
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def request_get_count(habit_id, token):
    try:
        response = requests.post(
            url="http://api:8000/get_count",
            json={'id_habit': habit_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=(3, 10))
        response.raise_for_status()
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def request_up_count(id_habit, token):
    try:
        response = requests.post(
            url="http://api:8000/edit_habit/up_count",
            json={"id_habit": id_habit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=(3, 10))
        response.raise_for_status()
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)


def request_delete_habit(data_delete, token):
    try:
        response = requests.delete(url="http://api:8000/get_habit/id",
                                   json=data_delete,
                                   headers={"Authorization": f"Bearer {token}"},
                                   timeout=(3, 10))
        response.raise_for_status()
        return response

    except Timeout:
        print("Запрос превысил время ожидания")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return Response(status_code=401)
