# BIM Document Manager

Система для управления BIM-документами (IFC файлами), анализа структуры, проверок качества (Quality Control) по кастомным правилам и поиска аномалий.

## Структура проекта
- `backend/` — REST API на FastAPI, фоновые задачи Celery (обработка IFC), PostgreSQL, Redis.
- `frontend/` — Пользовательский интерфейс на React (Vite, TypeScript).

## Требования
- **Docker** и **Docker Compose**
- **Node.js** (для локального запуска фронтенда)

## Как запустить проект (через Docker)

Вся серверная часть, база данных и брокер сообщений запакованы в `docker-compose.yml` и могут быть запущены одной командой.

### 1. Запуск Backend-части (API, БД, Worker, Redis)
Перейдите в папку `backend` и запустите контейнеры:

```bash
cd backend
docker compose up -d --build
```

**Что произойдет:**
- Поднимется база данных **PostgreSQL** (порт `5432`)
- Поднимется **Redis** для фоновых задач (порт `6379`)
- Запустятся миграции базы данных (Alembic)
- Поднимется основное **FastAPI** приложение (доступно на `http://localhost:8000`)
- Поднимется фоновый воркер **Celery** для обработки IFC-файлов.

Вы можете проверить документацию API (Swagger), открыв в браузере:
👉 **http://localhost:8000/docs**

### 2. Запуск Frontend-части
Перейдите в папку `frontend`, установите зависимости и запустите локальный сервер разработки:

```bash
cd ../frontend
npm install
npm run dev
```

После этого фронтенд будет доступен по адресу, который выдаст консоль (обычно `http://localhost:5173`).

---

## Полезные команды

**Остановка всех контейнеров бэкенда:**
```bash
cd backend
docker compose down
```

**Просмотр логов API или Worker'а:**
```bash
docker logs backend-api-1 -f
docker logs backend-worker-1 -f
```

**Запуск тестов:**
Для запуска локальных тестов бэкенда:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

