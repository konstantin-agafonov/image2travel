# 08. База данных: практические условия поездки

[Оглавление](README.md) · Далее: [происхождение данных](09-database-provenance.md)

Эти таблицы расширяют [каталог](07-database-catalog.md). Они хранят опубликованные значения; история и доказательства находятся в claims. На каждую строку/поле импорт создаёт утверждение с устойчивым `field_path`.

## Валюты и цены

```sql
CREATE TABLE currencies (
  code TEXT PRIMARY KEY CHECK (length(code) = 3),
  minor_units INTEGER NOT NULL CHECK (minor_units BETWEEN 0 AND 4)
);
CREATE TABLE price_estimates (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  category TEXT NOT NULL
    CHECK (category IN ('lodging', 'food', 'local_transport', 'ticket', 'activity', 'arrival_transport')),
  travel_style TEXT NOT NULL CHECK (travel_style IN ('budget', 'mid', 'comfort', 'any')),
  currency TEXT NOT NULL REFERENCES currencies(code),
  low_minor INTEGER NOT NULL CHECK (low_minor >= 0),
  high_minor INTEGER NOT NULL CHECK (high_minor >= low_minor),
  basis TEXT NOT NULL
    CHECK (basis IN ('person_day', 'room_night', 'vehicle_day', 'person_visit', 'group_trip', 'person_trip')),
  occupancy INTEGER CHECK (occupancy > 0),
  month INTEGER CHECK (month BETWEEN 1 AND 12),
  valid_from TEXT,
  valid_to TEXT,
  includes_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(includes_json)),
  excludes_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(excludes_json)),
  method TEXT NOT NULL,
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from)
);
CREATE INDEX idx_prices_lookup ON price_estimates(entity_id, category, travel_style, month);

CREATE TABLE exchange_rates (
  base_currency TEXT NOT NULL REFERENCES currencies(code),
  quote_currency TEXT NOT NULL REFERENCES currencies(code),
  rate_date TEXT NOT NULL,
  rate_decimal TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(id),
  checked_at TEXT NOT NULL,
  PRIMARY KEY (base_currency, quote_currency, rate_date, source_id)
);
```

`rate_decimal` валидируется положительным `Decimal`; 1 единица base равна rate единиц quote. Не использовать REAL для сумм и валютных расчётов. `occupancy` обязателен для расчёта стоимости комнаты, если цена зависит от числа гостей.

Бюджет направления — совокупность строк, не непрозрачный `budget_json`. Бесплатный вход записывается 0 только при подтверждении; отсутствие цены — отсутствие строки/unknown. Стоимость прибытия зависит от origin и дат, поэтому обычно живёт в runtime-кэше, а не в «вечной цене направления».

Расходы нельзя складывать без `basis`: жильё умножается на ночи и количество комнат, питание — на людей и дни. Количество дней и ночей не равно автоматически. Налоги, сборы и аренда авто явно включены либо исключены.

Provenance: `prices.{id}.low_minor`, `prices.{id}.high_minor`, `prices.{id}.conditions`; если диапазон выведен из нескольких тарифов — derived claim с зависимостями и формулой.

## Правила доступа к местам

```sql
CREATE TABLE access_rules (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  rule_type TEXT NOT NULL
    CHECK (rule_type IN ('closure', 'permit', 'booking', 'mobility', 'transport', 'conduct')),
  severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'blocker')),
  availability TEXT NOT NULL DEFAULT 'unknown'
    CHECK (availability IN ('allowed', 'limited', 'forbidden', 'unknown')),
  condition_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(condition_json)),
  valid_from TEXT,
  valid_to TEXT,
  note TEXT NOT NULL,
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from)
);
CREATE INDEX idx_access_rules_entity ON access_rules(entity_id, rule_type);
```

Пример `condition_json`: месяцы закрытия тропы, обязательность разрешения, применимые способы передвижения, допустимый уровень усилия, правила дронов/костров. Условия валидируются по схемам `rule_type`, а не произвольному языку правил.

Recurring-ограничения хранят месяцы/дни в JSON, конкретное временное закрытие — valid_from/to. Сезонный показатель направления не отменяет закрытие конкретного POI.

OSM `wheelchair=yes` — свидетельство о заявленной доступности, не гарантия безбарьерного маршрута целиком. Неизвестный уклон/лестницы или отсутствие трека блокируют уверенное обещание доступности.

Provenance: `access_rules.{id}`. Идентификатор правила устойчив для одного опубликованного ограничения; новая версия условий создаёт историю claims, не копии активного правила.

## Въезд и безопасность

```sql
CREATE TABLE travel_restrictions (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES entities(id),
  restriction_type TEXT NOT NULL CHECK (restriction_type IN ('entry', 'safety')),
  issuer_country TEXT,
  passport_country TEXT,
  scope_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(scope_json)),
  level TEXT NOT NULL CHECK (level IN ('info', 'caution', 'avoid', 'unknown')),
  valid_from TEXT,
  valid_to TEXT,
  summary TEXT NOT NULL,
  CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from)
);
CREATE INDEX idx_restrictions_lookup
  ON travel_restrictions(entity_id, restriction_type, passport_country);
```

Сущность — страна или направление; допустимость типа проверяется repository. `issuer_country` — кто публикует advisory; `passport_country` — для какого гражданства правило въезда. Это разные оси. `scope_json` содержит регион, длительность, цель визита, транзит и исключения.

Один advisory для граждан другой страны не является юридическим правилом въезда пользователя. В MVP не строить глобальную матрицу виз: хранить подтверждённые сведения только для выбранной географии и явно возвращать unknown для непокрытого случая.

`avoid` исключает направление/зону при действующем применимом подтверждении. Отсутствие advisory не означает `info` или безопасно. Источник и дата нужны перед рекомендацией рискованного природного маршрута.

Provenance: `restrictions.{id}`; все критичные поля публиковать с текущим claim.

## Климатическая статистика

```sql
CREATE TABLE climate_months (
  destination_id TEXT NOT NULL REFERENCES destinations(entity_id),
  month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
  period_start_year INTEGER NOT NULL,
  period_end_year INTEGER NOT NULL CHECK (period_end_year >= period_start_year),
  dataset TEXT NOT NULL,
  temp_mean_c REAL,
  precipitation_mean_mm REAL CHECK (precipitation_mean_mm >= 0),
  wet_days_mean REAL CHECK (wet_days_mean >= 0 AND wet_days_mean <= 31),
  sample_years INTEGER NOT NULL CHECK (sample_years > 0),
  source_id TEXT NOT NULL REFERENCES sources(id),
  computed_at TEXT NOT NULL,
  PRIMARY KEY (destination_id, month, period_start_year, period_end_year, dataset)
);
```

Агрегация исторических рядов/реанализа — «статистика за указанный период», не обязательно официальная климатическая норма и не прогноз. Wet day имеет явный порог, например precipitation ≥ 1 мм/сутки. Метод и полнота ряда — derived claim `climate.{dataset}.{period}.{month}`.

Текущий прогноз и расчётные переезды — `api_cache`, потому что зависят от координат, дат и транспорта. Полные GTFS-таблицы не входят в схему MVP; выбранные ручные транспортные факты — claims/access_rules, а расписание в полном объёме — отдельное будущее расширение.
