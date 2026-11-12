# Управление потоками

Сроки ниже — предлагаемые SLO/SLA при согласованном профиле, а не измеренные возможности неизвестного legacy. Freshness измеряется от commit/effective event источника до доступности проверенной версии. Для batch отдельно измеряются задержка получения и duration; сверка полноты не подменяется низким lag. Полный профиль source→destination/entity/action/mode задан в [реестре](data-flows.md); ключ ID связывает таблицы и DFD.

| Потоки | Формат / частота / обмен | Цель SLA | Владелец | DQ и публикация | Безопасность / мониторинг |
|---|---|---|---|---|---|
| F01–F02 | Versioned JSON events непрерывно; fallback encrypted CSV+manifest каждые 5 мин, async/batch | 95% клиентских обновлений ≤5 мин при доступном CDC/events; batch ≤15 мин | Customer Owner + Integration team | Тип, source key, verified fields, consent scope; quarantine | B из Task1; lag, input=accepted+rejected, конфликтные matches |
| F03–F04 | Source-native CDC envelope; fallback CSV+manifest hourly | До hourly mart ≤2 ч; закрытый день до 08:00 банковской зоны D+1 | Accounting Owner + Core teams | Count, debit/credit totals по валюте/дню; ни одного необъяснённого пропуска | Read-only extraction; WAL/journal retention, source CPU, gap offsets, reconcile differences |
| F05–F06 | Token-only JSON/CSV; microbatch 15 мин | ≤30 мин | Cards Owner | State mapping, token uniqueness, account links; authorization≠posting | Отдельная процессинговая зона; lag, invalid transitions |
| F07–F08 | Versioned CSV/JSON + control totals hourly | ≤2 ч | Loans Owner | Principal/interest/schedule version и currency; нет молчаливой подстановки | Restricted financial role; totals, rejected loans, missing schedules |
| F09 | JSON envelope; async непрерывно | Проверенная golden update ≤5 мин после приёма; review ≤1 рабочий день как цель | Customer Owner / steward | Детерминированный match, conflict queue, uniqueness crosswalk | Закрытая matching зона; backlog age, false merge incidents |
| F10–F11F–F11R | JSON schema + outbox; async непрерывно | CRM projection ≤5 мин от approved Hub commit | Customer + CRM owners | Версия/epoch, no-loop projection; source evidence отдельно | mTLS/API roles; outbox age, projection version gap |
| F12 | Normalized Parquet/CSV manifest → COPY staging → SQL; hourly batch | Публикация ≤2 ч от source commit | DWH owner / Accounting acceptance | Balance/count/FK/duplicate gates; атомарная версия mart | Restricted staging; manifest missing, DAG duration, watermark completeness |
| F13 | JSON/CSV snapshot+delta hourly | ≤2 ч, до F12 publish | Customer/Reference Owner | SCD intervals и as-of join, reference version pinned | Минимизация ПДн; unmatched facts, invalid intervals |
| F14/F20/F15 | SQL/read API; по запросу | p95 типового dashboard ≤5 сек; видимая свежесть ≤2 ч | BI owner | Сертифицированные формулы; quality/as_of на экране | SSO, RLS/column masks; latency/errors/доступы |
| F16 | Согласованный регуляторный формат + signature/hash; D+1/по календарю | Внутренний пакет готов до 08:00 D+1; реальный срок регулятора уточняется | Finance Reporting Owner | Подписанное закрытие и контрольный manifest; доставка/ack отдельно | Канал утверждённого получателя; deadlines, checksum, ack, report_version |
| F17 | Metadata JSON API; на deployment и nightly | Критичный новый schema/lineage до публикации данных; остальные ≤24 ч | Data Office + domain stewards | Owner/sensitivity/schema/lineage обязательны | Без sample ПДн; missing-owner/lineage coverage, ingestion failures |
| F18/F19 | Workflow JSON/HTTPS; по запросу | UI p95 ≤3 сек; queue age как F09 | Data Office + Customer Owner | Four-eyes, evidence, rule version; source audit | SSO, отдельные approve/read роли; audit completeness |

## Доставка и повторение

Envelope: `event_id, source_bank, source_system, entity_type, source_key, operation, source_commit_position, source_tx_id, record_version, occurred_at, bank_date, schema_version, correlation_id, origin_event_id, master_epoch`. Consumer хранит применённую `(source_system, event_id)` и последнюю версию объекта в одной локальной транзакции с upsert. Повтор не создаёт вторую запись. Для batch: `batch_id, from/to_watermark, file_count, row_count, totals_by_currency, sha256, schema_version`; checkpoint продвигается только после успешной сверки и publish.

Порядок гарантируется только внутри source key/partition; глобального порядка восьми систем нет. Старшая версия не перезаписывается поздним событием. Отсутствующий FK переводит зависимую запись в pending, после bounded retry — quarantine с тревогой; финансовые суммы не теряются. Для состояний «закрыто/отменено» валидируются разрешённые переходы. Для удаления сохраняется tombstone с версией, чтобы replay не воскресил запись.

Transient retry: 3 попытки с backoff 1/5/30 секунд и jitter; затем durable retry queue/DLQ. Schema/auth/DQ ошибки сразу в quarantine; служба эксплуатации не «чинит» payload без владельца. DLQ хранит защищённый payload/ref и reason, owner, first_seen, срок разбора. Replay с исходным event_id и новой transform_version сначала идёт в shadow, сверяется и атомарно заменяет вычисленный срез; не отправляет команды в Core.

Предлагаем Kafka retention 7 дней для replay, затем архив manifest/source events по согласованной политике; discovery проверяет, что outage+repair укладываются в retention. При превышении — resnapshot с новым T0 и сверкой, не продолжение с дырой. Для PostgreSQL-источников slot lag может удерживать WAL; лимиты/alarms должны защищать source disk ([документация](https://www.postgresql.org/docs/current/logicaldecoding-explanation.html)). Для иных legacy — аналогичная проверка механизма журналирования.

Delivery — at-least-once с идемпотентными sinks; end-to-end exactly-once между Kafka и внешней БД не обещается ([Kafka design](https://kafka.apache.org/41/design/design/)). Hub outbox записывается вместе с изменением golden record; polling publisher безопасно повторяет отправку. Потеря уведомления после commit не теряет саму запись.

## Эксплуатация

Платформенная команда дежурит по лагу/ошибкам, steward — по семантике, Finance Owner останавливает публикацию финансового среза. Внутренние цели: аналитический RPO ≤1 ч при возможности replay, RTO ≤4 ч; Customer Hub RPO ≤5 мин/RTO ≤30 мин с репликой и восстановлением. Эти цели требуют испытаний; сбой Hub не останавливает проводки существующих клиентов: Core использует локальные ID, новые неопределённые объединения ждут восстановления. Онлайновые банковские RPO/RTO не понижаются до аналитических.

Alerts: offset gap, unknown schema, late batch, source journal saturation, unresolved finance mismatch, missing lineage. При нарушении BI показывает последнюю сертифицированную версию и реальный as_of; регуляторный пакет не отправляется с недоказанной полнотой. Runbook фиксирует affected bank/date/currency, watermark, владельца, решение о rerun/rollback и audit trail.
