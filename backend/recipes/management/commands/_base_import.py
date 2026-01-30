import json

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    """Базовая команда для импорта данных из JSON."""
    model = None
    file_name = None

    def handle(self, *args, **options):
        self.stdout.write(f'Начало импорта из {self.file_name}...')
        try:
            with open(f'data/{self.file_name}', 'r', encoding='utf-8') as f:
                data = json.load(f)

                initial_count = self.model.objects.count()

                objects = [self.model(**item) for item in data]
                self.model.objects.bulk_create(objects, ignore_conflicts=True)

                created_count = self.model.objects.count() - initial_count

                self.stdout.write(self.style.SUCCESS(
                    f'Успешно! Файл: {self.file_name}. '
                    f'Добавлено новых записей: {created_count}'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при импорте: {e}'))
