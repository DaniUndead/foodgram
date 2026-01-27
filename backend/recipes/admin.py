from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

admin.site.unregister(Group)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')
    list_filter = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count('recipes')
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipes_count=Count('ingredients_in_recipe')
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes_count


class RecipeIngredientInline(admin.TabularInline):
    """Позволяет добавлять ингредиенты сразу на странице рецепта."""
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author', 
        'favorites_count', 'get_ingredients', 'get_tags', 'get_image'
    )
    list_filter = ('author', 'name', 'tags')

    search_fields = (
        'name',
        'author__username',
        'tags__name',
        'ingredients__name'
    )
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()

    @mark_safe
    @admin.display(description='Продукты')
    def get_ingredients(self, obj):
        return '<br>'.join([f'{i.name}' for i in obj.ingredients.all()])

    @mark_safe
    @admin.display(description='Теги')
    def get_tags(self, obj):
        return '<br>'.join([f'{t.name}' for t in obj.tags.all()])

    @mark_safe
    @admin.display(description='Картинка')
    def get_image(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="80" height="60">'
        return "Нет фото"


class BaseRecipeUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'created_at')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(BaseRecipeUserAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseRecipeUserAdmin):
    pass


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
