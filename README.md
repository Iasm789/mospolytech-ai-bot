# AIPolytech

Telegram-бот для студентов и абитуриентов Московского Политеха. Отвечает на вопросы про расписание, стипендии, общежития, услуги МФЦ и прочее — через меню или просто текстом в чат.

Бот называется **AIPolytech** (`@AIMosPolyHelperbot`). Информация берётся из официальных источников университета и локальной базы знаний.

---

## Что умеет

**Через меню:**
- расписание занятий по номеру группы (данные с `rasp.dmami.ru`);
- программы бакалавриата по факультетам;
- услуги МФЦ, стипендии, общежития, льготы;
- студенческие проекты и мероприятия;
- аспирантура, контакты, обратная связь;
- разделы для абитуриентов и студентов.

**Через свободный текст:**  
Можно написать вопрос своими словами — «как получить справку в МФЦ», «сколько стоит общежитие», «когда сессия» и т.п. ИИ даст вам ответ из нашей базы знаний.
P.S. Простите, что возможный долгий ответ. МЫ работаем над этим.

---

## Как устроены ответы на вопросы

Тут два слоя, и порядок их работы настраивается.

1. **RAG + локальная LLM (Ollama)** — бот ищет релевантные фрагменты в `docs/` (JSON и TXT) и просит модель сформулировать ответ на их основе.
2. **FAQ** — готовые пары вопрос–ответ из `docs/faq_questions.json`, с нечётким поиском и синонимами («общага» → «общежитие»).

По умолчанию (`ANSWER_PRIORITY=llm_first`): сначала LLM, если не получилось — FAQ.  
Можно переключить на `faq_first`, если Ollama недоступна или нужны быстрые шаблонные ответы.

LLM можно отключить совсем: `LOCAL_LLM_ENABLED=false` — тогда останутся FAQ и разделы меню.

---

## Стек

- Python 3.10, **aiogram 3**
- **Ollama** для локальной генерации
- Данные в JSON/TXT, без базы данных
- Docker + Docker Compose для развёртывания

---

## Структура проекта

```
├── main.py                 # точка входа
├── handlers/               # обработчики Telegram (меню, расписание, Q&A…)
├── services/               # парсеры, RAG, работа с данными
├── models/                 # модели данных
├── config/                 # настройки и константы
├── docs/                   # база знаний (JSON, TXT)
├── data/                   # кэши, CSV групп (не в git)
├── scripts/                # утилиты для парсинга и генерации данных
├── Dockerfile
├── docker-compose.yml      # бот + Ollama
└── docker-compose.bot-only.yml   # только бот
```

---

## Развёртывание через Docker

Это основной способ запуска. На машине нужны **Docker Desktop** (Windows/macOS) или Docker Engine + Compose (Linux).

### 1. Клонировать репозиторий

```bash
git clone <url-репозитория>
cd ai
```

### 2. Создать `.env`

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Откройте `.env` и укажите **BOT_TOKEN** — его даёт [@BotFather](https://t.me/BotFather) в Telegram.

Остальное можно оставить по умолчанию. Для Docker Compose URL Ollama переопределяется автоматически на `http://ollama:11434/...`, в `.env` это менять не нужно.

### 3. Подготовить данные

JSON-файлы в репозиторий не попадают (они в `.gitignore`), но бот без них будет работать урезанно. Положите в `docs/` то, что у вас есть:

| Файл | Для чего |
|------|----------|
| `faq_questions.json` | FAQ-ответы |
| `events_data.json` | мероприятия |
| `scholarships.json` | стипендии |
| `dormitories.json` | общежития |
| `mfc_services.json`, `mfc_old_services.json` | услуги МФЦ |
| `aspirantura_data.json` | аспирантура |
| `military.json` | раздел для призывников |

В `data/cache/` — кэш программ (`programs_cache.json`) и прочее.  
В `data/` — `num_group.csv` со списком групп для расписания (если есть).

Папки создадутся сами при первом запуске, но пустые JSON бот просто не подхватит — в логах будет предупреждение, не ошибка.

TXT-файлы в `docs/` уже лежат в репозитории — они участвуют в RAG-индексе.

### 4. Запустить стек

```bash
docker compose up -d --build
```

Поднимутся два контейнера:
- `aipolytech-bot` — сам бот;
- `aipolytech-ollama` — Ollama на порту `11434`.

Первый запуск может занять время: скачается образ Ollama (~4 ГБ).

### 5. Загрузить модель в Ollama

Ollama стартует пустой. Модель нужно скачать отдельно — один раз:

```bash
docker compose --profile init up ollama-init
```

По умолчанию тянется `qwen2.5:7b-instruct`. Другую модель можно указать так:

```bash
# в .env добавить:
# OLLAMA_MODEL=mistral:latest

docker compose --profile init up ollama-init
```

Или вручную:

```bash
docker exec aipolytech-ollama ollama pull qwen2.5:7b-instruct
```

**Важно:** модель в `.env` (`LOCAL_LLM_MODEL`, `LOCAL_LLM_MODELS`) должна совпадать с тем, что реально скачана в Ollama. Иначе бот запустится, но LLM-ответы будут падать с 404.

### 6. Проверить, что всё живо

```bash
docker compose ps
docker compose logs -f bot
```

В логах должны быть строки вроде «Бот успешно инициализирован» и «Start polling». После этого можно писать боту в Telegram.

---

## Полезные команды Docker

```bash
# пересобрать образ после изменений в коде
docker compose up -d --build

# логи
docker compose logs -f bot
docker compose logs -f ollama

# остановить
docker compose down

# остановить и удалить том с моделями Ollama (осторожно!)
docker compose down -v
```

---

## Запуск без Ollama в Compose

Если Ollama уже крутится на хосте или LLM не нужна:

```bash
# LLM отключена — FAQ + меню
# в .env: LOCAL_LLM_ENABLED=false

docker compose -f docker-compose.bot-only.yml up -d --build
```

Если Ollama на хосте, а бот в контейнере — в `.env` укажите:

```
LOCAL_LLM_API_URL=http://host.docker.internal:11434/api/generate
```

(на Linux вместо `host.docker.internal` может понадобиться IP хоста или `network_mode: host`).

---

## Настройка через `.env`

| Переменная | Смысл |
|------------|--------|
| `BOT_TOKEN` | токен Telegram-бота, обязателен |
| `ANSWER_PRIORITY` | `llm_first` или `faq_first` |
| `LOCAL_LLM_ENABLED` | включить/выключить генерацию через Ollama |
| `LOCAL_LLM_MODEL` | основная модель |
| `LOCAL_LLM_MODELS` | каскад моделей через запятую (fallback) |
| `ADMIN_IDS` | ID админов через запятую |
| `DEBUG` | подробные логи |
| `OLLAMA_HOST_PORT` | порт Ollama на хосте (по умолчанию 11434) |
| `OLLAMA_MODEL` | модель для `ollama-init` |

Полный список — в `config/settings.py` и `.env.example`.

---

## Локальный запуск без Docker

Если нужно разрабатывать или отладить без контейнеров:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # и прописать BOT_TOKEN

# Ollama должна быть запущена локально
ollama pull qwen2.5:7b-instruct

python main.py
```

Для production и сервера удобнее Docker — там уже отрезаны dev-зависимости (pytest, selenium, playwright) через `requirements-prod.txt`.

---

## Обновление данных

Данные с сайта университета со временем меняются. В `scripts/` лежат парсеры — `parse_programs.py`, `init_events.py`, `generate_programs_cache.py` и др. Их обычно гоняют на хосте (там есть Selenium/Playwright), результат кладут в `docs/` и `data/cache/`. Контейнер бота эти папки монтирует как volume — пересборка образа не нужна.

---

## Типичные проблемы

**Бот перезапускается в цикле**  
Смотрите `docker compose logs bot`. Частые причины: неверный `BOT_TOKEN`, синтаксическая ошибка в коде, нет `.env`.

**LLM не отвечает, в логах 404**  
Модель не скачана в Ollama или имя в `.env` не совпадает. Проверьте:

```bash
docker exec aipolytech-ollama ollama list
```

**«FAQ данные не загружены»**  
Нет файла `docs/faq_questions.json`. Бот работает, но FAQ-поиск недоступен.

**Долгий первый ответ**  
Холодный старт модели. Можно включить прогрев: `LOCAL_LLM_WARMUP_ENABLED=true` в `.env`.

**Порт 11434 занят**  
В `.env` смените `OLLAMA_HOST_PORT=11435` и перезапустите compose.

---

## Тесты и CI

```bash
pip install -r requirements.txt
pytest -q
```

В GitHub Actions (`.github/workflows/ci.yml`) прогоняются ruff, black и pytest.

---

## Команды бота в Telegram

| Команда | Действие |
|---------|----------|
| `/start` | приветствие и главное меню |
| `/menu` | вернуться в меню |
| `/help` | краткая справка |

---

Если что-то не заводится — начните с `docker compose logs bot`. В девяти случаях из десяти проблема либо в токене, либо в модели Ollama, либо в отсутствующем JSON в `docs/`.
