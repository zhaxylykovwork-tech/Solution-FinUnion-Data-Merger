# DWH на PostgreSQL и Lakehouse

| Аспект | PostgreSQL DWH | Iceberg Lakehouse |
|---|---|---|
| Роль | Проверенные отношения, витрины, report versions, точное закрытие | История/события/raw→curated, широкие сканы и исследования |
| Транзакционная граница | SQL-транзакция БД; можно атомарно активировать publish_version | Iceberg commit/snapshot таблицы; согласованность нескольких таблиц требует pinned publish manifest |
| Модель | Conformed core, SCD2 dimensions, звезда и снимки остатков | Parquet files + Iceberg schemas/metadata/partition evolution |
| Запросы | Сертифицированные BI/report SQL на выделенном read endpoint | Trino с ресурсными группами/лимитами; Spark для больших batch transforms |
| Доступ | SQL roles/RLS/column masking | SQL engine ACL плюс bucket/service roles и catalog auth; обход engine прямым доступом к файлам запрещён |
| Уход | Index/vacuum/partition/backup, performance и capacity | Compaction, snapshot expiration, orphan cleanup, catalog backup и restore, small-file контроль |

На 3 месяца: PostgreSQL DWH + закрытый raw landing для воспроизведения; Lakehouse не обязателен для первой отчётности. На 12: DWH остаётся для утверждённых финансовых/регуляторных срезов, Lakehouse принимает многолетние архивы, карточные и канальные события. DWH хранит необходимую детализацию для сверки и выбранный горячий горизонт; точный горизонт определяется retention/нагрузкой. Удалённая из горячего DWH история остаётся доступной только по утверждённому архивному процессу.

Iceberg — формат и метаданные таблиц, а не object storage и не отдельная SQL СУБД. S3-compatible storage хранит файлы. REST catalog управляет указателями и атомарностью metadata commits; отдельно выбирается поддерживаемая реализация с HA/backup. Trino — SQL engine, Spark — batch compute. DataHub хранит описание/lineage/ownership, не заменяя transactional catalog. Основания: [Iceberg docs](https://iceberg.apache.org/docs/latest/), [Trino connector](https://trino.io/docs/current/connector/iceberg.html).

## Распределение и единые показатели

1. Финансовые postings из Core → DWH — канонический расчёт оборота и остатка. Полная копия истории может храниться в Iceberg для исследования, с тем же posting key; она не добавляется второй раз в общий отчёт.
2. Cards authorization/clearing events → Lakehouse — анализ поведения, отказов, исторических рисков. Финансовый факт операции берётся из ledger, связь по external/clearing reference и версии mapping.
3. Customer/reference dimensions → Hub → DWH/Lakehouse как versioned projections; прямое независимое «исправление клиента» в Iceberg запрещено.
4. Curated risk/channel aggregate → DWH только с product contract, `snapshot_id + source watermark + metric_version` и сверкой. DWH не экспортирует агрегат в Lakehouse с последующим возвратом того же факта под другим ID.

Для каждого publish manifest фиксируются snapshots всех входных таблиц, transform Git SHA, версия справочников, календарь, watermark, DQ result и row counts. «Оборот» имеет одну формулу из Ledger Daily; исследовательские метрики имеют отдельные имена и experimental status. Несовпадение Trino и DWH проверяется на одинаковом as_of/наборе ключей/валюте, а не сравнением случайных totals.

Ограничения: эксплуатационная сложность двух контуров, стоимость репликации и возможное устаревание копий; Iceberg snapshot не равен неизменяемому legal archive; schema evolution не устраняет семантическое изменение. Physical erasure должен учитывать старые snapshots и backup. Конкретную совместимую версию engines/catalog и поддержку delete/evolution проверяют на trial перед production. Отказ от графа/OpenSearch/Flink на первом этапе уменьшает число вторичных копий и обязанностей сопровождения.
