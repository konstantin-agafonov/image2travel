# Image2Travel — план реализации

План разделён на **21 логическую часть** в папке [`plans/`](plans/README.md). Каждая часть находится в отдельном Markdown-файле.

**Идея:** превратить изображение в выполнимый план путешествия, который сохраняет впечатление — свет, тишину, ритм, активность и сезон, а не только похожий пейзаж.

**MVP:** skill + локальный MCP-сервер на Python, SQLite, локальные файлы; host-агент отвечает за vision и диалог, сервер — за данные, подбор и расчёты.

## Навигация

- [Полное оглавление и общие договорённости](plans/README.md)
- [Продукт и границы MVP](plans/01-product-and-mvp.md)
- [Пользовательский сценарий](plans/02-user-journey.md)
- [Контракты: Experience Fingerprint и TripBrief](plans/03-domain-contracts.md)
- [Архитектура](plans/04-architecture.md), [MCP](plans/05-mcp-server.md), [skill](plans/06-skill.md)
- **Структура БД:** [каталог](plans/07-database-catalog.md), [практические данные](plans/08-database-travel-data.md), [источники, факты, импорт и кэш](plans/09-database-provenance.md)
- **Наполнение БД:** [источники](plans/10-data-sources.md), [парсинг географии/POI](plans/11-parsing-geography.md), [парсинг практических данных](plans/12-parsing-travel-data.md), [конвейер импорта](plans/13-ingestion-pipeline.md)
- [Seed и ручная разметка](plans/14-seed-and-curation.md), [качество и обновление](plans/15-data-quality-and-refresh.md)
- [Подбор направлений](plans/16-destination-matching.md), [маршрут и валидация](plans/17-itinerary-and-validation.md)
- [Ответ и экспорт](plans/18-response-and-exports.md), [безопасность](plans/19-security-and-privacy.md)
- [Тесты и оценка](plans/20-testing-and-evaluation.md), [этапы реализации и запуск](plans/21-delivery-and-roadmap.md)

Документы описывают будущую реализацию. Команды, SQL-схемы и примеры не означают, что приложение, парсеры или каталог уже созданы.
