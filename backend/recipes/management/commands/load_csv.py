import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Загружает ингредиенты из дампа CSV-файла в таблицу Ingredient.

    Команда принимает путь к CSV-файлу с ингредиентами и загружает записи
    в базу данных, игнорируя дубликаты.
    """

    help = 'Загрузка дампа из файла CSV в базу данных.'

    def add_arguments(self, parser):
        """
        Добавляет необязательный аргумент командной строки.

        Args:
            parser: Парсер аргументов команды.
        """
        parser.add_argument(
            'csv_file',
            nargs='?',
            type=str,
            default=settings.BASE_DIR.parent / 'data' / 'ingredients.csv',
            help='Путь до дампа CSV (необязательный).'
        )

    def handle(self, *args, **options):
        """Выполняет загрузку данных из CSV-файла в базу данных."""
        csv_file = Path(options['csv_file'])

        if not csv_file.exists():
            raise CommandError(
                f'Файл не найден по указанному пути: {csv_file}'
            )

        try:
            with open(csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(
                    file,
                    fieldnames=['name', 'measurement_unit']
                )

                result = []
                for row in reader:
                    result.append(
                        Ingredient(
                            name=row['name'],
                            measurement_unit=row['measurement_unit']
                        )
                    )
                Ingredient.objects.bulk_create(result, ignore_conflicts=True)

                self.stdout.write(
                    self.style.SUCCESS('Данные успешно загружены!')
                )

        except csv.Error:
            raise CommandError('Неверная структура файла CSV.')
        except KeyError as e:
            raise CommandError(f'Не найдено ожидаемое поле CSV: {e}')
