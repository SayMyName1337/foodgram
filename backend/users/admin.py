from django.contrib import admin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка отображения пользователей в админской панели."""
    list_display = (
        'first_name',
        'last_name',
        'username',
        'email',
        'avatar',
    )
    search_fields = ('username', 'email')
    empty_value_display = 'Не задано'
    list_per_page = 25
    ordering = ('date_joined', )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Настройка отображения подписок в админской панели."""
    list_display = (
        'user',
        'following',
    )
    search_fields = (
        'user__username',
        'following__username',
    )
    list_per_page = 25
    empty_value_display = 'Пусто'
