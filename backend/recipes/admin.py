from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .mixins import RecipeCountMixin
from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)

admin.site.unregister(Group)


class IngredientInRecipesFilter(admin.SimpleListFilter):
    """Фильтр для поиска ингредиентов, которые используются в рецептах."""

    title = 'Используется в рецептах'
    parameter_name = 'used_in_recipes'

    RECIPE_USAGE_CHOICES = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.RECIPE_USAGE_CHOICES

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipe_ingredients__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipe_ingredients__isnull=True)

        return queryset


class HasRecipesFilter(admin.SimpleListFilter):
    """Фильтр: Есть рецепты."""
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'),)

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    """Фильтр: Есть подписки (пользователь подписан на кого-то)."""
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'),)

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(followers__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(followers__isnull=True)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    """Фильтр: Есть подписчики (на пользователя кто-то подписан)."""
    title = 'Есть подписчики'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'),)

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(authors__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(authors__isnull=True)
        return queryset


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'get_avatar',
        'following_count',
        'subscribers_count',
        *RecipeCountMixin.list_display
    )
    list_filter = (
        'is_staff',
        'is_active',
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Extra'), {'fields': ('avatar',)}),
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description='Подписок')
    def following_count(self, user):
        return user.followers.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.authors.count()

    @mark_safe
    @admin.display(description='Аватар')
    def get_avatar(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" width="50" height="50" '
                f'style="border-radius: 50%;" />'
            )
        return 'Нет фото'


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
    list_filter = ('measurement_unit', IngredientInRecipesFilter)


class RecipeIngredientInline(admin.TabularInline):
    """Позволяет добавлять ингредиенты сразу на странице рецепта."""

    model = RecipeIngredient
    min_num = 1
    extra = 1


class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            output.append(
                f'<a href="{image_url}" target="_blank">'
                f'<img src="{image_url}" style="max-height: 100px; '
                f'margin-right: 20px; vertical-align: middle;" />'
                f'</a>'
            )
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(
            f'<div style="display: flex; align-items: center;">'
            f'{"".join(output)}</div>'
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget},
    }
    list_display = (
        'id', 'name', 'get_cooking_time', 'author',
        'favorites_count', 'get_ingredients', 'get_tags', 'get_image'
    )

    search_fields = (
        'name',
        'author__username',
        'tags__name',
        'ingredients__name'
    )
    list_filter = ('author', 'tags')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Время (мин)', ordering='cooking_time')
    def get_cooking_time(self, obj):
        return obj.cooking_time

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
