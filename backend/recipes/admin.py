from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка отображения тегов в админской панели."""
    list_display = (
        'name',
        'slug',
    )
    search_fields = (
        'name',
    )
    empty_value_display = 'Не задано'
    list_per_page = 25


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка отображения ингредиентов в админской панели."""
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
    )
    empty_value_display = 'Не задано'
    list_per_page = 25


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка отображения рецептов в админской панели."""
    list_display = (
        'get_tags',
        'author',
        'get_ingredients',
        'name',
        'image',
        'text',
        'cooking_time',
        'pub_date',
        'favorites_count',
    )
    search_fields = (
        'author__username',
        'name',
    )
    list_filter = (
        'tags',
    )
    empty_value_display = 'Не задано'
    list_per_page = 25

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join(
            ingredient.name for ingredient in obj.ingredients.all()
        )

    @admin.display(description='Добавлено в избранное')
    def favorites_count(self, obj):
        return obj.favorite.count()


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """
    Настройка отображения состава ингредиентов рецепта в админской панели.
    """
    list_display = (
        'recipe',
        'ingredient',
        'amount',
    )
    empty_value_display = 'Не задано'
    list_per_page = 25


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка отображения избранного в админской панели."""
    list_display = (
        'user',
        'recipe',
    )
    empty_value_display = 'Не задано'
    list_per_page = 25


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка отображения корзины в админской панели."""
    list_display = (
        'user',
        'recipe',
    )
    empty_value_display = 'Не задано'
    list_per_page = 25
