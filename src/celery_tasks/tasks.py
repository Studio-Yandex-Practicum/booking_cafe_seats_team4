import io
import smtplib
from pathlib import Path

from PIL import Image
from sqlalchemy import select

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
def save_image(image_data: bytes, media_id: str):
    try:
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        filename = f'{media_id}.jpg'
        file_path = MEDIA_PATH / filename
        image.save(file_path, 'JPEG', optimize=True)
        return {
            'media_id': media_id,
        }

    except Exception as e:
        return {
            'media_id': media_id,
            'error': str(e)
        }


@celery_app.task(name='send_email_task')
def send_email_task(recipient, subject, body):
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login('your_email@example.com', SMTP_PASSWORD)
        message = f'Subject: {subject}\n\n{body}'
        server.sendmail('your_email@example.com', recipient, message)
        server.quit()

    except Exception as e:
        return str(e)
    return f'Email sent to {recipient}'


@celery_app.task(name='send_mass_mail')
async def send_mass_mail(body):
    recipients = select(User).where(User.is_active)
    recipients = recipients.scalars().all()
    for recipient in recipients:
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login('your_email@example.com', SMTP_PASSWORD)
            message = f'Subject: {recipient.username}\n\n{body}'
            server.sendmail('your_email@example.com', recipient.email, message)
            server.quit()

        except Exception as e:
            return str(e)
        return f'Email sent to {recipient.email}'
