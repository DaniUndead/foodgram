# Foodgram — Продуктовый помощник

Сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Функционал

* **Рецепты:** Публикация рецептов с фото, ингредиентами и тегами.
* **Пользователи:** Регистрация, авторизация (токены), смена пароля.
* **Подписки:** Возможность подписываться на любимых авторов.
* **Избранное:** Добавление рецептов в список "любимых".
* **Список покупок:** Добавление рецептов в корзину и скачивание списка ингредиентов (.txt).
* **Фильтрация:** Поиск рецептов по тегам и ингредиентам.

## Технологии

* **Backend:** Python, Django, Django REST Framework, Djoser
* **Frontend:** React, JavaScript
* **Database:** PostgreSQL
* **Infrastructure:** Docker, Docker Compose, Nginx, Gunicorn

## Установка и запуск (Docker)

Проект упакован в Docker-контейнеры. Для запуска вам понадобится установленный Docker и Docker Compose.

1.  **Клонируйте репозиторий**

    ```bash
    git clone git@github.com:daniundead/foodgram.git
    cd foodgram
    ```

2.  **Создайте файл .env**

    В корневой папке создайте файл `.env` и заполните его по шаблону:

    ```bash
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
    ```

3.  **Запустите контейнеры**

    ```bash
    docker-compose up -d --build
    ```

4.  **Выполните миграции и соберите статику**

    ```bash
    docker-compose exec backend python manage.py migrate
    docker-compose exec backend python manage.py collectstatic --no-input
    ```

## Установка и запуск (без Docker)

Для локальной разработки или запуска без контейнеризации. Потребуется установленный Python 3.9+.

1.  **Клонируйте репозиторий и перейдите в папку backend**
    ```bash
    git clone git@github.com:daniundead/foodgram.git
    cd foodgram/backend
    ```

2.  **Создайте и активируйте виртуальное окружение**
    ```bash
    python -m venv venv
    # для Windows
    source venv/Scripts/activate
    # для Linux/macOS
    source venv/bin/activate
    ```

3.  **Установите зависимости**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Выполните миграции**
    ```bash
    python manage.py migrate
    ```

5.  **Запустите сервер разработки**
    ```bash
    python manage.py runserver
    ```

## API Документация

После запуска проекта документация к API доступна по адресам:

* [Redoc](http://localhost/redoc/)
* [OpenAPI](http://localhost/api/docs/)

## Архитектура

Проект состоит из нескольких контейнеров:

* **db:** База данных PostgreSQL.
* **backend:** Приложение Django (Gunicorn).
* **frontend:** React-приложение.
* **nginx:** Веб-сервер, раздающий статику и проксирующий запросы.

## CI/CD

В проекте настроен GitHub Actions workflow (`foodgram_workflow.yml`). При пуше в ветку master:

1.  Запускаются тесты (flake8).
2.  Собираются и пушатся образы на Docker Hub.
3.  Происходит деплой на удаленный сервер.
4.  Отправляется уведомление в Telegram.
Автор: DaniUndead

GitHub: DaniUndead
