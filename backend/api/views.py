from django.db.models import Sum
from django.forms import ValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Follow, Ingredient, Recipe, ShoppingCart,
                            Tag, User)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import NewPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeShortSerializer, RecipeWriteSerializer,
                          TagSerializer, UserSerializer,
                          UserWithRecipesSerializer)
from .utils import generate_shopping_list


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):
    """
    Вьюсет для пользователей.
    Наследуется от Djoser, поэтому методы me, set_password и create уже есть.
    Добавляем только работу с подписками.
    """
    pagination_class = NewPageNumberPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        return self.get_paginated_response(
            UserWithRecipesSerializer(
                self.paginate_queryset(
                    User.objects.filter(following__user=request.user)
                    .prefetch_related('recipes')
                ),
                many=True,
                context={'request': request}
            ).data
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка."""
        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(Follow, user=user, author_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = get_object_or_404(User, pk=id)

        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя')

        _, created = Follow.objects.get_or_create(user=user, author=author)

        if not created:
            raise ValidationError(
                f'Вы уже подписаны на {author.username}'
            )

        return Response(
            UserWithRecipesSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(
            detail=False,
            methods=['put', 'delete'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated]
        )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    pagination_class = NewPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_to_list(self, model, user, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(user=user, recipe=recipe)

        if not created:
            model_name = model._meta.verbose_name.capitalize()
            raise ValidationError(
                f'Рецепт "{recipe.name}" уже добавлен в {model_name}'
            )

        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def _delete_from_list(self, model, user, pk):
        get_object_or_404(model, user=user, recipe_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self._add_to_list(Favorite, request.user, pk)
        return self._delete_from_list(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self._add_to_list(ShoppingCart, request.user, pk)
        return self._delete_from_list(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
    )
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = Ingredient.objects.filter(
            recipe_ingredients__recipe__shopping_cart__user=user
        ).values(
            'name', 'measurement_unit'
        ).annotate(
            amount=Sum('recipe_ingredients__amount')
        ).order_by('name')

        recipes = Recipe.objects.filter(shopping_cart__user=user)

        content = generate_shopping_list(user, ingredients, recipes)

        return FileResponse(
            content,
            content_type='text/plain',
            as_attachment=True,
            filename='shopping_list.txt'
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError(
                f'Рецепт с идентификатором id={pk} не найден. '
            )
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse('short-link-redirect', args=[pk])
            )},
        )
