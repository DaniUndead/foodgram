Конечно. Вот полный, исправленный файл README.md, в который я добавил этапы создания суперпользователя и импорта ингредиентов/тегов, как того требовал ревьюер.

Foodgram — Продуктовый помощник
Сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Функционал
Рецепты: Публикация рецептов с фото, ингредиентами и тегами.

Пользователи: Регистрация, авторизация (токены), смена пароля.

Подписки: Возможность подписываться на любимых авторов.

Избранное: Добавление рецептов в список "любимых".

Список покупок: Добавление рецептов в корзину и скачивание списка ингредиентов (.txt).

Фильтрация: Поиск рецептов по тегам и ингредиентам.

Технологии
Backend: Python, Django, Django REST Framework, Djoser

Frontend: React, JavaScript

Database: PostgreSQL

Infrastructure: Docker, Docker Compose, Nginx, Gunicorn

Установка и запуск (Docker)
Проект упакован в Docker-контейнеры. Для запуска вам понадобится установленный Docker и Docker Compose.

Клонируйте репозиторий

Bash

git clone git@github.com:daniundead/foodgram.git
cd foodgram
Создайте файл .env

В корневой папке создайте файл .env и заполните его по шаблону:

Bash

# PostgreSQL
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY='ваш_секретный_ключ'
DEBUG=False
ALLOWED_HOSTS=127.0.0.1, localhost, ваш_домен

# Переключатель БД (False для продакшена с Postgres)
USE_SQLITE=False
Запустите контейнеры

Bash

docker-compose up -d --build
Выполните миграции и соберите статику

Bash

docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
Загрузите ингредиенты и теги (Если ваши команды управления называются иначе, например import_csv, используйте их)

Bash

docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py load_tags
Создайте суперпользователя

Bash

docker-compose exec backend python manage.py createsuperuser
Установка и запуск (без Docker)
Для локальной разработки или запуска без контейнеризации. Потребуется установленный Python 3.9+.

Клонируйте репозиторий и перейдите в папку backend

Bash

git clone git@github.com:daniundead/foodgram.git
cd foodgram/backend
Создайте и активируйте виртуальное окружение

Bash

python -m venv venv
# для Windows
source venv/Scripts/activate
# для Linux/macOS
source venv/bin/activate
Установите зависимости

Bash

pip install -r requirements.txt
Выполните миграции

Bash

python manage.py migrate
Загрузите начальные данные (ингредиенты и теги)

Bash

python manage.py load_ingredients
python manage.py load_tags
Создайте суперпользователя

Bash

python manage.py createsuperuser
Запустите сервер разработки

Bash

python manage.py runserver
API Документация
После запуска проекта документация к API доступна по адресам:

* [OpenAPI](http://localhost/api/docs/)

Архитектура
Проект состоит из нескольких контейнеров:

db: База данных PostgreSQL.

backend: Приложение Django (Gunicorn).

frontend: React-приложение.

nginx: Веб-сервер, раздающий статику и проксирующий запросы.

CI/CD
В проекте настроен GitHub Actions workflow (foodgram_workflow.yml). При пуше в ветку master:

Запускаются тесты (flake8).

Собираются и пушатся образы на Docker Hub.

Происходит деплой на удаленный сервер.

Отправляется уведомление в Telegram.

Автор: Данис Хуснутдинов

GitHub: DaniUndead

[![Main Foodgram workflow](https://github.com/DaniUndead/foodgram/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/DaniUndead/foodgram/actions/workflows/foodgram_workflow.yml)