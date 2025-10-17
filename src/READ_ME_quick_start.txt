# Быстрый старт (локально)

## Запуск всех сервисов
```
bash
cd src
docker compose up -d --build
```

## Сервисы после запуска

- API: http://localhost:8000/docs
- База данных: localhost:5432
- Redis: localhost:6379
- RabbitMQ: http://localhost:15672 (логин: guest, пароль: guest)

## Проверить статус

```
bash
docker compose ps
```

# Создать суперпользователя

```
bash
docker compose exec web python -m services.users
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
## Остановить все сервисы
docker compose down

## Остановить и удалить все данные
docker compose down -v

## Посмотреть логи
docker compose logs web

## Перезапустить конкретный сервис
docker compose restart web

Alembic (из `src/`):
```bash
alembic heads
alembic history
alembic downgrade -1   # на один шаг назад
```

---
