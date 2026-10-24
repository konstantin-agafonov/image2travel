# 21. Этапы реализации, запуск и следующие шаги

[Оглавление](README.md)

## Этап 1. Основа и единые контракты

Задачи: Python/uv, закреплённый FastMCP, Pydantic schemas, taxonomy, DATA_DIR, stderr logging, миграции SQLite, repository и data-check.

Готово: пустая БД создаётся частями 07–09, схема валидируется, ошибки входа понятны, нет сетевых зависимостей для старта. До кода согласовать стартовую географию, провайдеров и лицензии.

## Этап 2. Малый проверенный seed

Задачи: 3–5 направлений, external IDs, 10–15 POI на каждое, anchors/backups, базовые цены/доступ, provenance, идемпотентный seed CLI.

Готово: повторная загрузка безопасна, есть история поля, ни одного уверенного критичного факта без источника. Редакционный опыт отделён от извлечённой географии.

## Этап 3. Три основных tools

Задачи: matching, diversity, itinerary, validation; `plan_trip`, `build_itinerary`, `validate_itinerary`; skill и output template.

Готово: фото/описание → concepts → выбор → маршрут → validation проходит на frozen каталоге. Unknown и impossible-case не замалчиваются.

## Этап 4. Конвейер источников

Задачи: fetch/staging/snapshots, PBF/OSM, Wikidata, Wikivoyage; allowlist официальных страниц и ручной fallback; review/diff; FX, климат и профильная маршрутизация по необходимости.

Порядок: сначала parser fixtures и единый CandidateRecord, затем минимальный live smoke. Массовые данные получать разрешёнными extracts, не Nominatim. Этап зависит от прав доступа, не только от разработки.

Готово: импорт повторяем, ошибки не загрязняют каталог, защищённая редактура не перезаписывается, сформирован отчёт свежести/покрытия.

## Этап 5. Полный MCP и экспорт

Задачи: `get_destination`, `verify_place`, `export_itinerary`, resources/prompts, Markdown/ICS/GeoJSON, files TTL/cleanup. Проверить клиентскую совместимость и ограничить размеры выдачи.

Готово: шесть tools, экспорт читается клиентом, рестарт не требует пользовательской сессии, stdout чистый, файлы недоступны по произвольному пути.

## Этап 6. Расширение и бета

Задачи: 10 → 30–50 направлений, калибровка весов, минимум 30 photo eval cases, десять frozen многошаговых MCP eval, минимум три host, лицензии распространения, performance/security review, интервью.

Готово: выполнены [gates части 20](20-testing-and-evaluation.md). Оценку сроков делать после проверки скорости ручной редакционной подготовки; 30–50 качественных направлений нельзя автоматически обещать за одну неделю. Порядок выше — зависимости, не гарантированный календарь.

## Запуск из репозитория (планируемый)

```bash
uv sync
uv run python -m image2travel seed --dry-run
uv run python -m image2travel seed
uv run python -m image2travel data-check
uv run python -m image2travel --transport stdio
```

`IMAGE2TRAVEL_DATA_DIR` задаёт абсолютный путь. Локальный default `./data/` разрешён при наличии прав записи и осознанном cwd. В installed package seed берётся из package resources, runtime-БД не пишется в site-packages.

После публикации пакета:

```bash
uvx image2travel-mcp
```

Это целевая команда, пока не существующий опубликованный артефакт. Первое создание БД/загрузка packaged seed локальны и идемпотентны; сетевой bulk-import не происходит молча при запуске host.

## Подключение клиента

Обобщённый **не универсальный** формат для клиентов с `mcpServers`:

```json
{
  "mcpServers": {
    "image2travel": {
      "command": "uvx",
      "args": ["image2travel-mcp"],
      "env": {"IMAGE2TRAVEL_DATA_DIR": "/absolute/path/to/image2travel-data"}
    }
  }
}
```

Реальные host имеют разные конфигурации/поддержку skills. В выпуске дать проверенные инструкции каждого выбранного клиента; не выдавать этот JSON за конфигурацию всех. Установка skill — отдельная операция. Сервер MVP только stdio, не открывает HTTP-порт.

## Runtime и секреты

В будущем `.gitignore` должен исключать `data/*` (кроме `.gitkeep`), `.env`, DB/WAL/SHM, raw и экспорты. Не исключать packaged seed в `src/image2travel/data/seed/`. `.env.example` содержит названия настроек без ключей; загрузку env определяет приложение, host не обязан читать `.env` автоматически.

Операционные команды: seed, ingest, data-check, cleanup, backup. Большие импорты/review выполняет оператор; публичный MCP не даёт административных инструментов. Для регулярного обновления — внешний timer; отдельные очереди пока не нужны.

## Next steps после доказанного качества

- MCP App, интерактивная карта, PDF, веб-приложение на том же core.
- Optional API рейсов, полноценный GTFS/transit provider и события.
- Расширение на города, гастрономию, семьи, групповые и несколько фото.
- SQLite embeddings при доказанной необходимости семантического поиска.
- Сохранённые поездки, аккаунты, публичные ссылки и remote transport — с отдельной privacy/auth-моделью.
- Server-side vision с добровольной загрузкой, MIME/size/EXIF-policy, TTL и новыми files kinds.

Следующие шаги не должны размывать MVP: сначала качество данных и выполнимость поездки, затем новый интерфейс и масштабирование.
