FROM python:3.11

WORKDIR /code
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Делаем так, чтобы Poetry не создавал виртуальное окружение внутри контейнера
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.7.1

RUN pip install "poetry==2.3.3"
COPY pyproject.toml poetry.lock ./
RUN poetry install
# Копируем весь код
COPY . .

# CMD "uvicorn" "app.main:app" "--reload"
