from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Tag,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Favorite,
    ShoppingCart,
)
from users.models import Subscription, User


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
            bool: True, если текущий пользователь подписан на obj,
                иначе False.
        """
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента внутри рецепта (с количеством)."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для чтения (список/детали)."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, source='ingredientinrecipe_set'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        """
        Проверяет, добавлен ли рецепт в избранное у текущего пользователя.

        Args:
            obj: Экземпляр модели рецепта.

        Returns:
            bool: True, если рецепт в избранном и пользователь
                аутентифицирован, иначе False.
        """
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """
        Проверяет, добавлен ли рецепт в список покупок
        у текущего пользователя.

        Аргументы:
            obj: Экземпляр модели рецепта.

        Возвращает:
            bool: True, если рецепт находится в списке покупок
                пользователя, и он аутентифицирован, иначе False.
        """
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор одного ингредиента при создании/изменении рецепта."""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для создания и редактирования."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_image(self, value):
        """
        Проверяет, что изображение рецепта передано и не пусто.

        Base64ImageField молча возвращает None для пустой строки,
        поэтому явную проверку нужно делать здесь.
        """
        if not value:
            raise serializers.ValidationError(
                'Изображение рецепта не может быть пустым.'
            )
        return value

    def _validate_not_empty_and_unique(self, items, keys, error_prefix):
        """
        Проверяет, что список не пуст и все элементы
        уникальны по заданному ключу.

        Args:
            items: список элементов для проверки.
            keys: список ключей (или сами элементы) для проверки уникальности.
            error_prefix: строка, используемая в сообщении об ошибке
                          (например, 'один ингредиент').

        Returns:
            list: исходный список items, если проверка пройдена.

        Raises:
            serializers.ValidationError:
                если список пуст или элементы не уникальны.
        """
        if not items:
            raise serializers.ValidationError(
                f'Нужно указать хотя бы {error_prefix}.'
            )
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError(
                f'{error_prefix.capitalize()} не должны повторяться.'
            )
        return items

    def validate(self, data):
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'}
            )
        if 'tags' not in self.initial_data:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно.'}
            )
        ingredients = data['ingredients']
        tags = data['tags']
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        self._validate_not_empty_and_unique(
            ingredients, ingredient_ids, 'один ингредиент'
        )
        self._validate_not_empty_and_unique(tags, tags, 'один тег')
        return data

    def create(self, validated_data):
        """
        Создаёт новый рецепт с переданными тегами и ингредиентами.

        Args:
            validated_data:
                проверенные данные рецепта (без 'ingredients' и 'tags').

        Returns:
            Recipe: созданный экземпляр рецепта.
        """
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """
        Обновляет существующий рецепт: теги и ингредиенты перезаписываются.

        Args:
            instance: обновляемый экземпляр рецепта.
            validated_data: проверенные данные для обновления.

        Returns:
            Recipe: обновлённый экземпляр рецепта.
        """
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredientinrecipe_set.all().delete()
        self._set_ingredients(instance, ingredients_data)
        return instance

    def _set_ingredients(self, recipe, ingredients_data):
        """
        Создаёт связи между рецептом и ингредиентами с указанием количества.

        Args:
            recipe: экземпляр рецепта.
            ingredients_data: список словарей с ключами 'id' и 'amount'.
        """
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_data
        )

    def to_representation(self, instance):
        """
        Возвращает представление рецепта в формате для чтения.

        Args:
            instance: экземпляр рецепта.

        Returns:
            dict: сериализованные данные через RecipeReadSerializer.
        """
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого представления рецепта
    (id, название, изображение, время готовки).
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с его рецептами для списка подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """
        Возвращает список рецептов пользователя с учётом параметра
        recipes_limit.

        Args:
            obj: экземпляр пользователя.

        Returns:
            list:
            сериализованные данные рецептов (ограниченные параметром limit,
            если он передан).
        """
        request = self.context.get('request')
        recipes = obj.recipe_set.all()
        limit = request.query_params.get('recipes_limit') if request else None
        if limit and limit.isdigit() and int(limit) > 0:
            recipes = recipes[:int(limit)]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        """
        Возвращает общее количество рецептов пользователя.

        Args:
            obj: экземпляр пользователя.

        Returns:
            int: количество рецептов.
        """
        return obj.recipe_set.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'following')
        validators = []

    def validate(self, data):
        user = data['user']
        following = data['following']
        if user == following:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Subscription.objects.filter(
            user=user, following=following
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора.'
            )
        return data

    def to_representation(self, instance):
        return UserWithRecipesSerializer(
            instance.following, context=self.context
        ).data


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    """Общий сериализатор для избранного и списка покупок."""

    class Meta:
        fields = ('user', 'recipe')
        validators = []

    def validate(self, data):
        if self.Meta.model.objects.filter(**data).exists():
            raise serializers.ValidationError('Рецепт уже добавлен.')
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(FavoriteShoppingCartSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = ShoppingCart
