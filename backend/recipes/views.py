from django.http import Http404, HttpResponseRedirect
from recipes.models import Recipe


def recipe_short_link_view(request, pk):
    """Контроллер для перенаправления по короткой ссылке."""

    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'Рецепт с id={pk} не найден.')

    return HttpResponseRedirect(f'/recipes/{pk}/')
