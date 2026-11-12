# Матрица покрытия требований

Требования финальной страницы сдачи спринта 6 сверены 12.11.2026. Здесь приведены результаты решения, без копии текста курса. Публикация репозитория и подтверждение отправки фиксируются отдельно после выполнения соответствующих действий.

| Требование | Артефакт / проверка |
|---|---|
| Не менее 10 сущностей, атрибуты/связи/источники/критерий/DQ | [16 сущностей](Task1/entities.md), E01–E16 |
| Логическая модель клиентов, счетов, договоров, продуктов, операций, обращений | [ERD: 2 листа + ключи/кардинальности](Task1/logical-data-model.md) |
| Классификация и защита | [Все E01–E16 и жизненный цикл копий](Task1/data-classification.md) |
| OLTP/MDM/DWH/Lakehouse/object/graph/search | [Стратегия и обоснованный отказ](Task1/storage-strategy.md) |
| BIAN-маппинг 8–10 сущностей, смысл использования | [10 сопоставлений, версия 13, роли и пересечения FU/RB](Task1/reference-model.md) |
| Мастера 3/12м, источник/создание/MDM различены | [16 строк и правило master epoch](Task2/master-systems.md) |
| Owner, Steward, Producer, Consumer, изменение, DQ | [Ownership + attribute authority + matching](Task2/data-ownership.md) |
| DFD на 3м со всеми восемью source systems/Hub/Integration/DWH/BI/DataHub/регулятором | [L0 + L1](Task2/README.md), F01–F20 |
| Create/Read/Update/Delete/Enrich/Validate/Aggregate | [Операции потоков](Task2/data-flows.md), tombstones≠удаление ledger |
| Режимы/форматы/частота/SLA/owner/DQ/security/monitoring | [Таблица и delivery/runbook](Task2/data-flow-management.md) |
| Не менее 5 проблемных зависимостей | [10 зависимостей с контролями и владельцами](Task2/data-dependencies.md) |
| To-Be 12м и все рассматриваемые компоненты | [Целевая схема и контуры](Task3/target-data-architecture.md) |
| PostgreSQL DWH/Lakehouse/Data Mesh: ≥3 подхода | [Сравнение и выбор гибрида](Task3/architecture-options.md) |
| Роли Iceberg/Trino, данные/ограничения 3/12м | [DWH/Lakehouse](Task3/dwh-lakehouse.md) |
| ≥4 pipelines, простой PG pipeline на 3м | [P1–P5, P1 алгоритм загрузки/публикации](Task3/data-pipelines.md) |
| 1–2 Big Data сценария с источником/storage/обработкой/consumers | [История карт и канальные события](Task3/data-pipelines.md) |
| Звезда/снежинка и OLAP-обоснование | [Звезда проводок, SCD2, суммы/FX/reversal/late events](Task3/analytical-model.md) |
| 3–5 доменных продуктов, связь BIAN/владельцы/потребители | [DP1–DP4 и контракты](Task3/data-products.md) |
| Какие системы остаются/выводятся, данные/потоки/завершение | [Exit gates по системам](Task4/migration-target-state.md) |
| План ≥6 этапов | [M1–M8 и протокол каждой волны](Task4/migration-plan.md) |
| Cutover: подготовка/freeze/выгрузка/load/сверка/route/fallback/monitoring | [15 шагов C01–C15, критичный домен отчётности](Task4/cutover-plan.md) |
| Риски/влияние/вероятность/митигация | [14 рисков, сигналы/действия/owners](Task4/migration-risks.md) |
| Tech radar/roadmap по зонам и причины | [Adopt/Trial/Assess/Hold и сроки](Task4/tech-roadmap.md) |
| Непрерывность и финансовая корректность | [Ограничения](README.md), one writer/epoch, публикация только после сверки, forward repair после финансового commit |
| Формат Markdown, Task1–Task4 README, допустимые редактируемые схемы | Автоматическая проверка обязательных файлов/ссылок и Draw.io XML в [validate.py](tools/validate.py) |
| Обоснование каждой технологии/отказа | [Storage](Task1/storage-strategy.md), [альтернативы](Task3/architecture-options.md), [roadmap](Task4/tech-roadmap.md), [источники](SOURCES.md) |
| Публичный GitHub Solution-FinUnion-Data-Merger и PR во вкладке Ревью | Требует внешней публикации и подтверждения платформы; локальное создание файлов не считается сдачей |

После подтверждённой отправки решение фиксируется до замечаний ревьюера. Матрица не утверждает выполнение реальной банковской миграции или испытаний production-систем.
