"""
Small env-var helpers with real type casting.

The bug this exists to prevent: `os.environ.get("EMAIL_USE_TLS")` returns a
*string*. `bool("False")` is `True`, because any non-empty string is truthy.
Same story for EMAIL_PORT staying a string instead of an int. Use these
instead of raw os.environ.get() for anything boolean/int-shaped.
"""

import os

_TRUE_VALUES = {"1", "true", "yes", "on"}


def env_str(key, default=None, required=False):
    val = os.environ.get(key, default)
    if required and val in (None, ""):
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return val


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in _TRUE_VALUES


def env_int(key, default=None):
    val = os.environ.get(key)
    if val is None or val == "":
        return default
    return int(val)


class EmailToolkitSettings:
    """
    Reads EMAIL_TOOLKIT_* settings from Django settings.py with fallbacks,
    so each project can override without editing this package.

    Add to settings.py:

        EMAIL_TOOLKIT = {
            "DEFAULT_FROM_EMAIL": env_str("DEFAULT_FROM_EMAIL"),
            "ACTIVATION_SUBJECT": "Confirm your account",
            "PASSWORD_RESET_SUBJECT": "Reset your password",
            "FAIL_SILENTLY": False,     # raise on send failure instead of swallowing it
            "USE_CELERY": False,        # set True once a Celery worker is wired up
        }
    """

    def __init__(self, django_settings):
        cfg = getattr(django_settings, "EMAIL_TOOLKIT", {}) or {}
        self.default_from_email = cfg.get(
            "DEFAULT_FROM_EMAIL", getattr(django_settings, "DEFAULT_FROM_EMAIL", None)
        )
        self.activation_subject = cfg.get("ACTIVATION_SUBJECT", "Confirm your account")
        self.password_reset_subject = cfg.get("PASSWORD_RESET_SUBJECT", "Reset your password")
        self.fail_silently = cfg.get("FAIL_SILENTLY", False)
        self.use_celery = cfg.get("USE_CELERY", False)


def get_toolkit_settings():
    from django.conf import settings as django_settings

    return EmailToolkitSettings(django_settings)
