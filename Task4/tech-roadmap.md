# Технологическая дорожная карта

Зоны показывают решение для данного кейса. Adopt означает целевое применение с приёмкой, не существующий факт внедрения. Trial имеет критерий входа/выхода. Assess не создаёт production-зависимости. Hold запрещает добавление в текущий охват без нового обоснования.

| Зона | Технология / подход | Почему / ограничения | Срок, зависимость, результат |
|---|---|---|---|
| Adopt | MDM Customer/Reference Hub с PostgreSQL, match/review/outbox | Common ID и эталонные справочники; не мастер платежей. Custom vs vendor оценивается discovery по сложности/поддержке | М1–3 после profiling; unique crosswalk и утверждённый gold, restore/unmerge |
| Adopt | Отдельный PostgreSQL DWH + SQL transforms в Git | Быстрый единый отчёт, ACID publish, простые сверки; capacity ограничена и измеряется | М2–3; P1 и certified marts, p95/load/restore gates |
| Adopt | Airflow | Batch dependencies/backfill/контроль запуска, без streaming через scheduler | М2–3; versioned DAG/run manifest, alerts и retry |
| Adopt | DataHub | Каталог и lineage с ownership, sensitivity; не enforcement БД и не Iceberg commit catalog | М1–3 critical assets, М4–12 расширение; owner/lineage до publish |
| Adopt | Существующий ESB/API adapters, schema contracts | Синхронные банковские команды и контролируемые адаптеры, reuse FU landscape | М1–3; canonical mappings без аналитики в online path |
| Trial → Adopt | Kafka + source-native CDC / outbox | Replay и разрыв связанности, но нагрузка и гарантии конкретного источника неизвестны | М2–4 trial по CRM/одному source, М4–6 распространение; fail/replay/retention/load test. Fallback batch не блокирует M3 |
| Adopt | Private object storage + manifests/retention | Документы и snapshots/replay; шифрование/ключи, lifecycle и retrieval обязательны | М1–3 landing, М4–12 archive; restore/erasure/ACL gates |
| Trial → Adopt | Iceberg + Parquet + Trino + REST catalog | Открытые аналитические таблицы и отдельный SQL compute; вводится только после испытаний compatibility/backup/maintenance | М4–7 trial → М7–10 historical products; pinned snapshots, compaction, cost и DQ |
| Trial → Adopt | Spark batch/microbatch | Большие архивные transforms, повторяемость; новый operational burden | М5–7 после подтверждения объёма; throughput/cost/late data тест, затем P3/P4 |
| Assess | Vendor MDM / поддерживаемый managed stack | Снизить custom match/workflow burden; нужно сравнить лицензии, residency, интеграции и компетенции | М1 decision gate, не переносить выбор после критичного срока M3 |
| Assess | dbt | Полезен для сложного SQL lineage/tests; сначала достаточно versioned SQL и Airflow | М3–5 после роста моделей; не вводить второй дублирующий DAG |
| Assess | Flink | Stateful low-latency обработка при доказанной бизнес-потребности; microbatch покрывает текущие аналитические цели | М7–9 benchmark только если 15мин недостаточно; отдельный SLA/ресурсы |
| Assess | Graph database | Многозвенные расследования, если SQL edge dataset не проходит benchmark | После М6; измеримый графовый сценарий, ACL и качество matching |
| Assess | Columnar/MPP DWH | Если PG не выдержит объём/latency/maintenance window | М4–6 по capacity forecast; оценка query profile/TCO и миграционного риска |
| Hold | Полный Data Mesh | Усложнит унификацию при неизвестной зрелости; используем 4 продукта и общую платформу | Пересмотр после М12 при зрелом ownership/self-service |
| Hold | Сырые ПДн в OpenSearch | Лишняя чувствительная копия и сложность ACL/delete; штатный CRM поиск достаточен для MVP | Пересмотр по measured search case после redaction/access/delete trial |
| Hold | Big-bang RB migration; MDM для финансовых фактов | Нарушает непрерывность и границы авторитета | На всём горизонте; только поэтапный gated cutover |

Критический путь 3 месяцев: discovery/owners → matching и reference mapping → reconciled DWH → parallel run → reporting cutover. Kafka/Lakehouse не блокируют эту цепочку при безопасном batch fallback. Путь 12 месяцев: product/legal readiness → master switch по когортам → полный расчётный цикл → archive/retrieval → decommission. Lakehouse параллелен продуктовым волнам, но не заменяет их.

До trial оцениваются компетенции source DBA, platform/on-call, data engineering, KYC stewardship и Finance reconciliation. Бюджет и численность команды в кейсе не известны. Если нет ответственного за эксплуатацию catalog/Kafka/Spark, компонент не проходит production gate; обучение, поддержка поставщика либо сокращение технического охвата должны быть явным решением программы. Первичные описания механизмов доступны в [SOURCES](../SOURCES.md).
