import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Загружает ингредиенты из дампа JSON-файла в таблицу Ingredient.

    Файл должен содержать массив объектов с полями
    'name' и 'measurement_unit'. При конфликте уникальности записи
    игнорируются (не перезаписываются).
    """

    help = 'Загрузка дампа из файла JSON в базу данных.'

    def add_arguments(self, parser):
        """
        Добавляет необязательный аргумент командной строки.

        Args:
            parser: Парсер аргументов команды.
        """
        parser.add_argument(
            'json_file',
            nargs='?',
            type=str,
            default=settings.BASE_DIR.parent / 'data' / 'ingredients.json',
            help='Путь до дампа JSON (необязательный).'
        )

    def handle(self, *args, **options):
        """Выполняет загрузку данных из JSON-файла в базу данных."""
        json_file = Path(options['json_file'])

        if not json_file.exists():
            raise CommandError(
                f'Файл не найден по указанному пути: {json_file}'
            )

        self.stdout.write(
            self.style.NOTICE(f'Чтение данных из {json_file}...')
        )

        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

                result = []
                for item in data:
                    result.append(
                        Ingredient(
                            name=item['name'],
                            measurement_unit=item['measurement_unit']
                        )
                    )
                Ingredient.objects.bulk_create(result, ignore_conflicts=True)

            self.stdout.write(
                self.style.SUCCESS('Данные успешно загружены!')
            )

        except json.JSONDecodeError:
            raise CommandError('Неверная структура JSON файла.')
        except KeyError as e:
            raise CommandError(f'Не найдено ожидаемое поле JSON: {e}')
