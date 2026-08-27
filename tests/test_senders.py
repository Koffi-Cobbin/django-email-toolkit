from types import SimpleNamespace

from django.contrib.auth.models import User
from django.core import mail

from email_toolkit.senders import send_activation_email, send_password_reset_email


def _make_user(db):
    return User.objects.create_user(username="jane", email="jane@example.com", password="x")


def test_send_activation_email(db):
    user = _make_user(db)
    send_activation_email(user, "https://app.example.com/activate/{uid}/{token}/")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["jane@example.com"]
    assert "activate" in mail.outbox[0].body


def test_send_password_reset_email(db):
    user = _make_user(db)
    send_password_reset_email(user, "https://app.example.com/reset/{uid}/{token}/")

    assert len(mail.outbox) == 1
    assert "reset" in mail.outbox[0].body
