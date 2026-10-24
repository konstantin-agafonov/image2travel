# 07. База данных: каталог направлений и POI

[Оглавление](README.md) · Далее: [практические данные](08-database-travel-data.md)

## Принципы схемы

SQLite — один файл `image2travel.db`. Для каждого соединения включать `foreign_keys=ON`; использовать WAL, `busy_timeout` и параметризованный SQL. Проверять наличие JSON-функций и FTS5 при старте.

- Стабильный внутренний `id` — UUID либо фиксированный ID seed; название не является ключом.
- Все даты проверки — UTC ISO 8601 единого формата, локальная дата поездки — отдельно.
- Координаты — WGS84, `lat`/`lon` в отдельных колонках; GeoJSON использует порядок **lon, lat**.
- Важные для фильтров и связей поля — обычные колонки/таблицы. JSON — валидируемые сложные профили и исходные теги, не замена всей схеме.
- `NULL` — неизвестно, а не 0, «открыто» или «нет ограничений».
- `updated_at` — время публикации карточки, **не дата проверки всех её фактов**. Проверка отдельного поля хранится в claims.
- Каталог не содержит user/trip/session. Связи источников и фактов описаны в [части 09](09-database-provenance.md).

## Связи

```text
entities (общий ID и тип)
 ├── countries → destinations (страна 1:N направление)
 ├── destinations → destination_months (12 строк сезонности)
 └── pois ← destination_pois → destinations (M:N)
entities ← external_ids (OSM / Wikidata / редакционный ID)
entities ← entity_tags → tags
entities ← claims → claim_evidence → source_snapshots → sources
entities ← price_estimates / access_rules / travel_restrictions
destinations ← climate_months / destination_search → destinations_fts
```

M:N нужна, чтобы одна точка не дублировалась в соседних направлениях. Крупное озеро может быть направлением или POI — редактор выбирает основную сущность. Его смотровая площадка/причал — отдельные POI. Один внешний ID нельзя бездумно присваивать нескольким объектам.

## Базовые сущности и внешние идентификаторы

```sql
CREATE TABLE entities (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('country', 'destination', 'poi')),
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'active', 'retired')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE countries (
  entity_id TEXT PRIMARY KEY REFERENCES entities(id),
  iso2 TEXT NOT NULL UNIQUE CHECK (length(iso2) = 2),
  name TEXT NOT NULL,
  default_currency TEXT
);

CREATE TABLE external_ids (
  provider TEXT NOT NULL,
  external_id TEXT NOT NULL,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  external_version TEXT,
  last_seen_at TEXT NOT NULL,
  PRIMARY KEY (provider, external_id)
);
CREATE INDEX idx_external_ids_entity ON external_ids(entity_id);
```

Для OSM: `provider=osm`, `external_id=node/123`, `way/456` или `relation/789`; числа разных типов не пересекаются. Для Wikidata: `provider=wikidata`, `external_id=Q...`. Версия OSM или revision Wikidata не заменяет дату проверки реального расписания.

Для таблиц-подтипов добавить триггеры/проверки repository: тип entity обязан соответствовать таблице. `entities.kind` после создания не менять без явной миграции; `retired` сохраняет историю вместо каскадного удаления.

## Направления

```sql
CREATE TABLE destinations (
  entity_id TEXT PRIMARY KEY REFERENCES entities(id),
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  country_id TEXT NOT NULL REFERENCES countries(entity_id),
  region TEXT,
  lat REAL NOT NULL CHECK (lat BETWEEN -90 AND 90),
  lon REAL NOT NULL CHECK (lon BETWEEN -180 AND 180),
  timezone TEXT NOT NULL,
  bbox_json TEXT CHECK (bbox_json IS NULL OR json_valid(bbox_json)),
  summary TEXT NOT NULL,
  experience_json TEXT NOT NULL CHECK (json_valid(experience_json)),
  visual_json TEXT NOT NULL CHECK (json_valid(visual_json)),
  anti_features_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(anti_features_json)),
  min_trip_days INTEGER NOT NULL DEFAULT 1 CHECK (min_trip_days >= 1),
  max_trip_days INTEGER NOT NULL DEFAULT 7 CHECK (max_trip_days >= min_trip_days),
  taxonomy_version TEXT NOT NULL,
  editorial_reviewed_at TEXT
);
CREATE INDEX idx_destinations_country ON destinations(country_id);

CREATE TABLE destination_months (
  destination_id TEXT NOT NULL REFERENCES destinations(entity_id),
  month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
  season_score REAL CHECK (season_score BETWEEN 0 AND 1),
  crowd_score REAL CHECK (crowd_score BETWEEN 0 AND 1),
  availability TEXT NOT NULL DEFAULT 'unknown'
    CHECK (availability IN ('open', 'limited', 'closed', 'unknown')),
  note TEXT,
  PRIMARY KEY (destination_id, month)
);
CREATE INDEX idx_destination_months_filter
  ON destination_months(month, availability, season_score);
```

`timezone` — IANA (`Europe/Ljubljana`), валидируется `zoneinfo`. Bbox — `[south, west, north, east]`; это границы поиска кандидатов, не разрешение доступа. Центр направления не используется как вход в парк или точная точка съёмки.

`experience_json`: эмоции, темп, усилие, социальность, сенсорные условия и сценарии переживания. `visual_json`: ландшафт, архитектура, палитра, свет. Это редакционные профили с provenance, не автоматически подтверждённые ощущения. Сезонность и людность — независимые показатели; неизвестный crowd остаётся `NULL`.

## Точки интереса

```sql
CREATE TABLE pois (
  entity_id TEXT PRIMARY KEY REFERENCES entities(id),
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  lat REAL CHECK (lat BETWEEN -90 AND 90),
  lon REAL CHECK (lon BETWEEN -180 AND 180),
  coordinate_kind TEXT NOT NULL DEFAULT 'unknown'
    CHECK (coordinate_kind IN ('entrance', 'point', 'representative', 'unknown')),
  timezone TEXT,
  duration_min INTEGER CHECK (duration_min > 0),
  effort TEXT CHECK (effort IN ('easy', 'moderate', 'hard', 'unknown')),
  best_time_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(best_time_json)),
  opening_hours_raw TEXT,
  opening_hours_json TEXT CHECK (opening_hours_json IS NULL OR json_valid(opening_hours_json)),
  opening_hours_status TEXT NOT NULL DEFAULT 'unknown'
    CHECK (opening_hours_status IN ('parsed', 'partial', 'unknown')),
  website_url TEXT,
  booking_url TEXT,
  osm_tags_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(osm_tags_json)),
  editorial_note TEXT,
  CHECK ((lat IS NULL) = (lon IS NULL))
);

CREATE TABLE destination_pois (
  destination_id TEXT NOT NULL REFERENCES destinations(entity_id),
  poi_id TEXT NOT NULL REFERENCES pois(entity_id),
  role TEXT NOT NULL DEFAULT 'optional'
    CHECK (role IN ('anchor', 'optional', 'backup', 'logistics')),
  priority INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (destination_id, poi_id)
);
CREATE INDEX idx_destination_pois_reverse ON destination_pois(poi_id);
CREATE INDEX idx_pois_geo ON pois(lat, lon);
```

У POI с неизвестными координатами/входом может быть справочная карточка, но он не должен автоматически попадать в точный маршрут. `representative` из центра OSM way/relation не означает «здесь можно стоять».

`duration_min` и `best_time_json` обычно редакционные оценки. `opening_hours_raw` сохраняет исходную строку; нормализованное расписание содержит интервалы, timezone и известные исключения. Неподдержанный `PH`, сезонная оговорка или условный доступ дают `partial`, а не «ежедневно открыто».

## Контролируемые теги

```sql
CREATE TABLE tags (
  id TEXT PRIMARY KEY,
  dimension TEXT NOT NULL,
  label_ru TEXT NOT NULL,
  taxonomy_version TEXT NOT NULL
);
CREATE TABLE entity_tags (
  entity_id TEXT NOT NULL REFERENCES entities(id),
  tag_id TEXT NOT NULL REFERENCES tags(id),
  weight REAL NOT NULL DEFAULT 1 CHECK (weight BETWEEN 0 AND 1),
  PRIMARY KEY (entity_id, tag_id)
);
CREATE INDEX idx_entity_tags_tag ON entity_tags(tag_id, entity_id);
```

Примеры ID: `emotion:calm`, `landscape:lake`, `activity:hiking`, `pace:slow`. Переводы и алиасы нормализуются на входе, а не создают произвольные новые теги. Provenance разметки: `claims.field_path=tags.emotion:calm`.

## Поиск по тексту

```sql
CREATE TABLE destination_search (
  rowid INTEGER PRIMARY KEY,
  destination_id TEXT NOT NULL UNIQUE REFERENCES destinations(entity_id),
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  summary TEXT NOT NULL,
  tags TEXT NOT NULL,
  aliases TEXT NOT NULL
);
CREATE VIRTUAL TABLE destinations_fts USING fts5(
  name, country, summary, tags, aliases,
  content='destination_search', content_rowid='rowid',
  tokenize='unicode61'
);
CREATE TRIGGER destination_search_ai AFTER INSERT ON destination_search BEGIN
  INSERT INTO destinations_fts(rowid, name, country, summary, tags, aliases)
  VALUES (new.rowid, new.name, new.country, new.summary, new.tags, new.aliases);
END;
CREATE TRIGGER destination_search_ad AFTER DELETE ON destination_search BEGIN
  INSERT INTO destinations_fts(destinations_fts, rowid, name, country, summary, tags, aliases)
  VALUES ('delete', old.rowid, old.name, old.country, old.summary, old.tags, old.aliases);
END;
CREATE TRIGGER destination_search_au AFTER UPDATE ON destination_search BEGIN
  INSERT INTO destinations_fts(destinations_fts, rowid, name, country, summary, tags, aliases)
  VALUES ('delete', old.rowid, old.name, old.country, old.summary, old.tags, old.aliases);
  INSERT INTO destinations_fts(rowid, name, country, summary, tags, aliases)
  VALUES (new.rowid, new.name, new.country, new.summary, new.tags, new.aliases);
END;
```

Текстовая проекция обновляется в той же транзакции, что карточка/теги/алиасы. Для алиасов — claim `aliases`; отдельная таблица потребуется только при сложной локализации. FTS ищет названия и описания, не заменяет объяснимый скоринг впечатлений. Векторный поиск/`sqlite-vec` — следующий этап.
