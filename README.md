# Telegram bot tracking habits 

Данный проект позволяет пользователю привить привычки с помощью бота в Telegram.
Помогает пользователю лучше контролировать выполнение заданных им привычек.
 
## Технологический стек
- Python 3.11
- Poetry
- PostgreSQL
- SQLAlchemy
- Alembic
- PytelegramBotAPI
- FastAPI 
- PyJWT 
- Apscheduler
- Docker-compose

## Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/VladGrab/tg_habit_bot.git
   ```
2. Установка Docker:
   ```bash
   pip install docker==7.1.0
   ```
3. Создаем и запускаем связку контейнеров:
   ```bash
   docker-compose up --build
   ```
   
## 📝 Пример использования

- Начало работы бота
![Начало работы бота](screenshots/start.JPG)
- После введения пароля. Время жизни токена изменено на 20 минут
![После введения пароля](screenshots/enter_password.JPG)
- Добавление привычки
![Добавление привычки](screenshots/add_habit.JPG)
- Получение напоминания
![Получение напоминания](screenshots/receiving_reminder.JPG)
- Выбор действия 'Выполнено'
![Выбор действия 'Выполнено'](screenshots/set_complete.JPG)
- Просмотр списка привычек
![Просмотр списка привычек](screenshots/edit_habits.JPG)
- Истекло время действия токена
![Истекло время действия токена](screenshots/more_than_5_minutes.JPG)
- Изменение названия и времени напоминания
![Изменение названия и времени напоминания](screenshots/rename_and_update_time.JPG)
- Привитие привычки
![Привитие привычки](screenshots/full_complete.JPG)