# Быстрый старт (локально)

## 1 Поднять Postgres в Docker
> Нужен Docker Desktop.

```bash
docker run --name cafe-pg \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=cafe \
  -p 5432:5432 -d postgres:15
```

Запуск:
```bash
docker compose up -d
```

---

## 2 Настроить окружение
Активируйте venv и поставьте зависимости:
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows (Git Bash/MINGW64)
# . .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
```

Создайте в папке infra/.env-файл на основе:

# DB (Postgres, async)
POSTGRES_USER=username
POSTGRES_PASSWORD=password
POSTGRES_DB=app_db
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432

# DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/app_db

# JWT
SECRET=CHANGE_ME_SUPER_SECRET_32CHARS_MIN
JWT_ALGO=HS256
TOKEN_IDLE_TTL_MIN=30

# logging
LOG_LEVEL=INFO
# LOG_FILE=./app.log

---

## 3 Примените миграции (из папки `src/`), если требуется.
```bash
cd src
alembic upgrade head
```

---

## 4 Запустите API (из папки `src/`)
```bash
uvicorn main:app --reload
```
Swagger: http://127.0.0.1:8000/docs

---

# Создание суперпользователя (ADMIN)
Запускать **из папки `src/`**

**Вариант 1. Интерактивно**
```bash
python -m services.users
```
Скрипт попросит `Login (email/phone)` и `Password`.

**Вариант 2. Одной командой через ENV**
- Git Bash / macOS / Linux:
  ```bash
  SU_LOGIN=admin@example.com SU_PASSWORD=PASSWORD python -m services.users
  ```
- PowerShell:
  ```powershell
  $env:SU_LOGIN="admin@example.com"; $env:SU_PASSWORD="PASSWORD"
  python -m services.users
  ```

Ожидаемый вывод:
```
OK: superuser id=3, login=admin@example.com, active=True, role=2
```

---

# Как авторизоваться в Swagger
1. `POST /auth/login`
   - **username**: email или телефон
   - **password**: пароль
   В ответ придёт `{"access_token": "...", "token_type": "bearer"}`.
2. Нажмите **Authorize** и вставьте токен в формате `Bearer <access_token>`.
3. Проверьте `GET /users/me`.

---

# Полезные команды
Остановить/удалить контейнер Postgres:
```bash
docker stop cafe-pg && docker rm cafe-pg
```

Alembic (из `src/`):
```bash
alembic heads
alembic history
alembic downgrade -1   # на один шаг назад
```

---
