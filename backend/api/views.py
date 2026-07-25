import djoser.views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User
from recipes.models import Tag, Ingredient
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    UserSerializer,
    AvatarSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения конкретного тега и списка тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения конкретного ингредиента и списка ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class UserViewSet(djoser.views.UserViewSet):
    """Вьюсет для получения пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        """
        Обрабатывает PUT и DELETE запросы для управления аватаром пользователя.

        Args:
            request: Объект HTTP-запроса.

        Returns:
            Response:
                - Для PUT: сериализованные данные
                обновлённого аватара и статус 200 OK.
                - Для DELETE: пустой ответ и статус 204 No Content.

        Raises:
            ValidationError: Если переданные данные
            не прошли валидацию сериализатора.
            PermissionDenied: Если пользователь не аутентифицирован.
        """
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
