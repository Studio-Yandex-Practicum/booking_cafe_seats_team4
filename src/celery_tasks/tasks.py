import io
import logging
import smtplib
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from celery_tasks.celery_app import celery_app
from core.config import settings
from models.user import User

logger = logging.getLogger(__name__)

MEDIA_PATH = Path(settings.MEDIA_PATH)
MEDIA_PATH.mkdir(parents=True, exist_ok=True)
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD


@celery_app.task(name='save_image')
def save_image(image_data: bytes, media_id: str) -> dict[str, str]:
    """Сохранить картинку как JPEG `<media_id>.jpg`.

    Возвращает словарь с ключом ``media_id``; при ошибке
    дополнительно возвращает ключ ``error`` с текстом ошибки.
    """
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


@celery_app.task(name='send_email_task')
def send_email_task(recipient: str, subject: str, body: str) -> str:
    """Отправить одно письмо пользователю."""
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        message = f'Subject: {subject}\n\n{body}'
        server.sendmail(SMTP_USERNAME, recipient, message)
        server.quit()
    except Exception as e:  # noqa: BLE001
        return str(e)
    return f'Email sent to {recipient}'


@celery_app.task(name='send_mass_mail')
def send_mass_mail(body: str) -> str:
    """Разослать письмо всем активным пользователям."""
    sync_database_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')
    engine = create_engine(sync_database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    recipients = session.execute(select(User).where(User.is_active))
    recipients = recipients.scalars().all()
    logger.info(f'GGG {len(recipients)}')
    if not recipients:
        session.close()
        engine.dispose()
        return 'Нет активных пользователей'
    for recipient in recipients:
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            subject = 'Новая акция!'
            message = f'Subject: {subject}\n\n{body}'
            message = message.encode('utf-8')
            server.sendmail(SMTP_USERNAME, recipient.email, message)
            server.quit()
        except Exception as e:  # noqa: BLE001
            print(str(e))
    return 'Email sent to all users'
