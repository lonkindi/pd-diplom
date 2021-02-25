from celery import shared_task
from django.core.mail import EmailMultiAlternatives

from orders import settings
from shop.models import MyUser


@shared_task(name="new_order_email_task")
def new_order_email_task(user_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    # send an e-mail to the user
    user = MyUser.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса заказа",
        # message:
        'Заказ сформирован',
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()
