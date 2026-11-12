# Реестр потоков: состояние 3 месяцев

В контексте P0 — единая платформа данных (Integration Layer, MDM, DWH, BI, DataHub). Восемь операционных систем, сотрудник, steward и регулятор — внешние участники относительно P0. Детальная схема раскрывает P0. FU DWH используется как основа нового выделенного PostgreSQL DWH только после проверки совместимости; при несовместимости разворачивается новый кластер. RB DWH/BI временно продолжают старую отчётность параллельно и не являются источником новых финансовых фактов.

| ID | Источник → приёмник | Сущности / действие | Режим | Назначение |
|---|---|---|---|---|
| F01 | FU CRM → Integration Layer | Customer, Case, Consent, Document refs; Create/Update/Delete | Async events или дельта batch | Принять клиентские сведения FU |
| F02 | RB CRM → Integration Layer | Те же сущности; Create/Update/Delete | CDC или согласованный batch | Принять клиентские сведения RB |
| F03 | FU Core → Integration Layer | Account, Agreement/Party, Posting, Payment; Create/Update/Read | Log CDC или контрольная выгрузка | Сохранить учётный авторитет FU |
| F04 | RB Core → Integration Layer | Те же; Create/Update/Read | CDC либо batch snapshot+delta | Безопасно включить RB в отчётность |
| F05 | FU Cards → Integration Layer | Card, карточный Agreement/Party; Create/Update | Async/CDC | Единый статус карт; только token |
| F06 | RB Cards → Integration Layer | Те же; Create/Update | CDC/batch | Нормализовать RB статусы |
| F07 | FU Loans → Integration Layer | Loan, кредитный Agreement/Party; Create/Update | CDC/batch | Кредитный портфель FU |
| F08 | RB Loans → Integration Layer | Те же; Create/Update | CDC/batch | Кредитный портфель RB |
| F09 | Integration Layer → MDM | Customer proposals, Consent projection; Validate/Enrich/Create/Update/Delete | Async worker | Matching, проверка и золотая запись; удаление по утверждённой политике |
| F10 | MDM → Integration Layer | Customer ID/crosswalk/reference updates; Create/Update/Delete | Transactional outbox → async | Опубликовать только утверждённую версию |
| F11 | Integration Layer → FU/RB CRM (две ветви F11F/F11R) | Golden profile, crosswalk, reference codes; Enrich/Update/Delete | Async projection | Менеджер видит общий ID; source evidence не перетирается |
| F12 | Integration Layer → DWH | Account/Agreement/Party/Card/Loan/Posting/Payment/Case/Document metadata; Validate/Create/Update/Aggregate | Hourly ELT batch | Единые факты и операционная история; без PAN и исходных документов |
| F13 | MDM → DWH | Customer/Identifier/Product/Tariff/Branch/Segment/Consent projection; Read/Enrich | Hourly snapshot+delta | Conformed dimensions и безопасные purpose-фильтры |
| F14 | DWH → BI | Сертифицированные витрины; Read/Aggregate | SQL по read endpoint | Изолированная аналитика |
| F15 | BI → Сотрудник | Клиенты, продукты, остатки и обороты; Read | Синхронное отображение | Управленческие решения с as_of и quality_status |
| F16 | DWH → Регуляторный потребитель | Утверждённый отчётный пакет; Aggregate/Read | Signed batch export после закрытия | Финансовая/регуляторная отчётность; не «автоматически принятый» отчёт |
| F17 | Integration Layer/MDM/DWH/BI → DataHub | Схемы, ownership, lineage, DQ; Create/Update | Metadata API batch/events | Источник до dashboard; schema change не теряется |
| F18 | Steward → MDM | Match decision, утверждённые reference changes; Validate/Update | Синхронный workflow | Исправления с аудитом; нет прямого DML |
| F19 | MDM → Steward | Конфликты, очередь quality review; Read | Синхронный UI | Человек получает основание для F18 |
| F20 | Сотрудник → BI | Запрос/параметры отчёта; Read request | Синхронно | Вход для результата F15, row-level scope |

В L0 F01–F08 сведены в «данные операционных систем», F11 — «золотой профиль/справочники в CRM», F18/F19 — решения/очередь, F20/F15 — запрос/отчёт, F16 — отчёт регулятору. При детализации внешние потоки сохраняются. F09/F10/F12/F13/F14/F17 внутренние и в L0 не появляются.

Delete означает tombstone/ограничение допустимого использования, а не SQL DELETE финансовой истории. При F09 отзыв согласия меняет projection и ограничивает потребление; запрос физического удаления следует retention/legal hold. На DFD нет команд перевести деньги: F03/F04 переносят уже созданные факты, а не запускают финансовые операции.

Операционные системы дополнительно получают reference crosswalk через существующую ESB/адаптеры по требованию владельца, без назначения нового writer финансовых данных. На 3 месяца обязательный обратный поток только в обе CRM; Core/Cards/Loans сохраняют локальные коды с явным mapping в Integration Layer/DWH. Метаданные F17 формируются платформенными ingestion jobs, включая схемы восьми источников; доступ к исходным payload каталогу не нужен.
