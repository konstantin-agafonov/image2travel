# 05. MCP-сервер

[Оглавление](README.md) · Далее: [skill](06-skill.md)

## Tools

Сохраняем имена исходного плана как публичный контракт сервера `image2travel`; при агрегации host может добавлять namespace. Изменять имена только вместе с версией skill.

| Tool | Вход | Результат |
|---|---|---|
| `plan_trip` | TripBrief | До трёх концепций, причины, вопросы, допущения |
| `get_destination` | ID, месяц опционально | Карточка, POI, факты и их происхождение |
| `build_itinerary` | TripBrief, destination_id | Структурированный маршрут, смета, план B |
| `validate_itinerary` | Полный Itinerary | Blockers, warnings, unknowns, feasibility |
| `verify_place` | Название либо координаты, контекст региона | До пяти кандидатов, свидетельства, confidence |
| `export_itinerary` | Itinerary, markdown/ics/geojson | Контент, file_id, resource URI, expires_at |

Первый сквозной прототип — три tools: подбор, построение, валидация. Остальные входят в завершённый MVP.

## Поведение

- Вход и выход валидируются Pydantic, публикуются `inputSchema` и `outputSchema`.
- JSON — основной результат; для совместимости сериализованный результат также доступен как text content. Не возвращать весь каталог.
- `plan_trip` объединяет фильтрацию, скоринг и диверсификацию; не заставляет host вызывать tool на каждое направление.
- Лимиты на строки, коллекции и размер Itinerary. Детали POI выдавать с `limit`/cursor при необходимости.
- Аннотации должны отражать фактические эффекты: экспорт создаёт файл, а инструмент с записью кэша не объявлять абсолютно read-only. Без разрушительных пользовательских операций.
- `verify_place` ищет сначала локально; сетевой поиск ограничен предметной географией. Это не универсальный публичный geocoding proxy.
- Bulk-import, SQL, произвольный URL и файловый путь не экспонируются как tools.

## Ошибки

Неверная дата/ID/бюджет — исправимая tool execution error с кодом, объяснением и next action. Неизвестный tool или испорченный JSON-RPC — протокольная ошибка SDK.

При неполных данных `plan_trip` возвращает вопросы и допущения. При недоступности провайдера — частичный результат с `unknown`/`stale`, а не придуманное значение. Если невозможно построить безопасный маршрут — результат с blockers, не «успех».

## Resources

`image2travel://schemas/experience-fingerprint`, `.../trip-brief`, `.../itinerary`, `image2travel://destinations/{id}`, `image2travel://sources/{id}`, `image2travel://files/{id}`, `image2travel://methodology`.

Resource источника возвращает метаданные, лицензии и поддержанные факты, не обязательно весь чужой контент. Файловый resource проверяет TTL и принадлежность пути runtime-каталогу.

## Prompts

`plan_from_photo`, `refine_plan`, `explain_tradeoffs` — дополнительные шаблоны. Основной workflow остаётся в skill, поскольку возможности клиентов различаются.

## Stateless по пользовательским поездкам

Сервер можно перезапустить между подбором и построением: host передаст brief и ID заново. SQLite хранит каталог, происхождение данных, кэш и метаданные экспортов, но не аккаунты, фотографии или историю диалога.

## Документация перед реализацией

- [MCP tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [MCP stdio](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP](https://gofastmcp.com/)

Эти ссылки не заменяют матрицу совместимости выбранных закреплённых версий.
