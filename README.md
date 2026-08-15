# Фудграм

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1.1-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.15.2-A30000?logo=django&logoColor=white)
![Djoser](https://img.shields.io/badge/Djoser-2.3.3-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-4169E1?logo=postgresql&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-26.0.0-499848?logo=gunicorn&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-1.25.4-009639?logo=nginx&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![React](https://img.shields.io/badge/React-17.0.1-61DAFB?logo=react&logoColor=black)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)

Сайт для публикации рецептов. Пользователи выкладывают свои рецепты, добавляют чужие в избранное, подписываются на понравившихся авторов и собирают список покупок - на странице рецепта нажимаешь «Добавить в покупки», а потом скачиваешь один файл со списком нужных продуктов сразу под все выбранные блюда, с суммированием одинаковых ингредиентов.

Дипломный проект курса Python-разработчик в Яндекс Практикуме (спринт 18). Фронтенд (React) выдан в готовом виде, весь backend - REST API на Django - написан с нуля.

- Сайт: http://158.160.171.191:9090/
- Документация API: http://158.160.171.191:9090/api/docs/
- Админка: http://158.160.171.191:9090/admin/

## Что умеет

- Регистрация и авторизация по токену, аватар пользователя
- CRUD рецептов с картинками (загрузка в base64), тегами и ингредиентами с указанием количества
- Избранное и список покупок, скачивание списка одним txt-файлом
- Подписки на авторов
- Поиск ингредиентов по названию, фильтрация рецептов по тегам/автору/избранному
- Короткие ссылки на рецепты
- Админка с поиском и фильтрами по всем моделям

## Стек технологий

- **Backend**: Python 3.12, Django 5.1, Django REST Framework, Djoser (токен-авторизация), django-filter, drf-extra-fields (base64-картинки)
- **База данных**: PostgreSQL 13 (в проде), SQLite - для локальной разработки без Docker
- **Frontend**: React 17 (готовый проект, интеграция через REST API)
- **Инфраструктура**: Docker, Docker Compose, Nginx, Gunicorn
- **CI/CD**: GitHub Actions - тесты (flake8), сборка образов, публикация в Docker Hub, деплой на сервер по SSH

## Как развернуть проект

### Локально в Docker

Понадобится Docker.

1. Склонировать репозиторий.
2. В `backend/` создать `.env` по образцу `backend/.env.example` (значения `POSTGRES_*` и `SECRET_KEY` - любые свои, `DB_ENGINE` можно оставить `sqlite` для быстрого локального запуска или указать `postgresql`, если нужна база как в проде).
3. Из папки `infra/`:
   ```bash
   docker compose up --build
   ```
4. Сайт откроется на `http://localhost/`, документация API - на `http://localhost/api/docs/`, админка - на `http://localhost/admin/`.

При старте backend-контейнера автоматически применяются миграции, собирается статика и загружается справочник ингредиентов (см. раздел ниже) - вручную ничего запускать не нужно.

### Backend без Docker

```bash
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py runserver
```

По умолчанию используется SQLite. Чтобы подключить PostgreSQL, пропишите в `.env` `DB_ENGINE=postgresql` и параметры подключения (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`).

### Деплой на сервер

Пуш в `main` запускает пайплайн в GitHub Actions: прогон flake8, сборка и публикация образов backend и frontend в Docker Hub, затем деплой на сервер по SSH - копирование `docker-compose.production.yml` и конфига nginx, обновление и пересоздание контейнеров. Для собственного сервера нужно завести в настройках репозитория (`Settings → Secrets and variables → Actions`) секреты `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `HOST`, `USER`, `SSH_KEY`, а на самом сервере - файл `.env` рядом с `docker-compose.production.yml` (тот же набор переменных, что в `backend/.env.example`, плюс `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` со своим доменом/IP).

## Как наполнить базу данными

Справочник ингредиентов (`data/ingredients.json`) загружается автоматически при каждом старте backend-контейнера - командой `manage.py load_json`, повторный запуск не создаёт дублей. Загрузить его вручную или из другого файла (в том числе CSV) можно так:

```bash
python manage.py load_json path/to/ingredients.json
python manage.py load_csv path/to/ingredients.csv
```

В Docker - через `exec` в контейнер backend:

```bash
docker compose exec backend python manage.py load_json /app/data/ingredients.json
```

Теги под фикстуру не заведены - их нужно создать через админку (`/admin/`) или Django shell: у тега есть название и уникальный slug.

## Документация API

Спецификация в формате OpenAPI (Redoc) поднимается вместе с проектом и доступна по адресу `/api/docs/` - локально это `http://localhost/api/docs/`, на сервере `http://158.160.171.191:9090/api/docs/`. Исходники - `docs/openapi-schema.yml` и `docs/redoc.html`.

## Примеры запросов

**Регистрация пользователя**

```bash
curl -X POST http://localhost/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vpupkin@yandex.ru",
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Иванов",
    "password": "Qwerty123!"
  }'
```

```json
{
  "email": "vpupkin@yandex.ru",
  "id": 1,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов"
}
```

**Получение токена**

```bash
curl -X POST http://localhost/api/auth/token/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "vpupkin@yandex.ru", "password": "Qwerty123!"}'
```

```json
{"auth_token": "9a3b7c1e6f5d4a8b0c2e1f3a4b5c6d7e8f9a0b1c"}
```

**Список рецептов**

```bash
curl http://localhost/api/recipes/
```

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "tags": [{"id": 1, "name": "Завтрак", "slug": "breakfast"}],
      "author": {
        "id": 1,
        "username": "vasya.pupkin",
        "first_name": "Вася",
        "last_name": "Иванов",
        "email": "vpupkin@yandex.ru",
        "avatar": null,
        "is_subscribed": false
      },
      "ingredients": [
        {"id": 1123, "name": "Картофель отварной", "measurement_unit": "г", "amount": 200}
      ],
      "is_favorited": false,
      "is_in_shopping_cart": false,
      "name": "Картофельное пюре",
      "image": "http://localhost/media/recipes/images/image.png",
      "text": "Отварить картофель, размять с молоком и маслом.",
      "cooking_time": 30
    }
  ]
}
```

Полный список эндпоинтов, параметров и форматов ошибок - в документации API (см. раздел выше).

## Автор

Григорий Швец, [github.com/SayMyName1337](https://github.com/SayMyName1337)
