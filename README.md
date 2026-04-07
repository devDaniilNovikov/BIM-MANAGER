# BIM Document Manager

Автоматизированная система управления проектной информацией на основе BIM/IFC моделей. Позволяет загружать IFC-файлы, просматривать 3D-модель, анализировать структуру здания, проводить проверки качества данных и экспортировать отчёты.

## Стек технологий

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, ifcopenshell
- **Frontend:** React, TypeScript, Vite, Material UI, Three.js, web-ifc, Recharts
- **Инфраструктура:** Docker, Docker Compose, nginx

## Структура проекта

```
backend/     — REST API (FastAPI), парсинг IFC, проверки качества, экспорт отчётов
frontend/    — SPA на React (Vite + TypeScript)
```

## Запуск через Docker Compose (рекомендуется)

Одна команда поднимает всё: базу данных, API-сервер и фронтенд.

### 1. Клонировать репозиторий

```bash
git clone https://github.com/devDaniilNovikov/BIM-MANAGER.git
cd PyCharmMiscProject
```

### 2. Запустить контейнеры

```bash
docker compose up -d --build
```

После запуска:
- **Фронтенд** — http://localhost:3000
- **API** — http://localhost:8000
- **Swagger (в режиме DEBUG)** — http://localhost:8000/api/docs

Остановка:
```bash
docker compose down
```

## Локальный запуск (для разработки)

### 1. База данных

Запустите PostgreSQL (через Docker или локально). Создайте базу:

```sql
CREATE USER bim WITH PASSWORD 'bimpass';
CREATE DATABASE bim_system OWNER bim;
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создайте файл `.env` в папке `backend/`:
```
DATABASE_URL=postgresql+asyncpg://bim:bimpass@localhost:5432/bim_system
DEBUG=true
```

Запуск:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Таблицы создаются автоматически при старте приложения.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Фронтенд будет доступен на http://localhost:5173. API-запросы проксируются на `http://localhost:8000`.

## Основные модули

| Модуль | Описание |
|--------|----------|
| Загрузка IFC | Загрузка и валидация IFC-файлов |
| 3D-просмотр | Визуализация модели (Three.js + web-ifc) |
| Пространственная структура | Дерево: здание > этаж > помещение |
| Элементы | Таблица элементов с фильтрацией и поиском |
| Замечания | Создание, редактирование, фильтрация замечаний |
| Контроль качества | Встроенные + пользовательские правила проверки |
| Аналитика | Дашборд со статистикой, графиками, полнотой данных |
| Экспорт | Отчёты в форматах XLSX, CSV, PDF |

## Полезные команды

Просмотр логов:
```bash
docker compose logs backend -f
docker compose logs frontend -f
```

Запуск тестов:
```bash
cd backend
source .venv/bin/activate
pytest
```
