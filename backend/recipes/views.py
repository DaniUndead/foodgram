from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


def recipe_short_link_view(request, pk):
    """Контроллер для перенаправления по короткой ссылке."""
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{recipe.pk}/')
