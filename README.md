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

## Запуск через IDE на Windows

Удобный способ: запустить backend и frontend прямо из редактора, без ручных команд в терминале. Браузер открывается по фиксированным URL.

### Вариант А — VS Code (бесплатно, рекомендуется)

**Необходимые расширения** (установить через `Ctrl+Shift+X`):
- `Python` (Microsoft)
- `Pylance`
- `ESLint`

**Подготовка** (выполняется один раз в терминале VS Code — `Ctrl+`` `):
```powershell
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Создайте backend\.env с содержимым:
# DATABASE_URL=postgresql+asyncpg://bim:bimpass@localhost:5432/bim_system
# DEBUG=true

# Frontend
cd ..\frontend
npm install
```

**Запуск backend (с дебаггером):**

1. Откройте проект в VS Code: `File → Open Folder → папка BIM-MANAGER`
2. Нажмите `F5` или перейдите в панель **Run and Debug** (`Ctrl+Shift+D`)
3. В выпадающем списке выберите **`Backend: FastAPI (uvicorn)`** → нажмите ▶

Backend стартует, в панели **Debug Console** появятся логи.
Доступен по адресу: **http://localhost:8000**

> Файл конфигурации уже готов: `.vscode/launch.json`

**Запуск frontend:**

1. Откройте новый терминал: `Terminal → New Terminal` (`Ctrl+Shift+`` `)
2. Выполните:
```powershell
cd frontend
npm run dev
```

Или через меню: `Terminal → Run Task → Frontend: npm dev`

Frontend доступен по адресу: **http://localhost:5173**

---

### Вариант Б — PyCharm Professional

**Настройка интерпретатора:**

1. `File → Settings → Project → Python Interpreter`
2. Нажмите шестерёнку → `Add Interpreter → Add Local Interpreter`
3. Выберите `Existing` → укажите путь `backend\.venv\Scripts\python.exe`

**Run-конфигурация для backend:**

1. В правом верхнем углу нажмите `Edit Configurations...` (или `Run → Edit Configurations`)
2. Нажмите `+` → выберите **`FastAPI`** (или **`Python`**)
3. Заполните поля:

| Поле | Значение |
|---|---|
| Name | `Backend: FastAPI` |
| Script / Module | `uvicorn` |
| Parameters | `app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Working directory | `C:\...\BIM-MANAGER\backend` |
| EnvFile | `backend\.env` |

4. Нажмите **OK**, затем ▶ (или `Shift+F10`)

**Запуск frontend в PyCharm:**

1. Откройте терминал внутри PyCharm: `View → Tool Windows → Terminal`
2. Выполните:
```powershell
cd frontend
npm run dev
```

---

### URL после запуска

| Сервис | Адрес |
|---|---|
| Фронтенд (React) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI (документация API) | http://localhost:8000/api/docs |
| Health check | http://localhost:8000/api/health |

> Swagger доступен только при `DEBUG=true` в файле `.env`

---

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

## Локальный запуск на Windows (для разработки)

### Требования

Перед началом установите:

| Инструмент | Версия | Ссылка |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| PostgreSQL | 15+ | https://www.enterprisedb.com/downloads/postgres-postgresql-downloads |
| Git | последняя | https://git-scm.com/download/win |

> **Важно при установке Python:** отметьте галочку **"Add Python to PATH"** на первом экране установщика.

---

### Шаг 1 — Клонировать репозиторий

Откройте **PowerShell** или **Git Bash** и выполните:

```powershell
git clone https://github.com/devDaniilNovikov/BIM-MANAGER.git
cd BIM-MANAGER
```

---

### Шаг 2 — База данных PostgreSQL

После установки PostgreSQL откройте **SQL Shell (psql)** (ищите в меню Пуск) или используйте **pgAdmin**.

Введите пароль суперпользователя `postgres`, затем выполните:

```sql
CREATE USER bim WITH PASSWORD 'bimpass';
CREATE DATABASE bim_system OWNER bim;
\q
```

Если используете psql из PowerShell:

```powershell
psql -U postgres -c "CREATE USER bim WITH PASSWORD 'bimpass';"
psql -U postgres -c "CREATE DATABASE bim_system OWNER bim;"
```

---

### Шаг 3 — Backend

Откройте **PowerShell** и перейдите в папку backend:

```powershell
cd backend
```

Создайте и активируйте виртуальное окружение:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

> Если PowerShell выдаёт ошибку "execution of scripts is disabled", выполните один раз:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Установите зависимости:

```powershell
pip install -r requirements.txt
```

> **Замечание по ifcopenshell:** если `pip install` завершается ошибкой на этом пакете, установите его отдельно:
> ```powershell
> pip install ifcopenshell
> ```
> При сохранении ошибки используйте готовый wheel с https://github.com/IfcOpenShell/IfcOpenShell/releases — скачайте файл `.whl` под вашу версию Python (например `ifcopenshell-0.8.x-py311-win_amd64.whl`) и установите:
> ```powershell
> pip install путь\к\файлу.whl
> ```

Создайте файл `.env` в папке `backend\`:

```powershell
New-Item -Path ".env" -ItemType File
notepad .env
```

Вставьте в открывшийся блокнот и сохраните:

```
DATABASE_URL=postgresql+asyncpg://bim:bimpass@localhost:5432/bim_system
DEBUG=true
```

Запустите backend:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Таблицы создаются автоматически при первом старте. Swagger UI будет доступен по адресу http://localhost:8000/api/docs.

---

### Шаг 4 — Frontend

Откройте **новое окно PowerShell** (backend должен продолжать работать в первом) и выполните:

```powershell
cd frontend
npm install
npm run dev
```

Фронтенд будет доступен на http://localhost:5173.

---

### Шаг 5 — Запуск тестов (опционально)

```powershell
cd backend
.venv\Scripts\activate
pytest
```

---

### Типичные проблемы на Windows

| Проблема | Решение |
|---|---|
| `'python' is not recognized` | Переустановите Python с флагом "Add to PATH", или используйте `py` вместо `python` |
| `'uvicorn' is not recognized` | Виртуальное окружение не активировано — выполните `.venv\Scripts\activate` |
| `Error connecting to PostgreSQL` | Проверьте, что служба PostgreSQL запущена: Win+R → `services.msc` → найдите postgresql → Запустить |
| `npm : The term 'npm' is not recognized` | Переустановите Node.js и откройте новый терминал |
| Ошибка порта 8000 или 5173 занят | Измените порт: `uvicorn ... --port 8001` или `vite --port 5174` |
| `asyncpg` не устанавливается | Установите Visual C++ Build Tools с https://visualstudio.microsoft.com/visual-cpp-build-tools/ |

---

## Полезные команды

Просмотр логов:
```bash
docker compose logs backend -f
docker compose logs frontend -f
```

Запуск тестов:
```bash
cd backend
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pytest
```
