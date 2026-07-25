from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes.models import (
    Tag,
    Ingredient,
)
from users.models import Subscription, User
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тега."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиента."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class UserSerializer(BaseUserSerializer):
    """Сериализатор для модели пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = BaseUserSerializer.Meta.model
        fields = (
            'id',
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """
        Определяет, подписан ли текущий пользователь на данного.

        Args:
            obj: экземпляр модели пользователя,
                для которого проверяется подписка.
        Returns:
            bool: True, если текущий пользователь подписан на obj, иначе False.
        """
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user,
            following=obj
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
