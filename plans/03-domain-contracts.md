# 03. Доменные контракты

[Оглавление](README.md) · Далее: [архитектура](04-architecture.md)

## Experience Fingerprint

Host извлекает сцену, вероятную географию, свет, время суток, сезон, активность, сенсорику, социальность, темп, усилие, эмоции, визуальный стиль и культурные маркеры.

Сенсорика вне видимого — интерпретация: по фото нельзя подтвердить запах, температуру, звук или фактическое отсутствие толпы за кадром.

```json
{
  "schema_version": "1.0",
  "summary": "Тихое горное утро у воды",
  "visible_facts": ["озеро", "хвойный лес", "туман", "мягкий свет"],
  "inferred": {
    "season": "late_spring",
    "time_of_day": "sunrise",
    "weather": "cool_calm",
    "crowd_level": "low"
  },
  "experience": {
    "emotions": ["calm", "solitude", "awe"],
    "pace": "slow",
    "effort": "easy",
    "social": "private",
    "sensory": {
      "sight": ["soft_light", "open_space"],
      "sound": ["water", "quiet"],
      "smell": ["conifers"],
      "temperature": "cool"
    }
  },
  "must_preserve": ["вода на рассвете", "мало людей", "лёгкая прогулка"],
  "nice_to_have": ["деревянный причал", "вид из окна"],
  "avoid": ["шумные экскурсии"],
  "location": {
    "candidate": "озеро в Альпах",
    "confidence": 0.6,
    "evidence": ["силуэт гор", "растительность"],
    "needs_verification": true
  }
}
```

Контролируемый словарь хранится в `src/image2travel/data/taxonomy.yaml`, версия передаётся в схемах. Неизвестные описания допустимы в свободном тексте; автоматический матчинг использует только нормализованные теги. `must_preserve` дополняется структурированными условиями, если его можно вычислить: `landscape=lake`, `time_of_day=sunrise`, `effort=easy`.

## TripBrief — единый вход

```json
{
  "schema_version": "1.0",
  "fingerprint": {
    "schema_version": "1.0",
    "summary": "Тихое горное утро у воды",
    "visible_facts": ["озеро", "лес"],
    "inferred": {"time_of_day": "sunrise"},
    "experience": {"emotions": ["calm"], "pace": "slow", "effort": "easy"},
    "must_preserve": ["вода на рассвете"],
    "nice_to_have": [],
    "avoid": []
  },
  "constraints": {
    "origin": "Москва",
    "start_date": "2027-05-10",
    "days": 5,
    "travelers": 2,
    "budget": {"amount": "2400.00", "currency": "USD", "scope": "group", "includes": "total"},
    "mode": "twin",
    "passport_country": null,
    "transport_modes": ["car", "walk"],
    "max_travel_hours": null,
    "mobility_requirements": []
  }
}
```

- Дни: 1–7, путешественники: положительное целое, confidence: 0–1.
- Дата — ISO 8601; неизвестную дату заменять не фиктивной датой, а `preferred_month` и допущением. Прошлую дату для будущей поездки отклонять понятной ошибкой.
- Деньги: десятичная строка в API, `Decimal` в Python, целое число минимальных денежных единиц в БД; число знаков задаёт справочник валют, не всегда два.
- `budget.scope`: `person` / `group`; `includes`: `total` / `on_site`. Поля исключают неоднозначность исходного `budget_usd`.
- Паспорт и мобильность — добровольные входные данные, не постоянные записи БД.

## Результаты

`PlanProposal`: `concepts` (0–3), `questions`, `assumptions`, `warnings`, `data_version`. Карточка: ID, роль, оценки компонент, причины, потери, сезон, бюджет, покрытие данных и confidence.

`Itinerary`: brief, направление, timezone, дни, блоки активностей, переезды, расходы, план B, источники, дата расчёта и версия каталога. Не требует ID сохранённой поездки.

`ValidationReport`: статус `valid` / `needs_review` / `invalid`, ошибки, предупреждения, непроверенные условия и feasibility score. Число не отменяет критичный blocker.

## Статусы утверждений

Каждое возвращаемое важное значение сопровождается `claim_id`, `source_url`, `checked_at`, `valid_from/to`, статусом `verified` / `editorial` / `estimated` / `unknown` / `conflicting` / `stale`. Для расчётов — метод, версия и ссылки на входные факты. `verified` означает проверку утверждения, не гарантию события в будущем.

`exact` разрешается только при согласованной географической проверке и убедительных визуальных признаках. Две ссылки на один объект сами по себе не доказывают место съёмки; копирующие друг друга страницы не независимы.
