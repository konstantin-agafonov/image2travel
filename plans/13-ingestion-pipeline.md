# 13. Конвейер загрузки данных в SQLite

[Оглавление](README.md) · Далее: [seed и редактура](14-seed-and-curation.md)

## Общий путь

```text
Конфигурация провайдера + выбранные регионы/ID
    ↓ fetch (или local PBF/seed)
Источник + неизменяемый снимок + hash/revision
    ↓ parse
ingestion_items: исходные значения и locator
    ↓ normalize + schema validation
Координаты, валюта, время, теги, условия действия
    ↓ resolve entity + deduplicate
Кандидаты новых сущностей и новых версий claims
    ↓ quality checks + review / conflict policy
Одобренный набор изменений
    ↓ short transaction: UPSERT + claims + projections + FTS
Опубликованный каталог + catalog version
    ↓ report
Счётчики, rejected, conflicts, unknowns, источники для повторной проверки
```

## Разделение модулей

Fetcher отвечает за сеть, политику доступа, лимиты и снимок. Parser — чистая функция над сохранённым содержимым; не делает HTTP и SQL. Normalizer приводит типы/единицы. Resolver связывает внешние ID. Publisher знает mappings поля→таблица и транзакции. Reviewer управляет неоднозначностями.

Общий промежуточный `CandidateRecord`: provider, external_key, entity_kind, identity hints, fields, field evidence, raw_values, conditions, parser_version и diagnostics. Для перечисленных тарифов/правил external_key включает стабильный ключ предложения/правила, а не порядковый номер в HTML.

## Идемпотентность

- External ID уникален по provider+ID; UPSERT не использует `INSERT OR REPLACE`, который может удалить связанную сущность.
- Snapshot дедуплицируется по source+content hash+parser version.
- Claim использует identity_key; повторная загрузка не дублирует утверждения.
- Неизменный импорт не меняет опубликованную версию каталога без содержательного изменения.
- Импорт не удаляет вручную выбранные роли POI и редакционные профили.
- Отключение/удаление seed-файла не удаляет entity автоматически: нужен явный `retired` и подтверждённая область действия.

Воспроизводимость требует сохранённых разрешённых снимков, фиксированной версии parser/taxonomy и seed revision. Если источник запрещает сохранение полного контента, использовать разрешённый фиксированный extract/ручной seed и прямо указывать ограничение воспроизводимости.

## Транзакционная публикация

1. Fetch/parse/normalize выполняются до транзакции.
2. Создаётся и проверяется diff: новые записи, изменения значений, conflicts, retire-кандидаты.
3. В короткой транзакции снять `is_current` у заменяемых claims, вставить/активировать новые, обновить проекции и FTS.
4. Проверить обязательные связи и уникальность; при ошибке откатить публикацию набора.
5. Обновить version только после успешного commit; сохранить отчёт запуска.

Единица атомарности — направление с его опубликованными изменениями либо небольшой явно описанный batch, не частичное поле без provenance. Один невалидный регион не должен ломать весь запуск; run получает `partial` и перечисление неуспешных batches.

## Сеть и сбои

Timeout подключения/ответа, bounded retries с exponential backoff и jitter только для временных сбоев. `429` учитывает Retry-After; если ожидание выходит за бюджет запуска/tool, отложить, а не повторять немедленно. `401/403` — исправить доступ, не перебирать обходные endpoints.

Rate limits и concurrency заданы provider-конфигурацией, учитываются суммарно между процессами при общем runtime-каталоге (локальная блокировка/бюджет). Large responses stream в ограниченный файл, не в память. Ошибка HTML/XML/JSON, пустой обязательный раздел, provider error в HTTP 200 — rejected/review.

Обычный запуск сервера не скачивает каталог заново. Фоновый демон/очередь не нужны: импорт запускает оператор CLI, расписание при необходимости — внешний cron/systemd timer.

## Планируемый CLI

```bash
uv run python -m image2travel seed --dry-run
uv run python -m image2travel seed
uv run python -m image2travel ingest --provider osm --input /path/region.osm.pbf --destination si-bled --dry-run
uv run python -m image2travel ingest --provider wikidata --destination si-bled
uv run python -m image2travel ingest --provider official --destination si-bled --dry-run
uv run python -m image2travel ingest --review-run RUN_ID
uv run python -m image2travel ingest --refresh-due --dry-run
uv run python -m image2travel data-check
```

`--dry-run` не изменяет активный каталог; может сохранять локальный staging/отчёт, что явно документируется. Для полностью read-only сравнения — режим без записи. `--review-run` читает diff и требует явного решения редактора для защищённых изменений. Импорт не выставляется в пользовательский MCP.

## Сквозной пример: смотровая у озера

1. Seed задаёт направление `si-bled`, bbox, страну, timezone, официальный сайт.
2. OSM parser находит viewpoint, OSM ID, координаты и website; запись становится draft.
3. Wikidata при наличии QID добавляет алиасы и географические свидетельства, не выдумывает отсутствующую связь.
4. Wikivoyage listing даёт кандидата длительности/описания; редактор подтверждает, что речь об этой точке.
5. Официальный источник/ручное подтверждение задаёт доступ, цену и сезонные ограничения; при отсутствии hours — unknown.
6. Редактор задаёт `duration_min`, effort, best_time и роль anchor как editorial, не как факт OSM.
7. Publisher в транзакции записывает entity, external IDs, POI, связь направления, claims/evidence и правила.
8. `get_destination` показывает значение с источником/датой/статусом; `build_itinerary` не обещает точный доступ, если вход representative или условия неизвестны.

Названия и числа примера — иллюстрация процесса, не готовый проверенный seed.
