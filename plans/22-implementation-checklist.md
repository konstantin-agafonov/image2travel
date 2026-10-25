# 22. Чеклист реализации Image2Travel

Проверка соответствия плана текущему состоянию. Отмечено то, что реализовано в кодовой базе.

## Этап 1. Основа и единые контракты
- [x] Структура проекта (pyproject.toml, src/layout)
- [x] FastMCP в проекте
- [x] Pydantic-схемы (ExperienceFingerprint, TripBrief, DestinationConcept, PlanTripResult)
- [x] DATA_DIR и конфигурация
- [x] Логирование в stderr (базовое)
- [x] Миграции SQLite
- [x] Инициализация БД (db.init_db)
- [x] Репозитории (базовый CatalogRepo)
- [x] data-check (базовый)
- [ ] Полноценный repository-слой для всех сущностей
- [ ] Согласование старта географии/провайдеров/лицензий (конфиг)

## Этап 2. Малый проверенный seed
- [x] Миграция основного каталога (entities/countries/destinations/pois/destination_pois/months/tags/fts)
- [x] CLI seed
- [x] Seed 3 направлений (Lake Bled, Plitvice Lakes, Hallstatt)
- [x] POI (5 штук) с привязкой к направлениям
- [x] Базовые price_estimates
- [x] Идемпотентность seed (INSERT OR IGNORE/REPLACE)
- [ ] 10-15 POI на каждое направление (сейчас ~1-2 на направление)
- [ ] anchors/backups роли
- [ ] Больше проверенных цен/доступ
- [ ] Полноценный provenance для seed-данных

## Этап 3. Три основных tools + skill
- [x] `plan_trip`
- [x] `build_itinerary`
- [x] `validate_itinerary`
- [x] matching (базовый с фильтрацией/скорингом/диверсификацией)
- [x] itinerary builder
- [x] validator
- [x] Skill image2travel (SKILL.md + references)
- [ ] Калибровка весов matching под реальные кейсы
- [ ] Улучшенная диверсификация

## Этап 4. Конвейер источников
- [x] Структура ingestion (cli/pipeline/parsers)
- [ ] Фетч/стейджинг/snapshots с полным циклом
- [ ] Парсеры OSM/Wikidata/Wikivoyage/official (только заглушки)
- [ ] allowlist источников
- [ ] review/diff механика
- [ ] Claims система в работе (таблицы есть, логика минимальна)

## Этап 5. Полный MCP и экспорт
- [x] `get_destination`
- [x] `verify_place`
- [x] `export_itinerary`
- [x] Файловый менеджер с TTL
- [x] Экспорт в markdown
- [ ] resources/prompts
- [ ] Поддержка ICS/GeoJSON
- [ ] Cleanup/очистка истекших файлов
- [ ] Ограничение размеров выдачи

## БД и данные (план 07-09)
- [x] entities/countries/sources/external_ids
- [x] destinations/pois/destination_pois
- [x] destination_months
- [x] tags/entity_tags/FTS
- [x] ingestion_runs/source_snapshots
- [x] claims/claim_evidence/claim_dependencies
- [x] ingestion_items
- [x] currencies/price_estimates/exchange_rates
- [x] access_rules/travel_restrictions/climate_months
- [x] api_cache/files/schema_migrations/catalog_metadata
- [ ] Интеграция access_rules в валидацию
- [ ] Интеграция travel_restrictions в рекомендации
- [ ] Использование climate_months
- [ ] Полноценная работа с claims/provenance

## Качество, тесты, запуск
- [x] Базовые тесты (imports, core)
- [x] `uv run python -m image2travel seed`
- [x] `uv run python -m image2travel data-check`
- [x] `uv run python -m image2travel` (запуск MCP)
- [ ] Расширенные тесты по плану (20-testing-and-evaluation)
- [ ] eval-кейсы
- [ ] Полноценный data-check с проверками

## Итог
**MVP готов к базовому использованию.** Основной флоу работает. Большая часть расширенной логики (provenance/ingestion/расширенные данные) заложена в схеме, но требует доработки.
