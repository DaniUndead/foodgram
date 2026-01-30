from recipes.models import Tag

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт тегов из JSON'
    model = Tag
    file_name = 'tags.json'
