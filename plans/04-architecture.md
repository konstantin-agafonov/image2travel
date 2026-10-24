# 04. Архитектура и структура проекта

[Оглавление](README.md) · Далее: [MCP](05-mcp-server.md)

```text
Фото + контекст
      ↓
Host: vision, диалог, skill, финальный Markdown
      ↓ TripBrief / Itinerary через MCP stdio
Python MCP adapter → core: matching / itinerary / validation
      ↓                    ↓
Repositories             API clients (только ограниченные проверки)
      ↓                    ↓
SQLite                 api_cache
      ↓
data/files/exports/

Отдельно: CLI ingest → fetch → parse → normalize → review → SQLite
          seed YAML → validate → idempotent load → SQLite
```

## Ответственность

Host отвечает за фото, fingerprint, вопросы и объяснение. Core — детерминированные расчёты без LLM. MCP adapter — схемы, инструменты, resources и ошибки. Repository — параметризованный SQL и транзакции. Importer — обновление каталога и происхождение фактов.

Сервер читает каталог из SQLite. YAML не является вторым runtime-хранилищем. Сеть не нужна для локального ранжирования; проверка прогноза, переездов и свежих ограничений может обращаться к настроенным провайдерам.

## Стек

Python 3.12, `uv`, FastMCP, Pydantic v2, стандартный `sqlite3`, FTS5, `httpx`, PyYAML с `safe_load`, `mwparserfromhell` для wikitext, HTML-парсер для разрешённых сайтов, pytest. Версии зависимостей фиксировать в lockfile.

Не смешивать API отдельного пакета FastMCP с API разных версий официального Python SDK: перед реализацией закрепить одну совместимую комбинацию и проверить минимум три host. Обновление библиотеки не должно автоматически ломать skill.

## Планируемая структура

```text
src/image2travel/
  __main__.py              # server / ingest / seed / data-check / cleanup
  server.py               # MCP adapter
  models.py               # публичные Pydantic-контракты
  db.py                   # подключения и миграции
  repositories/
  matching.py
  itinerary.py
  validate.py
  files.py
  clients/                # HTTP, лимиты, allowlist, кэш
  ingestion/
    pipeline.py
    normalize.py
    deduplicate.py
    parsers/              # osm, wikidata, wikivoyage, official, weather, fx
  data/
    migrations/*.sql
    taxonomy.yaml
    sources/*.yaml         # реестр провайдеров и разрешённых страниц
    seed/destinations/*.yaml
    seed/pois/*.yaml
    seed/facts/*.yaml
skill/
  SKILL.md
  references/
tests/
  fixtures/
evals/cases/*.json
plans/
data/                     # локальный runtime, не содержимое пакета
  image2travel.db
  raw/                    # разрешённые снимки импорта
  reports/
  files/exports/
  files/tmp/
```

Полные PBF могут быть входным локальным файлом вне runtime-каталога; не копировать гигабайты в SQLite. `files/uploads/` появится только с опциональным vision.

## Эксплуатационные ограничения

- Один локальный процесс, короткие транзакции; WAL и `busy_timeout` для параллельного чтения.
- Сетевые загрузки не выполнять внутри транзакции записи.
- **stdout занят MCP. Логи JSON идут в stderr**, не в stdout, как ошибочно предлагалось в исходном плане.
- Каталог данных задаётся абсолютным `IMAGE2TRAVEL_DATA_DIR`; default `./data/` только для осознанного локального запуска.
- В MVP нет HTTP endpoint и статической выдачи `data/`; доступ к экспорту по `file_id` через MCP.
