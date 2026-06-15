# 📋 Lighting Equipment Matcher

Сервис автоматического подбора аналогов светотехнического оборудования

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📖 О проекте

**Lighting Equipment Matcher** — веб-сервис для автоматического извлечения позиций светотехнического оборудования из технических заданий (ТЗ) и их сопоставления с фиксированным каталогом продукции.

### Возможности

- ✅ **Форматы файлов:** DOC, DOCX, PDF
- ✅ **Извлечение данных:** автоматическое распознавание названий, количества и характеристик
- ✅ **LLM интеграция:** использование Ollama (llama3.2) для интеллектуального парсинга
- ✅ **Умный поиск:** сопоставление с каталогом по мощности, световому потоку, цветовой температуре и размерам
- ✅ **Оценка соответствия:** взвешенная оценка с комментариями по отклонениям
- ✅ **Экспорт результатов:** генерация Excel-файла с результатами подбора
- ✅ **Веб-интерфейс:** простой и удобный интерфейс для загрузки файлов
- ✅ **Docker поддержка:** контейнеризация для лёгкого развёртывания

---

## 🚀 Быстрый старт

### Требования

- Python 3.11
- Ollama (опционально, для LLM функционала)
- 4 GB RAM (рекомендуется 8 GB)

### Установка

**1. Клонирование репозитория**

```bash
git clone https://github.com/your-repo/lighting-matcher.git
cd lighting-matcher
```

**2. Создание виртуального окружения**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**3. Установка зависимостей**

```bash
pip install -r requirements.txt
```

**4. Настройка каталога**

```bash
mkdir data
cp /path/to/КАТАЛОГ_ред_18.03.26.xlsx data/
```

**5. Настройка конфигурации**

Создайте файл `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
USE_LLM=true
CATALOG_PATH=data/КАТАЛОГ_ред_18.03.26.xlsx
MAX_DEVIATION_PERCENT=20
```

**6. Запуск сервиса**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Откройте браузер: [http://localhost:8000](http://localhost:8000)

---

## 🐳 Docker установка

```bash
# Сборка образа
docker build -t lighting-matcher .

# Запуск с Ollama
docker-compose up -d

# Остановка
docker-compose down
```

---

## 📁 Структура проекта

```
lighting-matcher/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Конфигурация
│   ├── models.py            # Pydantic модели
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── doc_parser.py    # Парсер DOC/DOCX
│   │   ├── pdf_parser.py    # Парсер PDF
│   │   └── catalog_parser.py # Парсер каталога
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── llm_extractor.py # LLM извлечение
│   │   └── regex_extractor.py # Regex извлечение
│   ├── matcher/
│   │   ├── __init__.py
│   │   └── product_matcher.py # Поиск соответствий
│   └── utils/
│       ├── __init__.py
│       ├── units.py         # Конвертация единиц
│       └── fuzzy.py         # Нечёткое сравнение
├── data/
│   └── КАТАЛОГ_ред_18.03.26.xlsx
├── uploads/                 # Временные загрузки
├── outputs/                 # Результаты
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 📊 Алгоритм работы

### 1. Извлечение данных из файла

- **DOCX** — прямое чтение XML структуры через `python-docx`
- **PDF** — извлечение текста и таблиц через `pdfplumber`
- **DOC** — использование `antiword`/`catdoc` или бинарный поиск

### 2. Парсинг характеристик

Сервис извлекает следующие параметры:

| Параметр | Описание |
|---|---|
| Наименование товара | Из заголовков и таблиц |
| Количество | Числовые значения со словами «шт», «штук» |
| Мощность (Вт) | Числа с единицей «Вт» |
| Цветовая температура (К) | Числа с единицей «К» |
| Световой поток (лм) | Числа с единицей «лм» |
| Размеры (мм) | Значения с указанием длины/ширины/высоты |

### 3. Оценка соответствия

Взвешенная оценка по параметрам:

| Параметр | Вес | Допустимое отклонение |
|---|---|---|
| Мощность | 30% | ±20% |
| Световой поток | 30% | ±20% |
| Цветовая температура | 20% | ±20% |
| Размеры | 20% | ±20% |

Дополнительные бонусы:

- Совпадение названия (fuzzy matching): до **+15%**
- Совпадение ключевых слов: до **+10%**

### 4. Классификация результатов

| Score | Статус | Описание |
|---|---|---|
| ≥ 90% | ✅ ТОЧНОЕ СООТВЕТСТВИЕ | Все параметры в пределах допуска |
| 75–89% | ✓ ХОРОШЕЕ СООТВЕТСТВИЕ | Незначительные отклонения |
| 60–74% | ⚠ БЛИЗКИЙ АНАЛОГ | Есть отклонения, но товар подходит |
| 40–59% | ⚠ ЧАСТИЧНОЕ СООТВЕТСТВИЕ | Часть параметров не совпадает |
| < 40% | ❌ СЛАБОЕ СООТВЕТСТВИЕ | Рекомендуется другой выбор |

---

## 🎯 Пример использования

**Входной файл (ТЗ)**

```
1. Светильник светодиодный уличный
   Мощность: 200 Вт
   Цветовая температура: 4000 К
   Степень защиты: IP66
   Количество: 20 шт
```

**Выходной файл (result.xlsx)**

| № | Наименование | Кол-во | Характеристики | Наименование из каталога | Комментарий |
|---|---|---|---|---|---|
| 1 | Светильник светодиодный уличный | 20 | Мощность: 200 Вт, Цветовая температура: 4000 К | ЗИНАР ЗН-01-200-830 | ✓ ХОРОШЕЕ СООТВЕТСТВИЕ (score: 85%) |

---

## 🔧 API Endpoints

### `GET /` — Главная страница

Веб-интерфейс для загрузки файлов.

### `POST /match` — Обработка файла

Загружает файл, извлекает позиции и возвращает Excel с результатами.

**Параметры:**

- `file` (multipart/form-data) — файл ТЗ (DOC, DOCX, PDF)

**Ответ:** Excel-файл с результатами подбора.

### `GET /ollama/status` — Статус Ollama

Проверяет доступность LLM.

```json
{
  "available": true,
  "model": "llama3.2",
  "url": "http://localhost:11434"
}
```

### `GET /health` — Health check

Проверяет состояние сервиса.

```json
{
  "status": "ok",
  "catalog_loaded": true,
  "catalog_count": 266,
  "ollama_available": true
}
```

---

## 🛠 Технологии

**Backend**

- [FastAPI](https://fastapi.tiangolo.com/) — веб-фреймворк
- [Uvicorn](https://www.uvicorn.org/) — ASGI сервер
- [Pydantic](https://docs.pydantic.dev/) — валидация данных

**Парсинг документов**

- `python-docx` — работа с DOCX
- `pdfplumber` — извлечение из PDF
- `PyPDF2` — резервный парсер PDF
- `antiword` / `catdoc` — парсинг старых DOC

**Обработка данных**

- `pandas` — работа с таблицами
- `openpyxl` — генерация Excel
- `thefuzz` — нечёткое сравнение строк

**LLM интеграция**

- [Ollama](https://ollama.ai/) — локальный LLM сервер
- `llama3.2` — модель для извлечения данных

**Контейнеризация**

- Docker — контейнеризация приложения
- Docker Compose — оркестрация

---

## 🧪 Тестирование

**Проверка API**

```bash
# Health check
curl http://localhost:8000/health

# Статус Ollama
curl http://localhost:8000/ollama/status

# Загрузка файла
curl -X POST http://localhost:8000/match -F "file=@test.docx" --output result.xlsx
```

**Проверка парсинга**

```bash
python -c "from app.parsers import DocParser; print(DocParser.extract_text('test.docx'))"
```

---

## ⚙️ Конфигурация

| Переменная | Значение по умолчанию | Описание |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL Ollama сервера |
| `OLLAMA_MODEL` | `llama3.2` | Модель для извлечения |
| `USE_LLM` | `true` | Использовать LLM |
| `CATALOG_PATH` | `data/КАТАЛОГ_ред_18.03.26.xlsx` | Путь к каталогу |
| `MAX_DEVIATION_PERCENT` | `20` | Допустимое отклонение (%) |
| `SIMILARITY_THRESHOLD` | `0.7` | Порог схожести |

---

## 🐛 Устранение проблем

**Не удаётся прочитать `.doc` файл**

Откройте файл в Microsoft Word, сохраните как `.docx` или `.pdf` и загрузите заново.

**Ollama не подключается**

```bash
# Запустите Ollama
ollama serve

# Проверьте статус
curl http://localhost:11434/api/tags

# Установите модель
ollama pull llama3.2
```

**Ошибка импорта pandas**

```bash
pip uninstall numpy pandas -y
pip install numpy==1.24.3 pandas==2.0.3
```

**Порт 8000 занят**

```bash
python -m uvicorn app.main:app --reload --port 8001
```

---

## 🌟 Roadmap

**Реализовано**

- [x] Поддержка DOCX, PDF
- [x] Интеграция с Ollama
- [x] Взвешенная оценка соответствия
- [x] Веб-интерфейс
- [x] Docker контейнеризация

**В планах**

- [ ] Полная поддержка старых DOC файлов
- [ ] Графический интерфейс для просмотра результатов
- [ ] API для интеграции с ERP системами
- [ ] Кэширование результатов
- [ ] Пакетная обработка файлов

---

## 📄 Лицензия

[MIT License](LICENSE)

---

## 👥 Авторы

**Разработчик:** Denis

Проект выполнен в рамках тестового задания Data/AI Engineer.

---

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) за отличный фреймворк
- [Ollama](https://ollama.ai/) за локальный LLM сервер
- Open source сообществу за библиотеки

---

## 📞 Контакты

По вопросам использования и сотрудничества:

- **Email:** support@lighting-matcher.com
- **GitHub:** [https://github.com/your-repo/lighting-matcher](https://github.com/your-repo/lighting-matcher)
