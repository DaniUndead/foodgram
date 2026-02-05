from django.http import Http404
from django.shortcuts import redirect
from recipes.models import Recipe


def recipe_short_link_view(request, pk):
    """Контроллер для перенаправления по короткой ссылке."""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепт с id={pk} не найден.')

    return redirect('recipe-detail', pk=pk)
