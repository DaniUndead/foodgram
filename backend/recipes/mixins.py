from django.contrib import admin
from django.db.models import Count


class RecipeCountMixin:
    """Миксин для добавления подсчета количества рецептов."""

    recipe_count_list_display = ('recipes_count',)

    def get_queryset(self, request):
        """Аннотируем QuerySet количеством связанных рецептов."""
        return super().get_queryset(request).annotate(
            recipes_count_annotated=Count(self.recipe_relation_name)
        )

    @admin.display(
        description='Рецептов',
        ordering='recipes_count_annotated'
    )
    def recipes_count(self, obj):
        return getattr(obj, 'recipes_count_annotated', 0)
