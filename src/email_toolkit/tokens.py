"""
Token generators for email-based verification links.

`PurposeTokenGenerator` mixes a `purpose` string into the hash, so an
activation token and a password-reset token for the same user are never
interchangeable — a real gap in a lot of copy-pasted Django auth code,
where a single generic token generator is reused for every kind of link.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class PurposeTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, purpose="generic"):
        self.purpose = purpose
        super().__init__()

    def _make_hash_value(self, user, timestamp):
        # is_active is included so an activation link is invalidated the
        # moment the account is activated, and a reset link is invalidated
        # the moment the password actually changes (password is already
        # part of the base class's hash via user.password).
        return (
            f"{user.pk}{user.password}{timestamp}"
            f"{self.purpose}{getattr(user, 'is_active', '')}"
        )


activation_token = PurposeTokenGenerator(purpose="activate")
password_reset_token = PurposeTokenGenerator(purpose="reset")


def build_action_url(user, url_template, token_generator):
    """
    Build a verification URL without depending on this project's urls.py.

    `url_template` is any string with `{uid}` and `{token}` placeholders,
    e.g. "https://app.example.com/activate/{uid}/{token}/" — point it at
    your frontend route or a Django view, whichever this project uses.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    return url_template.format(uid=uid, token=token)


def decode_uid(uidb64):
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode

    return force_str(urlsafe_base64_decode(uidb64))
