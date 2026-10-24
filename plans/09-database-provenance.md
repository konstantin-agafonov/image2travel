# 09. База данных: происхождение, импорт и эксплуатация

[Оглавление](README.md) · Далее: [источники](10-data-sources.md)

## Почему недостаточно таблицы «ссылки на направление»

URL у озера не объясняет, откуда взялись часы работы лодки, цена входа и оценка людности. Нужна связь **конкретного поля с утверждением и конкретным снимком источника**. Одновременно важно сохранить историю, не перезаписывать конфликт молча.

## Запуски и источники

```sql
CREATE TABLE ingestion_runs (
  id TEXT PRIMARY KEY,
  command TEXT NOT NULL,
  provider TEXT NOT NULL,
  scope_json TEXT NOT NULL CHECK (json_valid(scope_json)),
  parser_version TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
  counters_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(counters_json)),
  error_code TEXT
);

CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  canonical_url TEXT NOT NULL UNIQUE,
  title TEXT,
  publisher TEXT,
  language TEXT,
  source_kind TEXT NOT NULL
    CHECK (source_kind IN ('api', 'official_page', 'guide', 'dataset', 'editorial')),
  lineage_group TEXT NOT NULL,
  license_code TEXT,
  license_url TEXT,
  attribution TEXT,
  terms_checked_at TEXT,
  last_attempt_at TEXT,
  last_success_at TEXT
);

CREATE TABLE source_snapshots (
  id INTEGER PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id),
  run_id TEXT NOT NULL REFERENCES ingestion_runs(id),
  content_sha256 TEXT NOT NULL,
  fetched_at TEXT NOT NULL,
  source_modified_at TEXT,
  external_revision TEXT,
  http_status INTEGER,
  etag TEXT,
  last_modified TEXT,
  content_type TEXT,
  raw_path TEXT,
  parser_version TEXT NOT NULL,
  UNIQUE (source_id, content_sha256, parser_version)
);
CREATE INDEX idx_snapshots_source ON source_snapshots(source_id, fetched_at);
```

`sources` — страницы/документы, а не только домены. Реестр провайдера и rate limits живёт в конфигурации `data/sources/*.yaml`. Секреты не входят в URL, сохранённый в БД.

`lineage_group` связывает копии и общий первоисточник. Wikipedia и Wikidata нельзя автоматически считать независимыми, если одно значение перенесено между ними. Для OSM сохранять attribution и признаки производных данных.

Для неизменного content hash переиспользуется snapshot; время успешного повторного получения обновляется отдельно, а `run_id` остаётся запуском первого создания. HTTP 304 допустим только при наличии предыдущего тела/снимка; не означает автоматическое повторное содержательное ревью.

`raw_path` — относительный путь в защищённом `data/raw/`. При запрете сохранять полный материал хранить только разрешённую выдержку/метаданные и hash, а raw_path оставлять NULL. Снимки не выдавать как открытые MCP-files.

## Утверждения и доказательства

```sql
CREATE TABLE claims (
  id TEXT PRIMARY KEY,
  identity_key TEXT NOT NULL UNIQUE,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  field_path TEXT NOT NULL,
  value_json TEXT NOT NULL CHECK (json_valid(value_json)),
  origin TEXT NOT NULL CHECK (origin IN ('source', 'editorial', 'computed')),
  status TEXT NOT NULL
    CHECK (status IN ('verified', 'editorial', 'estimated', 'unknown', 'conflicting', 'stale')),
  confidence REAL CHECK (confidence BETWEEN 0 AND 1),
  method TEXT,
  valid_from TEXT,
  valid_to TEXT,
  checked_at TEXT,
  review_due_at TEXT,
  is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
  created_at TEXT NOT NULL,
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from)
);
CREATE UNIQUE INDEX idx_claim_current
  ON claims(entity_id, field_path) WHERE is_current = 1;
CREATE INDEX idx_claim_due ON claims(review_due_at, status);

CREATE TABLE claim_evidence (
  claim_id TEXT NOT NULL REFERENCES claims(id),
  snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),
  locator TEXT NOT NULL,
  evidence_role TEXT NOT NULL CHECK (evidence_role IN ('supports', 'contradicts', 'context')),
  excerpt TEXT,
  PRIMARY KEY (claim_id, snapshot_id, locator, evidence_role)
);

CREATE TABLE claim_dependencies (
  claim_id TEXT NOT NULL REFERENCES claims(id),
  input_claim_id TEXT NOT NULL REFERENCES claims(id),
  PRIMARY KEY (claim_id, input_claim_id),
  CHECK (claim_id <> input_claim_id)
);
```

`locator`: JSONPath, Wikidata property/statement ID, OSM tag, шаблон/секция wikitext, CSS-selector/табличная ячейка. Выдержки короткие и только при разрешении лицензии. Source-origin `verified` требует поддерживающее доказательство, editorial — автора/ревью в metadata seed; computed — метод и входные claims либо воспроизводимый dataset. Эти инварианты проверяет publisher.

`field_path` — **не произвольный SQL/JSONPath от пользователя**, а версия реестра разрешённых полей: `name`, `coordinates`, `opening_hours`, `months.5.crowd_score`, `prices.{id}.conditions`, `access_rules.{id}`, `restrictions.{id}`. Проекции в обычные таблицы обновляет mapping publisher. Межтабличную ссылку, зашитую в path, SQLite не контролирует: repository и `data-check` обязаны это делать.

История состоит из разных claims; только один current на entity+field_path. При конфликте current — явно `conflicting` с кандидатными значениями, остальные свидетельства сохраняются. Нельзя оставлять в проекции «проверенное» старое расписание без маркировки конфликта. Calculated claims имеют ацикличный граф зависимостей (проверка кодом).

`identity_key` — hash нормализованного entity, поля, значения, origin, условий действия и идентичности доказательства/редакционной ревизии. Повторный импорт не создаёт дубликат; изменение значения или доказательства может создать новую версию. `checked_at` обновляется только успешной проверкой именно этого утверждения, не сетевой попыткой.

## Staging и ошибки импорта

```sql
CREATE TABLE ingestion_items (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES ingestion_runs(id),
  snapshot_id INTEGER REFERENCES source_snapshots(id),
  external_key TEXT NOT NULL,
  candidate_json TEXT NOT NULL CHECK (json_valid(candidate_json)),
  stage TEXT NOT NULL CHECK (stage IN ('parsed', 'normalized', 'review', 'published', 'rejected')),
  error_code TEXT,
  error_detail TEXT,
  UNIQUE (run_id, external_key)
);
CREATE INDEX idx_ingestion_items_review ON ingestion_items(stage, run_id);
```

Импорт с ошибкой не загрязняет активный каталог. Ручное review переводит запись в published либо rejected; отчёт содержит причину, не только число записей.

## Кэш и файлы

```sql
CREATE TABLE api_cache (
  provider TEXT NOT NULL,
  cache_key TEXT NOT NULL,
  request_json TEXT NOT NULL CHECK (json_valid(request_json)),
  response_json TEXT NOT NULL CHECK (json_valid(response_json)),
  fetched_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  stale_until TEXT,
  attribution_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(attribution_json)),
  PRIMARY KEY (provider, cache_key)
);
CREATE INDEX idx_api_cache_expiry ON api_cache(expires_at);

CREATE TABLE files (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('export', 'tmp')),
  relative_path TEXT NOT NULL UNIQUE,
  mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
  sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX idx_files_expiry ON files(expires_at);

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  checksum TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
CREATE TABLE catalog_metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

Ключ кэша — hash provider+endpoint+нормализованных аргументов+версии адаптера. Включать транспортный профиль, даты, timezone, единицы, валюту; не включать ключ API, имя пользователя, фото или полный brief. Содержимое кэша не становится проверенным каталогом автоматически.

Экспорты содержат поездку, поэтому TTL ограничен (default 7 дней), и пользователь уведомлён о сохранении. Временные файлы — до 24 часов. Файлы создаются с UUID-именами, запись сначала в tmp, затем atomic rename и metadata; восстановление чистит orphan только внутри управляемых директорий.

## Миграции, резервные копии и проверки

- Последовательные `data/migrations/001_*.sql`, checksum, транзакция, резервная копия перед изменением схемы.
- Бэкап через SQLite backup API; не копировать только основной файл работающей WAL-базы.
- `catalog_metadata`: версия taxonomy, seed revision и версия опубликованного каталога; обновлять после успешного commit.
- `PRAGMA foreign_key_check`, `integrity_check`, проверка JSON-схем, типов entities, текущих claims и FTS rebuild/integrity.
- В git не коммитить DB, WAL/SHM, raw, отчёты и экспорты. Runtime-БД можно восстановить миграциями + одобренным seed; локальные свежие данные — резервной копией.
