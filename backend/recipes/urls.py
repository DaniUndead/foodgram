from django.urls import path

from .views import recipe_short_link_view

urlpatterns = [
    path('s/<int:pk>/', recipe_short_link_view, name='short-link-redirect'),
]
