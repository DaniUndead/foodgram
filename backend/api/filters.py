import django_filters
from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Теги'
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
        label='Автор'
    )
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited',
        label='В избранном'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='В корзине'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, recipes, name, value):
        """Фильтрация по избранным рецептам."""
        user = self.request.user
        if value and user.is_authenticated:
            return recipes.filter(favorites__user=user)
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        """Фильтрация по рецептам в корзине."""
        user = self.request.user
        if value and user.is_authenticated:
            return recipes.filter(shopping_carts__user=user)
        return recipes
