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
                created_objects = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(f)),
                    ignore_conflicts=True
                )

            self.stdout.write(self.style.SUCCESS(
                f'Успешно! Файл: {self.file_name}. '
                f'Добавлено записей: {len(created_objects)}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при импорте файла {self.file_name}: {e}'
            ))
