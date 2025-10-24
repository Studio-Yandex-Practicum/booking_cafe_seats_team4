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

def send_email_smtp(recipient: str, subject: str, body: str) -> bool:
    """Общая функция для отправки email через SMTP."""
    
    print(f"🔧 SMTP attempt: {recipient}")
    print(f"🔧 SMTP settings - Host: {SMTP_HOST}, Port: {SMTP_PORT}, User: {SMTP_USERNAME}")
    
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        print("✅ SMTP connection established")
        
        server.starttls()
        print("✅ TLS started")
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✅ SMTP login successful")
        
        message = MIMEText(body, 'plain', 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        message['From'] = SMTP_USERNAME
        message['To'] = recipient
        message['Date'] = formatdate(localtime=True)
        
        server.sendmail(SMTP_USERNAME, recipient, message.as_string())
        print("✅ Email sent via SMTP")
        
        server.quit()
        print("✅ SMTP connection closed")
        return True
        
    except Exception as e:
        print(f"❌ SMTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
# def send_email_smtp(recipient: str, subject: str, body: str) -> bool:
#     """Общая функция для отправки email через SMTP."""
#     try:
#         server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
#         server.starttls()
#         server.login(SMTP_USERNAME, SMTP_PASSWORD)
#         message = MIMEText(body, 'plain', 'utf-8')
#         message['Subject'] = Header(subject, 'utf-8')
#         message['From'] = SMTP_USERNAME
#         message['To'] = recipient
#         message['Date'] = formatdate(localtime=True)
#         server.sendmail(SMTP_USERNAME, recipient, message.as_string())
#         server.quit()
#         return True
#     except Exception:
#         return False


def create_sync_session():
    """Функция создания синхронной сессии для celery задач"""

    sync_database_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')
    engine = create_engine(sync_database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session, engine

@celery_app.task(name='send_email_task')
def send_email_task(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    """Отправить одно письмо пользователю или менеджеру."""
    
    print(f"📨 START send_email_task: {recipient}, subject: {subject}")
    
    try:
        success = send_email_smtp(recipient, subject, body)
        if success:
            print(f"✅ Email sent successfully to {recipient}")
            return f'Сообщение отправлено {recipient}'
        else:
            print(f"❌ Failed to send email to {recipient}")
            return f'Ошибка отправки сообщения для {recipient}'
    except Exception as e:
        print(f"💥 Error in send_email_task: {str(e)}")
        return f'Ошибка отправки сообщения для {recipient}: {str(e)}'
# @celery_app.task(name='send_email_task')
# def send_email_task(
#     recipient: str,
#     subject: str,
#     body: str,
# ) -> str:
#     """Отправить одно письмо пользователю или менеджеру."""
#     success = send_email_smtp(recipient, subject, body)
#     if success:
#         return f'Cообщение отправлено {recipient}'
#     return f'Ошибка отправки сообщения для {recipient}'


@celery_app.task(name='send_mass_mail')
def send_mass_mail(body: str, subject: str = 'Новая акция') -> str:
    """Разослать письмо всем активным пользователям."""

    session, engine = create_sync_session()
    try:
        recipients = session.execute(select(User).where(User.is_active))
        recipients = recipients.scalars().all()
        if not recipients:
            return 'Нет активных пользователей'
        successful_sends = 0
        for recipient in recipients:
            success = send_email_smtp(recipient.email, subject, body)
            if success:
                successful_sends += 1
        return f'Сообщение отправлено {successful_sends} пользователям'
    finally:
        session.close()
        engine.dispose()


# @celery_app.task(name='send_booking_notification')
# def send_booking_notification(
#         booking_id: int,
#         reminder_task_id: Optional[str] = None) -> str:
#     """Основная задача отправки уведомлений о бронировании"""

#     if reminder_task_id:
#         task = AsyncResult(reminder_task_id)
#         task.revoke(terminate=True)
#         return f"Задача напоминания {reminder_task_id} отменена"

#     session, engine = create_sync_session()
#     try:
#         booking = session.get(Booking, booking_id)
#         if not booking.is_active:
#             return 'Бронирование отменено'
#         cafe = session.get(Cafe, booking.cafe_id)
#         user = session.get(User, booking.user_id)
#         managers = cafe.managers
#         slots = booking.slots_id
#         earliest_slot = min(
#             slots,
#             key=lambda x: datetime.strptime(
#                 x.start_time, '%H:%M'
#             ))
#         lastest_slot = max(
#             slots,
#             key=lambda x: datetime.strptime(
#                 x.start_time, '%H:%M'
#             ))
#         email_body = BOOKING_CONFIRMATION_TEMPLATE.format(
#             username='ddd',
#             booking_date=booking.booking_date,
#             cafe=cafe.name,
#             first_slot=earliest_slot.start_time,
#             last_slot=lastest_slot.end_time
#         )
#         if user.email:
#             send_email_task.delay(
#                 user.email,
#                 'Подтверждение бронирования',
#                 body=email_body
#             )
#             reminder_task = send_email_task.apply_async(
#                 args=[user.email, 'Напоминание о бронировании', email_body],
#                 eta=datetime.combine(
#                     booking.booking_date,
#                     datetime.strptime(
#                         earliest_slot.start_time, '%H:%M'
#                     ).time()) - timedelta(hours=1)
#             )
#             booking.reminder_task_id = reminder_task.id
#             session.commit()
#         email_body = BOOKING_INFORMATION_FOR_MANAGER.format(
#             cafe=cafe.name,
#             booking_date=booking.booking_date,
#             first_slot=earliest_slot.start_time,
#             last_slot=lastest_slot.end_time,
#             table=booking.tables_id
#         )
#         for manager in managers:
#             if manager.email:
#                 send_email_task.delay(
#                     manager.email,
#                     'Новое бронирование',
#                     email_body
#                 )
#         return 'Сообщение направлено менеджерам и пользователю'
#     finally:
#         session.close()
#         engine.dispose()
@celery_app.task(name='send_booking_notification')
def send_booking_notification(
        booking_id: int,
        reminder_task_id: Optional[str] = None) -> str:
    """Основная задача отправки уведомлений о бронировании"""

    print(f"🔔 START: send_booking_notification for booking_id: {booking_id}")

    if reminder_task_id:
        task = AsyncResult(reminder_task_id)
        task.revoke(terminate=True)
        return f"Задача напоминания {reminder_task_id} отменена"

    session, engine = create_sync_session()
    try:
        print(f"📋 STEP 1: Getting booking with ID: {booking_id}")
        booking = session.get(Booking, booking_id)
        
        if not booking:
            print("❌ ERROR: Booking not found")
            return 'Бронирование не найдено'
            
        print(f"✅ Booking found: ID={booking.id}, is_active={booking.is_active}")

        if not booking.is_active:
            print("❌ Booking is not active")
            return 'Бронирование отменено'

        print(f"📋 STEP 2: Getting cafe with ID: {booking.cafe_id}")
        cafe = session.get(Cafe, booking.cafe_id)
        if not cafe:
            print("❌ ERROR: Cafe not found")
            return 'Кафе не найдено'
        print(f"✅ Cafe found: {cafe.name}")

        print(f"📋 STEP 3: Getting user with ID: {booking.user_id}")
        user = session.get(User, booking.user_id)
        if not user:
            print("❌ ERROR: User not found")
            return 'Пользователь не найдены'
        print(f"✅ User found: {user.email}")

        print(f"📋 STEP 4: Getting managers for cafe")
        managers = cafe.managers
        print(f"✅ Managers found: {len(managers)}")

        print(f"📋 STEP 5: Processing slots")
        slots = booking.slots_id
        if not slots:
            print("❌ ERROR: No slots found")
            return 'Нет слотов для бронирования'
        print(f"✅ Slots found: {len(slots)}")

        earliest_slot = min(
            slots,
            key=lambda x: datetime.strptime(x.start_time, '%H:%M')
        )
        latest_slot = max(
            slots,
            key=lambda x: datetime.strptime(x.start_time, '%H:%M')
        )
        print(f"✅ Earliest slot: {earliest_slot.start_time}, Latest slot: {latest_slot.end_time}")

        print(f"📋 STEP 6: Preparing email templates")
        email_body = BOOKING_CONFIRMATION_TEMPLATE.format(
            username='ddd',
            booking_date=booking.booking_date,
            cafe=cafe.name,
            first_slot=earliest_slot.start_time,
            last_slot=latest_slot.end_time
        )
        print(f"✅ User email body prepared")

        print(f"📋 STEP 7: Sending email to user: {user.email}")
        if user.email:
            print(f"📧 Sending to user: {user.email}")
            send_email_task.delay(
                user.email,
                'Подтверждение бронирования',
                body=email_body
            )
            print("✅ User email task sent to Celery")

            print(f"📋 STEP 8: Creating reminder task")
            reminder_task = send_email_task.apply_async(
                args=[user.email, 'Напоминание о бронировании', email_body],
                eta=datetime.combine(
                    booking.booking_date,
                    datetime.strptime(earliest_slot.start_time, '%H:%M').time()
                ) - timedelta(hours=1)
            )
            booking.reminder_task_id = reminder_task.id
            session.commit()
            print(f"✅ Reminder task created: {reminder_task.id}")
        else:
            print("❌ User has no email")

        print(f"📋 STEP 9: Preparing manager emails")
        email_body_manager = BOOKING_INFORMATION_FOR_MANAGER.format(
            cafe=cafe.name,
            booking_date=booking.booking_date,
            first_slot=earliest_slot.start_time,
            last_slot=latest_slot.end_time,
            table=booking.tables_id
        )
        print("✅ Manager email body prepared")

        print(f"📋 STEP 10: Sending emails to {len(managers)} managers")
        manager_count = 0
        for manager in managers:
            if manager.email:
                print(f"📧 Sending to manager: {manager.email}")
                send_email_task.delay(
                    manager.email,
                    'Новое бронирование',
                    email_body_manager
                )
                manager_count += 1
        print(f"✅ Manager emails sent to Celery: {manager_count}")

        result = f'Сообщение направлено пользователю и {manager_count} менеджерам'
        print(f"🎉 COMPLETE: {result}")
        return result

    except Exception as e:
        print(f"💥 CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return f'Ошибка при отправке уведомлений: {str(e)}'
    finally:
        session.close()
        engine.dispose()
        print("🔚 END: Session closed")