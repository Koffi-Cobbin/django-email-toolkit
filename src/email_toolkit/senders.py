"""
Generic templated-email senders.

Fixes baked in from the original repo review:
- No `print(message)` of secrets/tokens — uses `logging` instead, and never
  logs the rendered body (which contains the reset/activation link).
- Callers get a real exception on failure instead of a silent print(), so
  a view can decide whether to 500, retry, or degrade gracefully — instead
  of the send() call raising an unhandled SMTP error mid-request.
- Async-ready: if Celery is installed and EMAIL_TOOLKIT["USE_CELERY"] is
  True, sends go through a task queue instead of blocking the request.
"""

import logging

from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .conf import get_toolkit_settings
from .tokens import activation_token, password_reset_token, build_action_url

logger = logging.getLogger("email_toolkit")


class EmailSendError(Exception):
    """Raised when a templated email fails to send and fail_silently is False."""


def send_templated_email(subject, template_name, context, to_email, fail_silently=None):
    """
    Render `template_name` with `context` and send it to `to_email`.

    Does not print or log the rendered body (it may contain a reset link).
    """
    cfg = get_toolkit_settings()
    fail_silently = cfg.fail_silently if fail_silently is None else fail_silently

    try:
        message = render_to_string(template_name, context)
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=cfg.default_from_email,
            to=[to_email],
        )
        email.send(fail_silently=False)
        logger.info("Sent '%s' email to %s", subject, to_email)
        return True
    except Exception as exc:
        logger.exception("Failed to send '%s' email to %s", subject, to_email)
        if fail_silently:
            return False
        raise EmailSendError(str(exc)) from exc


def dispatch_email(subject, template_name, context, to_email, fail_silently=None):
    """
    Same as send_templated_email, but routes through Celery when configured,
    so callers don't block the request/response cycle waiting on SMTP.

    Falls back to a synchronous send if Celery isn't installed or isn't
    enabled — safe to call in every project, whether or not Celery is set up.
    """
    cfg = get_toolkit_settings()
    if cfg.use_celery:
        try:
            from .tasks import send_templated_email_task

            send_templated_email_task.delay(subject, template_name, context, to_email)
            return True
        except ImportError:
            logger.warning(
                "EMAIL_TOOLKIT['USE_CELERY'] is True but Celery isn't installed; "
                "sending synchronously instead."
            )
    return send_templated_email(subject, template_name, context, to_email, fail_silently)


def send_activation_email(user, url_template, extra_context=None, fail_silently=None):
    """
    url_template: e.g. "https://app.example.com/activate/{uid}/{token}/"
    """
    cfg = get_toolkit_settings()
    action_url = build_action_url(user, url_template, activation_token)
    context = {"user": user, "action_url": action_url, **(extra_context or {})}
    return dispatch_email(
        subject=cfg.activation_subject,
        template_name="email_toolkit/activation_email.txt",
        context=context,
        to_email=user.email,
        fail_silently=fail_silently,
    )


def send_password_reset_email(user, url_template, extra_context=None, fail_silently=None):
    """
    url_template: e.g. "https://app.example.com/reset-password/{uid}/{token}/"
    """
    cfg = get_toolkit_settings()
    action_url = build_action_url(user, url_template, password_reset_token)
    context = {"user": user, "action_url": action_url, **(extra_context or {})}
    return dispatch_email(
        subject=cfg.password_reset_subject,
        template_name="email_toolkit/password_reset_email.txt",
        context=context,
        to_email=user.email,
        fail_silently=fail_silently,
    )
