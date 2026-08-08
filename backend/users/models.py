from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import F, Q

from . import constants, validators


class User(AbstractUser):
    """Кастомная модель пользователя."""
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=constants.FIRST_NAME_MAX_LENGTH,
        help_text='Введите имя',
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=constants.LAST_NAME_MAX_LENGTH,
        help_text='Введите фамилию',
    )
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=constants.USERNAME_MAX_LENGTH,
        help_text='Введите никнейм',
        unique=True,
        validators=[
            UnicodeUsernameValidator(),
            validators.validate_username_not_forbidden,
        ],
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=constants.EMAIL_MAX_LENGTH,
        help_text='Введите адрес электронной почты',
        unique=True,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        help_text='Загрузите аватар',
        blank=True,
        null=True,
        upload_to='users/avatars/',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following',
    )
    following = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_follow',
            ),
            models.CheckConstraint(
                condition=~Q(user=F('following')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.following.username}'
