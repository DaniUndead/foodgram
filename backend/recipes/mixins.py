from django.db.models import Count

from backend.recipes import admin


class RecipeCountMixin:
    """Миксин для добавления подсчета количества рецептов."""

    recipe_relation_name = 'recipes'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count_annotated=Count(self.recipe_relation_name)
        )

    @admin.display(
            description='Количество рецептов',
            ordering='recipes_count_annotated'
        )
    def recipes_count(self, obj):
        return obj.recipes_count_annotated
