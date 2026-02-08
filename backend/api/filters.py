import django_filters
from django_filters.rest_framework import FilterSet
from recipes.models import Ingredient


class IngredientFilter(FilterSet):
    name = django_filters.filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
