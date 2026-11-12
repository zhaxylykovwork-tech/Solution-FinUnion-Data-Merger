# Первичные источники и границы заимствования

Проверены 12.11.2026. Источники подтверждают назначение механизмов; архитектура, пороги, SLA и планы ниже являются проектными решениями. Полные тексты курса в репозиторий не включаются.

| Источник | Что проверено / где используется |
|---|---|
| [BIAN release 13, официальный набор API](https://github.com/bian-official/public/tree/main/release13.0.0/semantic-apis/oas3/yamls) | Зафиксирована версия 13 для воспроизводимого словаря Task1/Task2. Это не заявление о последней версии |
| [Party Reference Data Directory](https://github.com/bian-official/public/blob/main/release13.0.0/semantic-apis/oas3/yamls/PartyReferenceDataDirectory.yaml) | Область справочных данных стороны; локальный Customer Hub проектируется отдельно |
| [Position Keeping](https://github.com/bian-official/public/blob/main/release13.0.0/semantic-apis/oas3/yamls/PositionKeeping.yaml), [Payment Execution](https://github.com/bian-official/public/blob/main/release13.0.0/semantic-apis/oas3/yamls/PaymentExecution.yaml) | Разделение учёта движения и исполнения платежа |
| [Product Directory](https://github.com/bian-official/public/blob/main/release13.0.0/semantic-apis/oas3/yamls/ProductDirectory.yaml), [Location Data Management](https://github.com/bian-official/public/blob/main/release13.0.0/semantic-apis/oas3/yamls/LocationDataManagement.yaml) | Границы справочной информации о продукте и местоположении |
| [PostgreSQL logical decoding](https://www.postgresql.org/docs/current/logicaldecoding-explanation.html) | Возможны повторы после сбоя, необходимы идемпотентность и контроль replication slot; не предполагается поддержка PostgreSQL в legacy |
| [Kafka design](https://kafka.apache.org/41/design/design/) | Журнал событий, порядок в partition и ограничения гарантии exactly-once при внешних sinks |
| [Iceberg](https://iceberg.apache.org/docs/latest/) | Формат аналитических таблиц с метаданными и snapshots поверх файлов, не СУБД для банковских проводок |
| [Trino Iceberg connector](https://trino.io/docs/current/connector/iceberg.html) | Отдельные роли SQL engine, Iceberg catalog и object storage, необходимость обслуживания таблиц |
| [Airflow architecture](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html) | DAG оркестрирует batch-задачи; потоковые workers работают вне scheduler |
| [DataHub features](https://docs.datahub.com/docs/features) | Каталог, ownership, lineage; фактическая защита доступа обеспечивается также в БД/хранилищах |

Имена остальных BIAN-областей и ссылки на их официальные спецификации приведены в [reference-model.md](Task1/reference-model.md). Маппинг — интерпретация для кейса: сервисный домен BIAN не равен таблице, микросервису или Data Owner автоматически.
