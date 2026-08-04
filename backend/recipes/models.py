from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from . import constants
from users.models import User


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=constants.TAG_MAX_LENGTH,
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        unique=True,
        max_length=constants.TAG_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        """Строковое представление объекта."""
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=constants.INGREDIENT_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=constants.INGREDIENT_MEASUREMENT_MAX_LENGTH,
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        """Строковое представление объекта."""
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""
    tags = models.ManyToManyField(
        to=Tag,
        verbose_name='Теги',
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=constants.RECIPE_NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(constants.MIN_COOKING_TIME),]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        """Строковое представление объекта."""
        return self.name


class IngredientInRecipe(models.Model):
    """Модель ингредиентов в рецептах."""
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(constants.MIN_INGREDIENT_AMOUNT)],
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        """Строковое представление объекта."""
        return f'{self.recipe} - {self.ingredient} - {self.amount}'


class UserRecipeRelation(models.Model):
    """
    Абстрактная модель.
    Добавляет к модели пользователя и рецепт.
    """
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name="%(app_label)s_%(class)s_relation",
            )
        ]

    def __str__(self):
        """Строковое представление объекта."""
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeRelation):
    """Модель избранного."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(UserRecipeRelation):
    """Модель корзины."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
