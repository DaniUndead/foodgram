import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON'

    def handle(self, *args, **options):
        self.stdout.write('Начало импорта ингредиентов...')
        with open('data/ingredients.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            ingredients = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                ) for item in data
            ]
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(
            'Ингредиенты успешно импортированы!'
        ))
