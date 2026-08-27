# django-email-toolkit

Reusable Django transactional email helpers — activation links, password
resets, and generic templated sends — it's a dependency instead of something you fork per
project.

## Install (per project)

```bash
pip install git@github.com:Koffi-Cobbin/django-email-toolkit.git
```

Or for local development across sibling projects:

```bash
pip install -e ../django-email-toolkit
```

Add to `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "email_toolkit",
]

EMAIL_TOOLKIT = {
    "DEFAULT_FROM_EMAIL": env("DEFAULT_FROM_EMAIL"),
    "ACTIVATION_SUBJECT": "Confirm your account",
    "PASSWORD_RESET_SUBJECT": "Reset your password",
    "FAIL_SILENTLY": False,   # True = log and return False instead of raising
    "USE_CELERY": False,      # flip on once a worker is wired up
}

# Use conf.env_bool / conf.env_int for the SMTP settings themselves —
# this is the fix for the string-vs-bool bug from the original repo:
from email_toolkit.conf import env_str, env_bool, env_int

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend" if not DEBUG else \
                "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = env_str("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD")
```

## Usage

```python
from email_toolkit.senders import send_activation_email, send_password_reset_email

# in your signup view, after creating the (inactive) user:
send_activation_email(
    user,
    url_template="https://myapp.com/activate/{uid}/{token}/",
)

# in your "forgot password" view:
send_password_reset_email(
    user,
    url_template="https://myapp.com/reset-password/{uid}/{token}/",
)
```

Both raise `email_toolkit.senders.EmailSendError` on failure unless you pass
`fail_silently=True` — decide per-call whether a failed send should 500 the
request or degrade gracefully, instead of an unhandled SMTP exception
bubbling up.

### Verifying a token (activation or reset)

```python
from django.contrib.auth import get_user_model
from email_toolkit.tokens import decode_uid, activation_token  # or password_reset_token

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = decode_uid(uidb64)
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return success_response()
    return invalid_link_response()
```

### Avoiding the user-enumeration bug from the original repo

The original `forget_password` view returned `404` for an unknown email and
`200` for a known one — which lets an attacker check which emails are
registered. Do this instead, regardless of whether the user exists:

```python
def forget_password(request):
    email = request.data.get("email")
    user = User.objects.filter(email=email).first()
    if user:
        send_password_reset_email(user, url_template=RESET_URL_TEMPLATE, fail_silently=True)
    # same response either way — don't leak whether the account exists
    return Response({"detail": "If that email is registered, a reset link has been sent."})
```

## Overriding templates

Drop a template at `your_app/templates/email_toolkit/activation_email.txt`
in your project — Django's template loader resolution order means your
project's copy wins over the package default, no code changes needed.

## Async sending

Set `EMAIL_TOOLKIT["USE_CELERY"] = True` and install the `celery` extra
(`pip install django-email-toolkit[celery]`) once a project has a worker
running. `send_activation_email` / `send_password_reset_email` will
automatically route through a Celery task instead of blocking the request;
until then they send synchronously, so it's safe to leave off in projects
that don't need it yet.

## Running tests

```bash
pip install -e .[dev]
pytest
```
