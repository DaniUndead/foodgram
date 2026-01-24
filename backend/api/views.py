from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Follow, Ingredient, Recipe, ShoppingCart,
                            Tag, User)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import RecipeFilter
from .pagination import PageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeShortSerializer, RecipeWriteSerializer,
                          TagSerializer, UserWithRecipesSerializer)
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
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class UserViewSet(DjoserUserViewSet):
    """
    Вьюсет для пользователей. 
    Наследуется от Djoser, поэтому методы me, set_password и create уже есть.
    Добавляем только работу с подписками.
    """
    pagination_class = PageNumberPagination

    @action(
            detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
        )
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        user = request.user
        queryset = User.objects.filter(following__user=user).prefetch_related(
            'recipes'
        )
        pages = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
            detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, IsAuthenticatedOrReadOnly]
        )
    def subscribe(self, request, id=None):
        """Подписка/отписка."""
        user = request.user

        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            obj, created = Follow.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'errors': f'Вы уже подписаны на {author.username}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                UserWithRecipesSerializer(
                    author, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        get_object_or_404(Follow, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_to_list(self, model, user, pk):
        """Вспомогательный метод добавления в избранное/корзину."""
        recipe = get_object_or_404(Recipe, pk=pk)
        obj, created = model.objects.get_or_create(user=user, recipe=recipe)

        if not created:
            return Response(
                {'errors': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def _delete_from_list(self, model, user, pk):
        """Вспомогательный метод удаления."""
        recipe = get_object_or_404(Recipe, pk=pk)
        get_object_or_404(model, user=user, recipe=recipe).delete()
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

        if not ingredients:
            pass

        recipes = Recipe.objects.filter(shopping_cart__user=user)

        content = generate_shopping_list(user, ingredients, recipes)

        response = FileResponse(
            content,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
