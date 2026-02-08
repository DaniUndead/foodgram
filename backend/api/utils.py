import base64
from datetime import datetime

from django.core.files.base import ContentFile
from rest_framework import serializers


def generate_shopping_list(user, ingredients, recipes):
    """Генерация текстового файла со списком покупок."""

    header = (
        f'Список покупок для: {user.get_full_name()} ({user.username})\n'
        f'Дата составления: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
        f'{"="*30}\n'
    )

    ingredients_lines = [
        f'{index}. {ingredient["name"].capitalize()}: '
        f'{ingredient["amount"]} {ingredient["measurement_unit"]}'
        for index, ingredient in enumerate(ingredients, start=1)
    ]

    recipes_header = f'\n\n{"="*30}\nКупить для рецептов:\n'
    recipes_lines = [
        f'- {recipe.name} (Автор: {recipe.author.username})'
        for recipe in recipes
    ]

    return '\n'.join([
        header,
        *ingredients_lines,
        recipes_header,
        *recipes_lines
    ])


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and not data.startswith('data:image'):
            return None

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
