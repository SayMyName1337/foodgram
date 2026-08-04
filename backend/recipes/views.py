from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def redirect_to_recipe(request, pk):
    """Редирект с короткой ссылки на страницу рецепта во фронтенде."""
    get_object_or_404(Recipe, id=pk)
    return redirect(f'/recipes/{pk}/')
