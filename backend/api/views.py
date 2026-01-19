from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilter
from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag, User
from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer, UserSerializer)


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


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        """Оптимизированный запрос с предварительной загрузкой."""
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients'
        )
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in (
            'favorite', 'shopping_cart', 'download_shopping_cart'
        ):
            return (IsAuthenticated(),)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _change_recipe_status(self, request, pk, model, serializer_class):
        """Вспомогательный метод для добавления/удаления рецепта (DRY)."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в этот список'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = serializer_class(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=user, recipe=recipe)
        if not obj.exists():
            return Response(
                {'errors': 'Рецепт не найден в этом списке'},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self._change_recipe_status(
            request, pk, Favorite, FavoriteSerializer
        )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в корзину покупок."""
        return self._change_recipe_status(
            request, pk, ShoppingCart, ShoppingCartSerializer
        )

@action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в .txt файле."""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                {'errors': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = Ingredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'name', 'measurement_unit'
        ).annotate(amount=Sum('recipeingredient__amount'))

        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
        )
        for ing in ingredients:
            shopping_list += (
                f'{ing["name"]}: {ing["amount"]} {ing["measurement_unit"]}\n'
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        filename = f'{user.username}_shopping_list.txt'

        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        return response


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        current_password = serializer.validated_data.get('current_password')
        if not current_password:
            current_password = serializer.validated_data.get('old_password')

        if not user.check_password(current_password):
            return Response(
                {'errors': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Вьюсет для работы с подписками."""
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Возвращаем пользователей, на которых подписан текущий юзер.
        Оптимизируем запрос, подгружая рецепты.
        """
        return User.objects.filter(
            following__user=self.request.user
        ).prefetch_related(
            'recipes', 'recipes__tags', 'recipes__ingredients'
        )

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        """Подписка/отписка на автора."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.follower.filter(author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.follower.create(author=author)
            serializer = self.get_serializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = user.follower.filter(author=author)
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
