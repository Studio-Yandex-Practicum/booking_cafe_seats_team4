BOOKING CAFÉ API - README файл:

===============================================================
ОПИСАНИЕ
===============================================================
FastAPI‑сервис для бронирования мест в кафе. Проект реализует:
• JWT‑аутентификацию (Bearer) и ролевую модель (USER / MANAGER / ADMIN)
• CRUD над сущностями: пользователи, кафе, столы, слоты, блюда, бронирования, акции
• Единый формат ошибок (code, message) и централизованные хендлеры
• Логирование с форматированием и ротацией, возможность добавлять user‑контекст
• Фоновые задачи на Celery: загрузка изображений, массовые рассылки по email
• Alembic‑миграции, тесты на auth/users, pre‑commit + ruff

Репозиторий ориентирован на работу локально и в CI (GitHub Actions).

===============================================================
ТЕХНОЛОГИИ
===============================================================
• Python, FastAPI, Pydantic
• PostgreSQL (async SQLAlchemy), Alembic
• JWT (jose), passlib (bcrypt_sha256)
• Celery (+ RabbitMQ и Redis по умолчанию)
• Uvicorn (dev‑сервер)
• pre‑commit, ruff
• GitHub Actions (линт, стиль)

===============================================================
СТРУКТУРА ПРОЕКТА (ключевые директории/файлы)
===============================================================
project/
  ├─ infra/
  │   ├─ .env.example
  │   └─ docker-compose.yml          — PostgreSQL 17 (volume: pgdata)
  └─ src/
      ├─ main.py                     — создание приложения FastAPI
      ├─ requirements.txt
      ├─ alembic/                    — миграции
      │   ├─ env.py, script.py.mako
      │   └─ versions/…
      ├─ api/
      │   ├─ __init__.py             — сборка роутеров
      │   ├─ deps.py                 — зависимости (Bearer, текущий user, role‑check)
      │   ├─ exceptions.py           — единые обработчики ошибок (CustomError + X‑Request‑ID)
      │   ├─ responses.py            — схемы/примеры типовых ответов для Swagger
      │   ├─ table_service.py
      │   ├─ endpoints/
      │   │   ├─ auth.py             — POST /auth/login
      │   │   ├─ users.py            — /users, /users/me, управление пользователями
      │   │   ├─ cafe.py             — /cafe (CRUD кафе)
      │   │   ├─ table.py            — /table (столы)
      │   │   ├─ slots.py            — /slots (временные слоты)
      │   │   ├─ dishes.py           — /dishes (меню/блюда)
      │   │   ├─ booking.py          — /booking (бронирования)
      │   │   ├─ media.py            — /media (загрузка изображений, Celery)
      │   │   └─ action.py           — /actions (акции, массовые рассылки)
      │   └─ validators/
      │       ├─ users.py, cafe.py, table.py, slots.py, dishes.py, media.py
      │       └─ …                   — прикладные проверки входных данных
      ├─ core/
      │   ├─ config.py               — загрузка настроек из .env / infra/.env
      │   ├─ db.py                   — ASGI‑движок БД, асинхронные сессии
      │   ├─ logging.py              — лог‑формат, ротация, LoggerAdapter для user‑контекста
      │   ├─ security.py             — hash/verify, создание/декодирование JWT
      │   ├─ email_templates.py
      │   └─ constants.py
      ├─ crud/                       — слой доступа к данным
      │   ├─ users.py, cafe.py, table.py, slots.py, dishes.py, action.py, …
      ├─ models/                     — SQLAlchemy‑модели
      │   ├─ user.py, cafe.py, table.py, slots.py, dish.py, booking.py, action.py, relations.py
      │   └─ base.py, __init__.py
      ├─ schemas/                    — Pydantic‑схемы ввода/вывода
      │   ├─ auth.py, user.py, cafe.py, table.py, slots.py, dish.py, booking.py, action.py, media.py
      │   └─ common.py               — общая схема ошибок и др.
      ├─ services/
      │   └─ users.py                — ensure_superuser и прикладные операции
      ├─ celery_tasks/
      │   ├─ celery_app.py           — конфигурация Celery
      │   └─ tasks.py                — save_image, send_mass_mail
      └─ tests/
          ├─ test_cafes.py           — проверка кафе
          ├─ test_tables.py          — проверка столов
          ├─ test_auth.py            — проверка логина (422 на неверные креды)
          └─ test_users.py           — создание пользователя, дубликаты и пр.

===============================================================
БЫСТРЫЙ СТАРТ
===============================================================
1) Клонировать репозиторий и создать виртуальное окружение:
   python -m venv .venv
   # Windows: .venv\\Scripts\\activate
   # macOS/Linux: source .venv/bin/activate

2) Установить зависимости:
   pip install -r src/requirements.txt

3) Подготовить окружение (.env):
   • Скопируйте infra/.env.example → .env и заполните значения
   • Либо создайте .env вручную (см. раздел «Переменные окружения»)

4) Поднять PostgreSQL (вариант через docker-compose):
   cd infra
   docker compose up -d
   # проверка: psql postgres://…:5432

5) Применить миграции:
   cd ../src
   alembic upgrade head
   (опционально запустить python -m services.db_seed для наполнения базы тестовыми данными юзеров, кафе и столов)

6) Запустить приложение:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

   Swagger UI:  http://localhost:8000/docs
   ReDoc:       http://localhost:8000/redoc
   Health:      GET /  →  {{"status":"ok"}}

===============================================================
ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (.env)
===============================================================
JWT / AUTH
• SECRET=CHANGE_ME_SUPER_SECRET_32CHARS_MIN
• JWT_ALGO=HS256
• TOKEN_IDLE_TTL_MIN=30              # Idle‑TTL, мин; валидность «с момента последнего запроса»

БАЗА ДАННЫХ
• DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
  # Если не задан, собирается из нижеследующих:
• POSTGRES_USER=
• POSTGRES_PASSWORD=
• POSTGRES_SERVER=localhost
• POSTGRES_PORT=5432
• POSTGRES_DB=

МЕДИА / ХРАНИЛИЩЕ
• MEDIA_PATH=/media                  # папка для сохранения изображений

CELERY / БРОКЕРЫ
• CELERY_BROKER_URL=amqp://guest:guest@localhost:5672/   # RabbitMQ
• CELERY_RESULT_BACKEND=redis://localhost:6379/0         # Redis

SMTP (для рассылок из /actions)
• SMTP_HOST=smtp.yandex.ru
• SMTP_PORT=587
• SMTP_USERNAME=python-plus-53-54-cafe@yandex.ru
• SMTP_PASSWORD=***

ЛОГИРОВАНИЕ
• LOG_LEVEL=INFO
• LOG_FILE=                         # необязательный путь до файла для ротации логов

===============================================================
ЗАПУСК CELERY
===============================================================
Требуются брокер RabbitMQ и Redis (по умолчанию указан localhost).
Запуск воркера Celery:
  celery -A celery_tasks.celery_app:celery_app worker -l info

===============================================================
АУТЕНТИФИКАЦИЯ И РОЛИ
===============================================================
Логин:
  POST /auth/login
  Content-Type: application/x-www-form-urlencoded
  body: login=<email|phone>&password=<string>

Успех (200):
  {{ "access_token": "<JWT>", "token_type": "bearer" }}

Ошибка (422):
  {{ "code": 422, "message": "Неверные имя пользователя или пароль" }}
  # Для неактивного пользователя — 422 с message="Пользователь неактивен"

Защита эндпоинтов:
  Authorization: Bearer <JWT>

Ролевые ограничения:
  • require_manager_or_admin — доступ только MANAGER/ADMIN (403 иначе)

===============================================================
API — ОБЗОР МОДУЛЕЙ
===============================================================
• /auth        — вход, выдача JWT
• /users       — создание пользователя, профиль (/users/me), чтение/обновление/деактивация
• /cafe        — создание/обновление/список кафе (роль‑чек для менеджеров/админов)
• /table       — управление столами (привязка к кафе)
• /slots       — управление временными слотами бронирования
• /dishes      — управление блюдами/меню
• /booking     — создание/чтение/отмена бронирований
• /media       — загрузка изображений (JPG/PNG); асинхронное сохранение через Celery
• /actions     — управление акциями; массовая email‑рассылка (Celery)

Примечание: фактические поля запросов/ответов см. в Swagger (/docs).

===============================================================
ЕДИНЫЙ ФОРМАТ ОШИБОК
===============================================================
Любая ошибка возвращается в следующем формате:
  {{ "code": <int>, "message": "<str>" }}

Примеры:
  • 401 Unauthorized  → {{ "code": 401, "message": "Требуется авторизация" }}
  • 403 Forbidden     → {{ "code": 403, "message": "Недостаточно прав" }}
  • 404 Not Found     → {{ "code": 404, "message": "Не найдено" }}
  • 422 Unprocessable → {{ "code": 422, "message": "Неверные данные запроса" }}
  • 400 Bad Request   → нарушения ограничений БД (дубликаты и т.п.)

Дополнительно:
  • В error‑ответах проставляется заголовок X‑Request‑ID (для трассировки).
  • Обработчики: api/exceptions.py (HTTPException, RequestValidationError, IntegrityError, Exception)

===============================================================
ЛОГИРОВАНИЕ
===============================================================
• Формат: "%(asctime)s | %(levelname)s | %(name)s | user=%(user)s id=%(user_id)s | %(message)s"
• Ротация: RotatingFileHandler (LOG_MAX_BYTES, LOG_BACKUP_COUNT)
• UserAdapter добавляет контекст пользователя (user, user_id), либо SYSTEM по умолчанию
• Уровень и файл задаются через LOG_LEVEL и LOG_FILE

===============================================================
МОДЕЛИ ДАННЫХ (в общих чертах)
===============================================================
• User      — логин (email/phone), username, роль, is_active, password_hash
• Cafe      — наименование, адрес, менеджер (связь user→cafe)
• Table     — столы в кафе, емкость/номер и пр.
• Slot      — временные интервалы для бронирования (HH:MM)
• Dish      — блюда/меню (наименование, описание, цена и др.)
• Booking   — пользователь, кафе/стол, дата/время слота, статус
• Action    — маркетинговые акции (вкл. массовые рассылки)

Реальные поля смотрите в src/models/*.py и в схеме Swagger.

===============================================================
КАЧЕСТВО КОДА, PRE-COMMIT, ТЕСТЫ
===============================================================
• Установка хуков:
    pip install pre-commit
    pre-commit install
    pre-commit run --all-files

• Ruff:
    ruff check . --fix
    ruff format .

• Тесты:
    pytest -q

• GitHub Actions:
    .github/workflows/style_check.yml, main.yml

===============================================================

## ПРИМЕЧАНИЯ (правила проекта)

- Все **защищённые эндпоинты** требуют валидного JWT‑токена.
- Пользователь может **просматривать/изменять только свои данные** там, где это предусмотрено (профиль, свои бронирования).
- Создание/изменение справочников (**кафе, столы, слоты, блюда, акции**) - только для **MANAGER/ADMIN**.
- Один пользователь **не может забронировать один и тот же слот/столик дважды** (конфликты слотов запрещены).
- **Отменять/редактировать** бронирование может его автор; менеджер — в пределах своего кафе; админ — без ограничений.
- Все ошибки возвращаются в формате `CustomError` (`code`, `message`); для трассировки используется `X‑Request‑ID`.
- Загрузка медиа (если включено) — только изображения; сохранение асинхронно (через Celery).


===============================================================

## БЛАГОДАРНОСТИ

Проект выполнен в рамках учебного курса «Python‑разработчик (расширенный)» от [Яндекс Практикум](https://practicum.yandex.ru/).
Все участники команды завершили проект, успешно реализовав свои зоны ответственности.
