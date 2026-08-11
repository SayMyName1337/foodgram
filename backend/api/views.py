import djoser.views
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from users.models import User, Subscription
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientInRecipe,
)
from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter, IngredientFilter
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    UserSerializer,
    AvatarSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    UserWithRecipesSerializer,
    SubscriptionSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения списка тегов и отдельного тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для получения списка ингредиентов и отдельного ингредиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(djoser.views.UserViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        ["get"],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """Возвращает профиль текущего пользователя. Доступно только GET."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        """Загружает или обновляет аватар текущего пользователя."""
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя."""
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """Подписывает текущего пользователя на автора."""
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'following': author.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        """Отписывает текущего пользователя от автора."""
        author = get_object_or_404(User, id=id)
        deleted_count, _ = Subscription.objects.filter(
            user=request.user, following=author
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Вы не были подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь.

        Args:
            request: объект HTTP-запроса.

        Returns:
            Response: пагинированный список сериализованных данных авторов
                    через UserWithRecipesSerializer.

        Raises:
            PermissionDenied: если пользователь не аутентифицирован.
        """
        authors = User.objects.filter(followers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """
        Возвращает оптимизированный queryset для рецептов.

        Returns:
            QuerySet: оптимизированный queryset рецептов.
        """
        return Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredientinrecipe_set__ingredient'
        )

    def get_serializer_class(self):
        """
        Возвращает класс сериализатора в зависимости от действия.

        Returns:
            serializers.Serializer:
                RecipeReadSerializer для list/retrieve,
                RecipeWriteSerializer для остальных действий.
        """
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def _add_relation(self, request, pk, serializer_class):
        """
        Создаёт связь рецепта с текущим пользователем
        (избранное / список покупок) через переданный сериализатор.

        Args:
            request: объект HTTP-запроса.
            pk: идентификатор рецепта.
            serializer_class: класс сериализатора (Favorite/ShoppingCart).

        Returns:
            Response: сериализованные данные рецепта, статус 201 Created.

        Raises:
            Http404: если рецепт с указанным pk не найден.
            ValidationError: если рецепт уже добавлен.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_relation(self, request, pk, model, error_message):
        """
        Удаляет связь рецепта с текущим пользователем
        (избранное / список покупок).

        Args:
            request: объект HTTP-запроса.
            pk: идентификатор рецепта.
            model: модель-посредник (Favorite или ShoppingCart).
            error_message: строка для сообщений об ошибках
                           (например, 'избранном' или 'списке покупок').

        Returns:
            Response: пустой ответ (статус 204 No Content)
                      или ошибка, если рецепта не было в списке.

        Raises:
            Http404: если рецепт с указанным pk не найден.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': f'Рецепта не было в {error_message}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное текущего пользователя."""
        return self._add_relation(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного текущего пользователя."""
        return self._remove_relation(request, pk, Favorite, 'избранном')

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок текущего пользователя."""
        return self._add_relation(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок текущего пользователя."""
        return self._remove_relation(
            request, pk, ShoppingCart, 'списке покупок'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """
        Генерирует и скачивает текстовый файл со списком покупок.

        Returns:
            HttpResponse: текстовый файл с именем "shopping_list.txt"
                          и заголовком Content-Disposition для скачивания.
        """
        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__shoppingcart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        lines = [
            f'{item["ingredient__name"]} '
            f'({item["ingredient__measurement_unit"]}) — '
            f'{item["total_amount"]}'
            for item in ingredients
        ]
        content = 'Список покупок:\n' + '\n'.join(lines)

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.

        Args:
            request: объект HTTP-запроса.
            pk: идентификатор рецепта.

        Returns:
            Response:
                JSON с ключом "short-link", содержащим полный URL
                вида /s/{id}/ (может быть использован для перенаправления).

        Raises:
            Http404: если рецепт не найден.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = request.build_absolute_uri(
            f'/s/{recipe.short_link}/'
        )
        return Response({'short-link': short_link})
