from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from recipes.mixins import RecipeCountMixin

from .mixins import RecipeCountMixin
from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

admin.site.unregister(Group)


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = (
        'id', 'name', 'slug', *RecipeCountMixin.list_display
    )
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
        *RecipeCountMixin.list_display
    )
    search_fields = ('name',)


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

    search_fields = (
        'name',
        'author__username',
        'tags__name',
        'ingredients__name'
    )
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @mark_safe
    @admin.display(description='Продукты')
    def get_ingredients(self, recipe):
        return '<br>'.join(
            f'{i.ingredient.name} — {i.amount} {i.ingredient.measurement_unit}'
            for i in recipe.recipe_ingredients.all()
        )

    @mark_safe
    @admin.display(description='Теги')
    def get_tags(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @mark_safe
    @admin.display(description='Картинка')
    def get_image(self, recipe):
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="80" height="60">'
        return ''


class BaseRecipeUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(BaseRecipeUserAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseRecipeUserAdmin):
    pass


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'following_count',
        'followers_count',
        *RecipeCountMixin.list_display
    )
    list_filter = ('is_staff', 'is_active')

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description='Подписок')
    def following_count(self, user):
        return user.followers.count()

