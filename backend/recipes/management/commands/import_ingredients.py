from recipes.models import Ingredient

from ._base_import import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт ингредиентов из JSON'
    model = Ingredient
    file_name = 'ingredients.json'
