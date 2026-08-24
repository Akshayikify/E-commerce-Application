from django.core.mail import send_mail
from celery import shared_task
from django.conf import settings
import os

@shared_task
def send_confirmation_mail(order_id, to_mail):
    from_email = getattr(settings, 'EMAIL_HOST_USER', None) or os.getenv('EMAIL_HOST_USER') or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    return send_mail(
        subject=f'Order #{order_id} is confirmed',
        message=f"Your order #{order_id} is successfully placed.",
        from_email=from_email,
        recipient_list=[to_mail],
        fail_silently=False
    )