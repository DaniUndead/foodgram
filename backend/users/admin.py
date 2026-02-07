from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from recipes.mixins import RecipeCountMixin

from .models import User

admin.site.unregister(Group)

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
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    @admin.display(description='Подписок')
    def following_count(self, obj):
        return obj.followers.count()

    @admin.display(description='Подписчиков')
    def followers_count(self, obj):
        return obj.autors.count()
