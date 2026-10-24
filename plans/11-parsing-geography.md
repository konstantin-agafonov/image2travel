# 11. Парсинг географии, направлений и POI

[Оглавление](README.md) · Далее: [практические парсеры](12-parsing-travel-data.md)

## 1. OSM: основной массовый импорт

### Откуда

Региональный `.osm.pbf` из [Geofabrik](https://download.geofabrik.de/), выбранный по географии стартового каталога. PBF — локальный вход importer, не отдельный постоянно работающий сервис. Для небольших обновлений — разрешённый провайдер Overpass. Публичный Overpass не является гарантированным бесплатным backend продукта.

### Как

1. Редактор задаёт bbox/полигон для направления и список нужных категорий.
2. Потоковый parser (`pyosmium` либо предварительная фильтрация `osmium`, выбранная реализацией) отбирает объекты. Не загружать весь PBF в память.
3. Категории: `tourism=viewpoint/museum/information`, `natural=peak/beach/water`, `leisure=park/nature_reserve`, `amenity=cafe/restaurant`, разрешённые точки доступа и начала маршрутов.
4. Сохранять `name`, локализованные name/alt_name, `tourism`, `natural`, `amenity`, `opening_hours`, `access`, `foot`, `wheelchair`, `fee`, `website`, `contact:website`, `wikidata`, `wikipedia`, `ele`.
5. Node имеет point; way/relation требует сборки геометрии. Центр/представительная точка маркируется `representative`; вход ищется отдельно. Неполная геометрия — review, а не случайные координаты.
6. Перевести теги в нормализованную категорию и детерминированные теги ландшафта/активности. `natural=water` не гарантирует `lake`: учитывать water=lake и контекст.
7. Отфильтровать private/no/закрытые и чувствительные точки; сохранить причину. `access=permissive`/условный доступ не превращать в безусловное разрешение.
8. Разрешить дубликаты, связать существующий entity по OSM ID, создать кандидатов в ingestion_items.
9. После review публиковать выбранные 10–15 POI, не все кафе внутри bbox.

### Пример малого запроса Overpass

```overpass
[out:json][timeout:25];
(
  nwr["tourism"="viewpoint"](46.30,14.00,46.42,14.20);
  nwr["amenity"="cafe"](46.30,14.00,46.42,14.20);
);
out meta center;
```

Bbox и категории берутся из проверенной конфигурации, не из произвольной строки пользователя. `out meta center` даёт версию/timestamp и центр way/relation; этот центр не использовать как гарантированную точку доступа. Сохранять также `timestamp_osm_base` всего ответа. Обрабатывать error/remark даже при HTTP 200; неполный ответ не публиковать как полный.

### Куда в БД

`sources` (URL dataset/объекта) → `source_snapshots` (hash/revision) → `ingestion_items` → `entities`, `external_ids`, `pois`, `destination_pois`, `entity_tags`. Каждое опубликованное поле сопровождается claim и evidence locator вроде `tags.opening_hours`.

Удаление объекта из ответа не означает закрытие: причиной может быть фильтр/лаг/неполнота. Retire — отдельное подтверждённое решение.

## 2. Wikidata: связь имён, стран и внешних ID

### Откуда

Из OSM `wikidata=Q...` или редакционного seed. Если QID неизвестен — ограниченный `wbsearchentities`; кандидат не принимается автоматически только по похожему названию.

Пример получения уже известной сущности:

```text
GET https://www.wikidata.org/wiki/Special:EntityData/Q1527.json
```

Для малых групп использовать Action API `wbgetentities` с необходимыми props; масштабные выборки — dump, а не бесконечный SPARQL-запрос. User-Agent и `maxlag`/Retry-After обязательны по подходящим API-политикам.

### Что парсить

Labels/aliases RU/EN/местного языка; P625 (координаты), P17 (страна), P131 (административный регион), P31 (тип), P856 (официальный сайт), sitelinks. У statements сохранять rank, qualifiers и references. Deprecated statements не принимать, `novalue`/`somevalue` не превращать в строковое значение.

Не переносить координату центра города как координату причала. Если данные расходятся с OSM, сравнить тип объекта, precision, регион и первоисточник; отправить в review.

### Куда

`external_ids`, country/destination geography, aliases в claims/search-проекции, source snapshots и field-level evidence. Официальная ссылка из P856 — кандидат на allowlist, не разрешение автоматически скачивать любой найденный URL.

## 3. Wikivoyage: listings и туристический контекст

### Откуда

Реестр содержит конкретную языковую страницу, например `en:Bled`. Получать wikitext через MediaWiki API, не HTML всего сайта:

```text
GET https://en.wikivoyage.org/w/api.php
  ?action=query&prop=revisions&titles=Bled
  &rvprop=ids|timestamp|content&rvslots=main
  &redirects=1&format=json&formatversion=2
```

Параметры кодируются HTTP-клиентом. Сохранять pageid, revid, timestamp, canonical title; missing/redirect/continuation обрабатывать явно. Для воспроизводимого повторного парсинга использовать сохранённую revision.

### Как

`mwparserfromhell` разбирает шаблоны `see`, `do`, `eat`, `sleep`, `listing` и поддержанные языковые варианты. Не regex по всему wikitext. Извлекать name, lat/long, address, url, hours, price и короткий контекст с номером секции/шаблона.

Строки hours/price — **кандидаты**: язык, валюта, сезон, дата и условия часто неоднозначны. Листинг не задаёт актуальный тариф без повторной проверки оператора. Неструктурированную прозу использовать для редакционного review, не машинного утверждения о безопасности.

### Куда

Staging-кандидаты POI, claims с evidence `template:see[n].hours`, ссылки на страницу/revision, лицензионные метаданные. Связать с OSM/Wikidata по внешнему ID, затем по категории+координатам+сайту. Окончательный выбор точек и summary — редактор.

## 4. Проверка предполагаемого места

`verify_place` использует эти же данные, но не запускает массовый импорт. Проверяет название/регион/географию кандидата, показывает свидетельства и границы точности. Подтверждение существования озера не доказывает, что фото снято именно там.

Если потребуется геокодер, выбрать договорного/собственного провайдера. Публичный [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/) требует отдельного осознанного решения разработчика: максимум 1 req/s по всему приложению, идентифицирующий User-Agent, кэш, запрет autocomplete и систематического сбора POI, дополнительные ограничения bulk/периодических запросов. Поэтому по умолчанию он выключен.
