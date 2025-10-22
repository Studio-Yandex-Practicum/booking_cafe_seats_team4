import io
import smtplib
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from email.mime.text import MIMEText
from email.utils import formatdate
from email.header import Header

from celery_tasks.celery_app import celery_app
from core.config import settings
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
    from api.validators.media import media_exist, check_media_id
    media_id = check_media_id(media_id)
    filename = f'{media_id}.jpg'
    file_path = MEDIA_PATH / filename
    file_path = media_exist(file_path)
    return file_path


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


@celery_app.task(name='send_email_task')
def send_email_task(recipient: str, subject: str, body: str) -> str:
    """Отправить одно письмо пользователю или менеджеру."""

    success = send_email_smtp(recipient, subject, body)
    if success:
        return f'Cообщение отправлено {recipient}'
    else:
        return f'Ошибка отправки сообщения для {recipient}'


@celery_app.task(name='send_mass_mail')
def send_mass_mail(body: str, subject: str = 'Новая акция!') -> str:
    """Разослать письмо всем активным пользователям."""
    sync_database_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')
    engine = create_engine(sync_database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
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
