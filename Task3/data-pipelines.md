# Пайплайны и большие данные

Все pipelines имеют owner, input contract/schema, manifest/watermark, source→target lineage и immutable run_id. Retry повторяет чтение и вычисление, не банковскую команду. Ниже интервалы и SLA — проектные цели из Task2.

| ID / срок | Источник → приёмник | ETL/ELT, инструменты, преобразование | Частота / owner | Ошибка и условие публикации |
|---|---|---|---|---|
| P1 / 3м: простой PostgreSQL DWH | FU/RB Core exports + Hub dimensions → PG staging → core → marts | **ELT**: Airflow получает CSV+manifest по защищённому каналу; COPY в staging; SQL нормализует codes, decimal/currency, bank_date, as-of keys; формирует postings и daily account snapshot | Hourly, закрытие D+1 до 08:00 / Finance+DWH | Нет manifest или разница counts/totals → срез не publish. `batch_id` unique, load в shadow transaction, atomic publish_version, checkpoint после сверки |
| P2 / 3м: Customer Hub | CRM verified events/batch → Hub → CRM projections/DWH | **ETL**: integration worker проверяет/нормализует до gold, matching, survivorship, crosswalk; PostgreSQL Hub + outbox; Airflow для initial/backfill | Непрерывно, до 5 мин при events; hourly projection в DWH / Customer | Неоднозначность → review; неверная schema → quarantine; event_id и version защищают от дубля; только approved gold публикуется |
| P3 / 6–9м: история карт | FU/RB Cards events/archives → raw object → Iceberg curated | **ELT**: Kafka→raw writer, Spark batch нормализует status/event type и dedup по origin event key; Iceberg snapshot; Trino читает curated | Microbatch 15 мин; archived backfill nightly / Cards+Risk | Late/out-of-order не меняет posted ledger; missing sequence в quarantine и alarm; publish manifest pin source offsets+snapshot |
| P4 / 9–12м: события каналов | FU web/mobile gateway events → Kafka → raw → curated Iceberg → агрегат DWH | **ETL/ELT**: producer минимизирует ПДн, Spark очищает bot/duplicate/session events, purpose-фильтр и агрегаты; Trino exploration; Airflow batch export согласованных KPI | Microbatch 15 мин, daily KPI / Channel Owner | Нет основания на цель → исключить из целевого использования; проверка completeness/dedup; KPI с metric_version, raw не доступен BI |
| P5 / 3–12м: закрытый финансовый пакет | DWH core/marts → versioned report snapshot → подписанный export | **ETL**: Airflow+SQL создают фиксированную версию по Finance-approved mapping, control totals; export job шифрует/подписывает и ждёт transport ack | По банковскому календарю / Finance Reporting | Нет sign-off или mismatch → hold; повтор доставки имеет тот же package_id, не новый отчёт. Исправление после отправки — новая корректирующая версия по процессу |

## P1: исполнимый алгоритм обработки, без вымышленного connector

1. Export job источника согласует согласованный T0/commit watermark, отдаёт files и manifest. Если нет log CDC, extract contract обязан включать inserts/updates и deletion ledger между from/to; один updated_at недостаточен.
2. Airflow сначала проверяет размер/hash/schema/непрерывность диапазона и регистрирует batch как RECEIVED. Raw файл сохраняется по закрытой retention policy.
3. COPY в staging с `source_bank, source_system, source_key, source_version, batch_id`. Проверяются unique keys, decimal precision, обязательные поля, count и totals по currency/date; rejected rows имеют reason и сохраняются.
4. SQL upsert в shadow core по ключу источника и версии; финансовое исправление сохраняет original/reversal linkage. Dimensions загружаются до facts, неразрешённый customer получает unknown key с quality flag. Проводки не удаляются inner join.
5. Отдельные tests проверяют баланс ledger_transaction_id по валюте и source totals на одинаковом watermark, затем строят marts. В одной транзакции переключается запись published_version и фиксируется checkpoint. Потребители читают только её, а не промежуточные таблицы.
6. Если процесс упал до switch, старая published version работает; retry использует batch_id и не удваивает строки. Если switch успел commit, повтор распознаёт PUBLISHED. Коррекция схемы создаёт новый transform_version и shadow rerun с теми же исходными ключами.

Этот алгоритм проектный, промышленный DAG/коннекторы не реализованы: реальная схема источников и credentials неизвестны. [Синтетическая проверка](../tools/validate.py) проверяет важные расчётные инварианты аналитической модели, а не заявляет интеграционное испытание банка.

## Два сценария Big Data

| Сценарий | Источник / характер | Storage / обработка | Потребители и результат |
|---|---|---|---|
| История карточных операций | Два Cards: многолетние архивные выгрузки и поток authorization/clearing; события и полуструктурированные attributes | Immutable raw на object storage с manifests; batch исторический import и microbatch текущих событий; Spark ELT → Iceberg; partition по event_date с benchmark bucket/card token | Risk/антифрод аналитика, исследование частоты отказов; Trino SQL. Online authorization не зависит от этого контура; проводки сверяются отдельно |
| Поведение в клиентских каналах | FU/RB web/mobile/gateway: event_time, session_token, action, channel, product code; pseudonymous events | Kafka streaming transport → raw → 15-мин Spark microbatch → Iceberg session aggregates; daily KPI ELT в DWH после DQ | Channel BI и product owners: воронка, adoption продуктов FU клиентами RB; доступ зависит от цели, отчёт содержит completeness и as_of |

Объёмы/скорости не заданы, поэтому термин Big Data здесь означает архитектурный сценарий масштабируемой истории, а не выдуманные петабайты. Trial измеряет объём в сутки, bytes per event, cardinality, late-event distribution, стоимость годового хранения и scan/runtime. Stateful millisecond fraud detection потребует отдельного SLA и архитектуры; этот проект такого обещания не делает.

## Общие правила backfill и поздних событий

Backfill идёт отдельной квотой, source transactions не задерживаются. Одинаковые данные в snapshot и CDC дедуплицируются по source key/version/position с учётом consistent T0. Late event входит в текущую незакрытую версию с as-of dimension; для закрытого периода открывает exception и корректирующий отчёт. В Lakehouse пересчитывается затронутый partition/snapshot, а downstream получает новый product_version. Schema breaking change блокирует writer до контрактного согласования. DQ thresholds для финансовой полноты — нулевое необъяснённое расхождение, для event telemetry допустимый процент пропусков утверждается отдельно и виден потребителю.
