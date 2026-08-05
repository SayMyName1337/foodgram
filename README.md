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

Сайт для публикации рецептов. Пользователи выкладывают свои рецепты, добавляют чужие в избранное, подписываются на понравившихся авторов и собирают список покупок — на странице рецепта нажимаешь «Добавить в покупки», а потом скачиваешь один файл со списком нужных продуктов сразу под все выбранные блюда, с суммированием одинаковых ингредиентов.

Дипломный проект курса Python-разработчик в Яндекс Практикуме (спринт 18). Фронтенд (React) выдан в готовом виде, весь backend — REST API на Django — написан с нуля.

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

## Деплой

Пуш в `main` запускает пайплайн в GitHub Actions: прогон flake8, сборка и публикация образов backend и frontend в Docker Hub, затем деплой на сервер по SSH — обновление docker-compose и конфига nginx, пересоздание контейнеров. Миграции, сборка статики и загрузка справочника ингредиентов происходят автоматически при старте backend-контейнера.

## Как запустить локально

Понадобится Docker.

1. Склонировать репозиторий.
2. В `backend/` создать `.env` по образцу `backend/.env.example`.
3. Из папки `infra/`:
   ```bash
   docker compose up --build
   ```
4. Сайт откроется на `http://localhost/`, документация API — на `http://localhost/api/docs/`.

Для разработки backend без Docker: `python -m venv venv`, `pip install -r backend/requirements.txt`, дальше обычные `manage.py migrate` и `manage.py runserver`. По умолчанию используется SQLite; чтобы подключить PostgreSQL, пропишите в `.env` `DB_ENGINE=postgresql` и параметры подключения.

## Автор

Григорий Швец, [github.com/SayMyName1337](https://github.com/SayMyName1337)
