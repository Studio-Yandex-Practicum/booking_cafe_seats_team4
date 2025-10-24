from schemas.user import UserRole
from schemas.table import TableCreate as TableCreateSchema
from schemas.cafe import CafeCreate
from models.user import User
from models.table import Table
from models.cafe import Cafe
from crud.table import table_crud
from crud.cafe import cafe_crud
from core.security import hash_password
from core.config import settings
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


sys.path.append(str(Path(__file__).resolve().parent.parent))

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def ensure_user(
        session, login, password, username,
        role: UserRole, is_active: bool = True
) -> User:
    """
    Идемпотентно создает или обновляет пользователя с нужной ролью и статусом.
    Если пользователь существует, обновляет его роль и
    статус активности при необходимости.
    """
    user = await session.scalar(
        select(User).where((User.email == login)
                           | (User.phone == login)).limit(1)
    )

    if user:
        needs_update = False
        if user.role != role:
            user.role = role
            needs_update = True
        if user.is_active != is_active:
            user.is_active = is_active
            needs_update = True

        if needs_update:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(
                f"Пользователь '{login}' уже существует, статус обновлен "
                f"(Роль: {role.name}, Активен: {is_active})."
            )
        else:
            print(
                f"Пользователь '{login}' уже существует, "
                f"изменений не требуется."
            )
        return user

    new_user_data = {
        "username": username,
        "role": role,
        "is_active": is_active,
        "password_hash": hash_password(password),
    }
    if '@' in login:
        new_user_data["email"] = login
    else:
        new_user_data["phone"] = login

    new_user = User(**new_user_data)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    print(
        f"Пользователь '{login}' (Роль: {role.name}, "
        f"Активен: {is_active}) создан."
    )
    return new_user


async def seed_database():
    """Наполняет базу всеми необходимыми тестовыми данными для демонстрации."""
    async with SessionFactory() as session:
        print('--- Начало наполнения базы данных ---')

        print("\n1. Создание пользователей...")
        admin = await ensure_user(
            session, login='admin@example.com', password='password',
            username='admin', role=UserRole.ADMIN
        )
        manager1 = await ensure_user(
            session, login='manager1@example.com', password='password',
            username='manager1', role=UserRole.MANAGER
        )
        manager2 = await ensure_user(
            session, login='manager2@example.com', password='password',
            username='manager2', role=UserRole.MANAGER
        )
        regular_user = await ensure_user(
            session, login='user@example.com', password='password',
            username='user', role=UserRole.USER
        )
        inactive_user = await ensure_user(
            session, login='inactive@example.com', password='password',
            username='inactive_user', role=UserRole.USER, is_active=False
        )

        print("\n2. Создание кафе...")

        cafe1 = await cafe_crud.get_by_name_and_address(
            session,
            name="Кофейня 'Уют'",
            address='г. Москва, ул. Тверская, д. 1'
        )
        if not cafe1:
            cafe1_data = CafeCreate(
                name="Кофейня 'Уют'",
                address='г. Москва, ул. Тверская, д. 1',
                phone='+7(495)111-11-11',
                description='Лучший кофе в центре.',
                managers_id={manager1.id}
            )
            cafe1 = await cafe_crud.create(cafe1_data, session)
            print(f"-> Кафе '{cafe1.name}' создано.")
        else:
            print(f"-> Кафе '{cafe1.name}' уже существует.")

        cafe2 = await cafe_crud.get_by_name_and_address(
            session, name="Кафе 'Прохлада'",
            address='г. Санкт-Петербург, Невский пр., д. 28'
        )
        if not cafe2:
            cafe2_data = CafeCreate(
                name="Кафе 'Прохлада'",
                address='г. Санкт-Петербург, Невский пр., д. 28',
                phone='+7(812)222-22-22',
                description='Прохладительные напитки и закуски.',
                managers_id={manager2.id}
            )
            cafe2 = await cafe_crud.create(cafe2_data, session)
            print(f"-> Кафе '{cafe2.name}' создано.")
        else:
            print(f"-> Кафе '{cafe2.name}' уже существует.")

        inactive_cafe = await cafe_crud.get_by_name_and_address(
            session, name="Закрытое кафе", address='Нигде'
        )
        if not inactive_cafe:
            inactive_cafe_data = CafeCreate(
                name="Закрытое кафе",
                address='Нигде', phone='+7(000)000-00-00',
                description='Это кафе не работает.',
                managers_id={manager1.id}
            )
            inactive_cafe = await cafe_crud.create(inactive_cafe_data, session)
            stmt = update(Cafe).where(
                Cafe.id == inactive_cafe.id).values(is_active=False)
            await session.execute(stmt)
            await session.commit()
            print(f"-> Создано неактивное кафе: '{inactive_cafe.name}'.")
        else:
            print(f"-> Неактивное кафе '{inactive_cafe.name}' уже существует.")

        print("\n3. Создание столов...")

        existing_tables_cafe1 = await table_crud.get_multi(
            session, cafe_id=cafe1.id
        )
        if len(existing_tables_cafe1) == 0:
            tables_for_cafe1 = [
                TableCreateSchema(description='Столик у окна', seat_number=2),
                TableCreateSchema(
                    description='Большой стол в центре', seat_number=6),
            ]
            for table_data in tables_for_cafe1:
                await table_crud.create(table_data, session, cafe_id=cafe1.id)
            print(f"-> Созданы активные столы для кафе '{cafe1.name}'.")
        else:
            print(f"-> Столы для кафе '{cafe1.name}' уже существуют.")

        if not any(
            t.description == "Сломанный столик" for t in existing_tables_cafe1
        ):
            inactive_table_data = TableCreateSchema(
                description="Сломанный столик", seat_number=1)
            inactive_table = await table_crud.create(
                inactive_table_data, session, cafe_id=cafe1.id
            )
            stmt = update(Table).where(
                Table.id == inactive_table.id).values(is_active=False)
            await session.execute(stmt)
            await session.commit()
            print(
                f"-> Создан неактивный стол '{inactive_table.description}' "
                f"в кафе '{cafe1.name}'."
            )
        else:
            print(f"-> Неактивный стол в кафе '{cafe1.name}' уже существует.")

        existing_tables_cafe2 = await table_crud.get_multi(
            session, cafe_id=cafe2.id
        )
        if len(existing_tables_cafe2) == 0:
            tables_for_cafe2 = [
                TableCreateSchema(
                    description='Стол на веранде', seat_number=4),
            ]
            for table_data in tables_for_cafe2:
                await table_crud.create(table_data, session, cafe_id=cafe2.id)
            print(f"-> Созданы столы для кафе '{cafe2.name}'.")
        else:
            print(f"-> Столы для кафе '{cafe2.name}' уже существуют.")

        print('\n--- Наполнение базы данных завершено ---')


if __name__ == '__main__':

    if sys.platform.startswith('win'):
        try:
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    asyncio.run(seed_database())
