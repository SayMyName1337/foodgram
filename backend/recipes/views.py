from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .models import Recipe


def redirect_to_recipe(request, short_link):
    """Редирект с короткой ссылки на страницу рецепта во фронтенде."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return HttpResponseRedirect(
        request.build_absolute_uri(f'/recipes/{recipe.id}/')
    )
