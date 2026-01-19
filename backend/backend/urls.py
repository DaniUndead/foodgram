from api.views import (IngredientViewSet, RecipeViewSet, SubscriptionViewSet,
                       TagViewSet, UserViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/',
         SubscriptionViewSet.as_view({'get': 'list'}),
         name='subscriptions'),
    path('users/<int:pk>/subscribe/',
         SubscriptionViewSet.as_view(
             {'post': 'subscribe', 'delete': 'subscribe'}
         ),
         name='subscribe'),
]
