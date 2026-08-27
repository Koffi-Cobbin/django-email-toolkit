"""
Optional Celery task. Only imported (see senders.dispatch_email) when
EMAIL_TOOLKIT["USE_CELERY"] is True — projects without Celery installed
never touch this module.
"""

from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_templated_email_task(self, subject, template_name, context, to_email):
    from .senders import send_templated_email

    try:
        send_templated_email(subject, template_name, context, to_email, fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)
