import json

from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Импорт тегов из JSON'

    def handle(self, *args, **options):
        self.stdout.write('Начало импорта тегов...')
        with open('data/tags.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            tags = [
                Tag(
                    name=item['name'],
                    color=item['color'],
                    slug=item['slug']
                ) for item in data
            ]
            Tag.objects.bulk_create(tags, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS('Теги успешно импортированы!'))