from django.contrib import admin
from django.db.models import Count


class RecipeCountMixin:
    """Миксин для добавления подсчета количества рецептов."""

    list_display = ('recipes_count',)

    def get_queryset(self, request):
        """Аннотируем QuerySet количеством связанных рецептов."""
        return super().get_queryset(request).annotate(
            recipes_count_annotated=Count('recipes')
        )

    @admin.display(
        description='Рецептов',
        ordering='recipes_count_annotated'
    )
    def recipes_count(self, obj):
        return obj.recipes_count_annotated
