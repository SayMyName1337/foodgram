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
    RecipeMinifiedSerializer,
    UserWithRecipesSerializer,
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

    def get_permissions(self):
        """Требует аутентификации для действия 'me'."""
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        """
        Управление аватаром текущего пользователя.

        PUT /me/avatar/ – загружает или обновляет аватар.
        DELETE /me/avatar/ – удаляет аватар (устанавливает None).

        Args:
            request: Объект HTTP-запроса.

        Returns:
            Response:
                - PUT: сериализованные данные аватара (статус 200 OK).
                - DELETE: пустой ответ (статус 204 No Content).

        Raises:
            ValidationError: если переданные данные невалидны.
            PermissionDenied: если пользователь не аутентифицирован.
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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """
        Управление подпиской на автора.

        Args:
            request: объект HTTP-запроса.
            id: идентификатор автора (из URL).

        Returns:
            Response:
                - POST: сериализованные данные автора с его рецептами
                (статус 201 Created) или ошибка, если подписка невозможна.
                - DELETE: пустой ответ (статус 204 No Content)
                или ошибка, если подписки не существовало.

        Raises:
            Http404: если автор с указанным id не найден.
            ValidationError: если попытка подписаться на самого себя.
            PermissionDenied: если пользователь не аутентифицирован.
        """
        author = get_object_or_404(User, id=id)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Subscription.objects.filter(
                user=user, following=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(user=user, following=author)
            serializer = UserWithRecipesSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = Subscription.objects.filter(
            user=user, following=author
        ).delete()
        if deleted_count == 0:
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

    def _add_or_remove(self, request, pk, model, error_message):
        """
        Вспомогательный метод для добавления или удаления рецепта
        из связанной модели (избранное / список покупок).

        Args:
            request: объект HTTP-запроса.
            pk: идентификатор рецепта.
            model: модель-посредник (Favorite или ShoppingCart).
            error_message: строка для сообщений об ошибках
                           (например, 'избранном' или 'списке покупок').

        Returns:
            Response:
                - POST: сериализованные данные рецепта (статус 201 Created)
                        или ошибка, если рецепт уже добавлен.
                - DELETE: пустой ответ (статус 204 No Content)
                          или ошибка, если рецепта не было в списке.

        Raises:
            Http404: если рецепт с указанным pk не найден.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': f'Рецепт уже в {error_message}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            return Response(
                {'errors': f'Рецепта не было в {error_message}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """
        Добавляет или удаляет рецепт из избранного текущего пользователя.

        POST /recipes/{id}/favorite/ – добавляет рецепт в избранное.
        DELETE /recipes/{id}/favorite/ – удаляет рецепт из избранного.

        Args:
            request: объект HTTP-запроса.
            pk: идентификатор рецепта.

        Returns:
            Response: результат выполнения _add_or_remove.
        """
        return self._add_or_remove(request, pk, Favorite, 'избранном')

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавляет или удаляет рецепт из списка покупок текущего пользователя.

        POST /recipes/{id}/shopping_cart/ – добавляет рецепт в список покупок.
        DELETE /recipes/{id}/shopping_cart/ – удаляет рецепт из списка покупок.

        Args:
            request: объект HTTP-запроса.
            pk: идентификатор рецепта.

        Returns:
            Response: результат выполнения _add_or_remove.
        """
        return self._add_or_remove(
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
        short_link = request.build_absolute_uri(f'/s/{recipe.id}/')
        return Response({'short-link': short_link})
