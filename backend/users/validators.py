from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username_not_forbidden(value):
    """Валидация на запретные юзернеймы при регистрации."""
    if value.lower() in settings.FORBIDDEN_USERNAMES:
        raise ValidationError(
            f'Имя пользователя "{value}" использовать нельзя.'
        )
