from collections import Counter

from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (MIN_AMOUNT, MIN_TIME, Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'color')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для связи рецепт-ингредиент."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = [*DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar']
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        return (
            request
            and request.user.is_authenticated
            and (
                getattr(obj, 'is_subscribed_annotated', False)
                or obj.follower.filter(user=request.user).exists()
            )
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'description',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields

    def _is_exists(self, recipe, model_class):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False

        attr_name = f'is_in_{model_class._meta.model_name}_annotated'

        return (
            getattr(recipe, attr_name, False)
            or model_class.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._is_exists(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._is_exists(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    cooking_time = serializers.IntegerField(min_value=MIN_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'description',
            'ingredients', 'tags', 'cooking_time'
        )

    def _validate_unique(self, items, error_msg):
        """Проверка на дубликаты (DRY)."""
        if not items:
            raise serializers.ValidationError('Список не может быть пустым.')

        ids = [
            item.id if hasattr(item, 'id') else item['ingredient'].id
            for item in items
        ]

        if len(ids) != len(set(ids)):

            duplicates = [
                item for item, count in Counter(ids).items()
                if count > 1
            ]
            raise serializers.ValidationError(
                f'{error_msg} Дубли: {duplicates}'
            )

    def validate_ingredients(self, ingredients):
        return self._validate_unique(
            ingredients, 'Ингредиенты не должны повторяться.'
        )

    def validate_tags(self, tags):
        return self._validate_unique(tags, 'Теги не должны повторяться.')

    def create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags')

        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор для рецептов (общий родитель)."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами (для подписок)."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, 'recipes', 'recipes_count']
        read_only_fields = fields

    def get_recipes(self, user):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = user.recipes.all()

        if limit:
            try:
                recipes = recipes[:int(limit)]
            except (ValueError, TypeError):
                pass

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data
