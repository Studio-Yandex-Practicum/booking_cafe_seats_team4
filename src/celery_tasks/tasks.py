import io
import smtplib
from datetime import datetime, timedelta

from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path
from typing import Optional

from celery.result import AsyncResult
from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from celery_tasks.celery_app import celery_app
from core.config import settings
from core.email_templates import (BOOKING_CONFIRMATION_TEMPLATE,
                                  BOOKING_INFORMATION_FOR_MANAGER)
from models.booking import Booking
from models.cafe import Cafe
from models.user import User

MEDIA_PATH = Path(settings.MEDIA_PATH)
MEDIA_PATH.mkdir(parents=True, exist_ok=True)
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD


@celery_app.task(name='save_image')
def save_image(image_data: bytes, media_id: str) -> dict[str, str]:
    """Сохранить картинку как JPEG `<media_id>.jpg`."""

    try:
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        filename = f'{media_id}.jpg'
        file_path = MEDIA_PATH / filename
        image.save(file_path, 'JPEG', optimize=True)
        return {'media_id': media_id}
    except Exception as e:  # noqa: BLE001
        return {'media_id': media_id, 'error': str(e)}


@celery_app.task(name='get_image_task')
def get_image_task(media_id: str) -> str:
    """Celery задача для получения изображения по ID."""
    from api.validators.media import check_media_id, media_exist

    media_id = check_media_id(media_id)
    filename = f'{media_id}.jpg'
    # RET504: возвращаем результат напрямую без промежуточного присваивания
    return media_exist(MEDIA_PATH / filename)


def send_email_smtp(recipient: str, subject: str, body: str) -> bool:
    """Общая функция для отправки email через SMTP."""
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        message = MIMEText(body, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = SMTP_USERNAME
        message['To'] = recipient
        message['Date'] = formatdate(localtime=True)
        server.sendmail(SMTP_USERNAME, recipient, message.as_string())
        server.quit()
        return True
    except Exception:
        return False


def create_sync_session():
    """Функция создания синхронной сессии для celery задач"""

    sync_database_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')
    engine = create_engine(sync_database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session, engine


@celery_app.task(name='save_image')
def save_image(image_data: bytes, media_id: str) -> dict[str, str]:
    """Сохранить картинку как JPEG `<media_id>.jpg`."""

    try:
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        filename = f'{media_id}.jpg'
        file_path = MEDIA_PATH / filename
        image.save(file_path, 'JPEG', optimize=True)
        return {'media_id': media_id}
    except Exception as e:  # noqa: BLE001
        return {'media_id': media_id, 'error': str(e)}


@celery_app.task(name='get_image_task')
def get_image_task(media_id: str) -> str:
    """Celery задача для получения изображения по ID."""
    from api.validators.media import check_media_id, media_exist
    media_id = check_media_id(media_id)
    filename = f'{media_id}.jpg'
    file_path = MEDIA_PATH / filename
    file_path = media_exist(file_path)
    return file_path


@celery_app.task(name='send_email_task')
def send_email_task(
    recipient: str,
    body: str,
    subject: str = 'Новое бронирование!',
) -> str:
    """Отправить одно письмо пользователю или менеджеру."""
    success = send_email_smtp(recipient, subject, body)
    if success:
        return f'Cообщение отправлено {recipient}'
    return f'Ошибка отправки сообщения для {recipient}'


@celery_app.task(name='send_mass_mail')
def send_mass_mail(body: str, subject: str = 'Новая акция!') -> str:
    """Разослать письмо всем активным пользователям."""

    session, engine = create_sync_session()
    try:
        recipients = session.execute(select(User).where(User.is_active))
        recipients = recipients.scalars().all()
        if not recipients:
            return 'Нет активных пользователей'
        successful_sends = 0
        for recipient in recipients:
            success = send_email_smtp(recipient.email, body, subject)
            if success:
                successful_sends += 1
        return f'Сообщение отправлено {successful_sends} пользователям'
    finally:
        session.close()
        engine.dispose()


@celery_app.task(name='send_booling_notification')
def send_booking_notification(
        booking_id: int,
        reminder_task_id: Optional[str] = None) -> str:
    """Основная задача отправки уведомлений о бронировании"""

    if reminder_task_id:
        task = AsyncResult(reminder_task_id)
        task.revoke(terminate=True)
        return f"Задача напоминания {reminder_task_id} отменена"

    session, engine = create_sync_session()
    try:
        booking = session.get(Booking, booking_id)
        if not booking.is_active:
            return 'Бронирование отменено'
        cafe = session.get(Cafe, booking.cafe_id)
        user = session.get(User, booking.user_id)
        managers = cafe.managers
        slots = booking.slots_id
        earliest_slot = min(
            slots,
            key=lambda x: datetime.strptime(
                x.start_time, '%H:%M'
            ))
        lastest_slot = max(
            slots,
            key=lambda x: datetime.strptime(
                x.start_time, '%H:%M'
            ))
        email_body = BOOKING_CONFIRMATION_TEMPLATE.format(
            booking_date=booking.booking_date,
            cafe=cafe.name,
            first_slot=earliest_slot.start_time,
            last_slot=lastest_slot.end_time
        )
        if user.email:
            send_email_task.delay(user.email, body=email_body)
            reminder_task = send_email_task.apply_async(
                args=[user.email, 'Напоминание о бронировании', email_body],
                eta=datetime.combine(
                    booking.booking_date,
                    datetime.strptime(
                        earliest_slot.start_time, '%H:%M'
                    ).time()) - timedelta(hours=1)
            )
            booking.reminder_task_id = reminder_task.id
            session.commit()
        email_body = BOOKING_INFORMATION_FOR_MANAGER.format(
            cafe=cafe.name,
            booking_date=booking.booking_date,
            first_slot=earliest_slot.start_time,
            last_slot=lastest_slot.end_time,
            table=booking.tables_id
        )
        for manager in managers:
            if manager.email:
                send_email_task.delay(manager.email, body=email_body)
        return 'Сообщение направлено менеджерам и пользователю'
    finally:
        session.close()
        engine.dispose()
