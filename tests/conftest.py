import django
from django.conf import settings


def pytest_configure():
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-not-for-production",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "email_toolkit",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {},
            }
        ],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        EMAIL_TOOLKIT={"FAIL_SILENTLY": False},
        USE_TZ=True,
    )
    django.setup()
