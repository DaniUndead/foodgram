import base64

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


MAX_LENGTH_NAME = 10
MAX_LENGTH_SLUG = 10
MAX_LENGTH_UNIT = 10
MIN_AMOUNT = 1
MIN_TIME = 1


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_NAME,
        unique=True,
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=MAX_LENGTH_SLUG,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_NAME,
        unique=True,
    )
    unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH_UNIT,

    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_NAME,
    )
    description = models.TextField(
        'Описание'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
        null=True,
        default=None
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (минуты)',
        validators=[
            MinValueValidator(
                MIN_TIME,
                message=f'Минимум {MIN_TIME} минута!'
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def get_short_link(self):
        byte_id = str(self.id).encode('ascii')
        return base64.urlsafe_b64encode(byte_id).decode(
            'ascii'
        ).replace('=', '')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Промежуточная модель для связи Рецепт-Ингредиент
    с указанием количества.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f'Минимум {MIN_AMOUNT}!'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name}: {self.ingredient.name} - {self.amount}'


class UserRecipeRelation(models.Model):
    """
    Базовая (абстрактная) модель для связей Пользователь <-> Рецепт.
    Используется для Избранного и Корзины.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class Favorite(UserRecipeRelation):
    """Модель для избранных рецептов."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(UserRecipeRelation):
    """Модель для корзины покупок."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'


class Follow(models.Model):
    """Модель для подписок на авторов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,

        related_name='followers',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
