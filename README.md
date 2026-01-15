# BOOKING CAFÉ API

## Описание

FastAPI-сервис для бронирования мест в кафе. Проект реализует:

- JWT-аутентификацию (Bearer) и ролевую модель (USER / MANAGER / ADMIN)
- CRUD над сущностями: пользователи, кафе, столы, слоты, блюда, бронирования, акции
- Единый формат ошибок (code, message) и централизованные хендлеры
- Логирование с форматированием и ротацией, возможность добавлять user-контекст
- Фоновые задачи на Celery: загрузка изображений, массовые рассылки по email
- Alembic-миграции, тесты на auth/users, pre-commit + ruff

Репозиторий ориентирован на работу локально и в CI (GitHub Actions).

---

## Технологии

- Python, FastAPI, Pydantic
- PostgreSQL (async SQLAlchemy), Alembic
- JWT (jose), passlib (bcrypt_sha256)
- Celery (+ RabbitMQ и Redis по умолчанию)
- Uvicorn (dev-сервер)
- pre-commit, ruff
- GitHub Actions (линт, стиль)

---

## Структура проекта

    project/
      ├─ infra/
      │   ├─ .env.example
      │   └─ docker-compose.yml
      └─ src/
          ├─ main.py
          ├─ requirements.txt
          ├─ alembic/
          │   ├─ env.py, script.py.mako
          │   └─ versions/…
          ├─ api/
          │   ├─ __init__.py
          │   ├─ deps.py
          │   ├─ exceptions.py
          │   ├─ responses.py
          │   ├─ table_service.py
          │   ├─ endpoints/
          │   │   ├─ auth.py
          │   │   ├─ users.py
          │   │   ├─ cafe.py
          │   │   ├─ table.py
          │   │   ├─ slots.py
          │   │   ├─ dishes.py
          │   │   ├─ booking.py
          │   │   ├─ media.py
          │   │   └─ action.py
          │   └─ validators/
          │       ├─ users.py, cafe.py, table.py, slots.py, dishes.py, media.py
          │       └─ …
          ├─ core/
          │   ├─ config.py
          │   ├─ db.py
          │   ├─ logging.py
          │   ├─ security.py
          │   ├─ email_templates.py
          │   └─ constants.py
          ├─ crud/
          ├─ models/
          ├─ schemas/
          ├─ services/
          ├─ celery_tasks/
          └─ tests/

---

## Быстрый старт

1. Создать виртуальное окружение:

       python -m venv .venv
       # Windows: .venv\Scripts\activate
       # macOS/Linux: source .venv/bin/activate

2. Установить зависимости:

       pip install -r src/requirements.txt

3. Подготовить окружение:

   Скопировать infra/.env.example → .env и заполнить значения

4. Поднять PostgreSQL:

       cd infra
       docker compose up -d

5. Применить миграции:

       cd ../src
       alembic upgrade head

6. Запустить приложение:

       uvicorn main:app --reload --host 0.0.0.0 --port 8000

---

## Переменные окружения

    SECRET=CHANGE_ME_SUPER_SECRET_32CHARS_MIN
    JWT_ALGO=HS256
    TOKEN_IDLE_TTL_MIN=30

    DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

    MEDIA_PATH=/media

    CELERY_BROKER_URL=amqp://guest:guest@localhost:5672/
    CELERY_RESULT_BACKEND=redis://localhost:6379/0

    SMTP_HOST=smtp.yandex.ru
    SMTP_PORT=587
    SMTP_USERNAME=python-plus-53-54-cafe@yandex.ru
    SMTP_PASSWORD=***

    LOG_LEVEL=INFO
    LOG_FILE=

---

## Запуск Celery

    celery -A celery_tasks.celery_app:celery_app worker -l info

---

## Аутентификация и роли

**Логин:**

POST /auth/login  
Content-Type: application/x-www-form-urlencoded  
body: login=<email|phone>&password=<string>

**Успех (200):**

    { "access_token": "<JWT>", "token_type": "bearer" }

**Ошибка (422):**

    { "code": 422, "message": "Неверные имя пользователя или пароль" }

---

## API — обзор модулей

- /auth — вход, выдача JWT
- /users — управление пользователями
- /cafe — кафе
- /table — столы
- /slots — временные слоты
- /dishes — блюда
- /booking — бронирования
- /media — загрузка изображений
- /actions — акции и рассылки

---

## Единый формат ошибок

Все ошибки возвращаются в формате:

    { "code": <int>, "message": "<str>" }

Примеры:

    { "code": 401, "message": "Требуется авторизация" }
    { "code": 403, "message": "Недостаточно прав" }
    { "code": 404, "message": "Не найдено" }
    { "code": 422, "message": "Неверные данные запроса" }

---

## Логирование

Формат:

    %(asctime)s | %(levelname)s | %(name)s | user=%(user)s id=%(user_id)s | %(message)s

---

## Модели данных

- User — логин, роль, is_active, password_hash
- Cafe — наименование, адрес, менеджер
- Table — столы в кафе
- Slot — временные интервалы
- Dish — меню
- Booking — бронирование
- Action — акции и рассылки

---

## Качество кода и тесты

    pre-commit install
    pre-commit run --all-files

    ruff check . --fix
    ruff format .

    pytest -q

---

## Правила проекта

- Все защищённые эндпоинты требуют JWT
- Пользователь работает только со своими данными
- MANAGER / ADMIN управляют справочниками
- Конфликтные бронирования запрещены

---

## Благодарности

Антон Иванов — https://github.com/Sktchxx  
Михаил Ефименко — https://github.com/Mikhail1589  
Артем Иванов — https://github.com/IvanovArtem123  
Надя Рыскина — https://github.com/dushanadik  
Алексей Прокунин — https://github.com/prokaleks
