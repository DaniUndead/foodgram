from datetime import datetime


def generate_shopping_list(user, ingredients, recipes):
    """Генерация текстового файла со списком покупок."""

    header = (
        f'Список покупок для: {user.get_full_name()} ({user.username})\n'
        f'Дата составления: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
        f'{"="*30}\n'
    )

    ingredients_lines = []
    for idx, ing in enumerate(ingredients, 1):
        name = ing['name'].capitalize()

        line = f'{idx}. {name}: {ing["amount"]} {ing["measurement_unit"]}'
        ingredients_lines.append(line)

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
