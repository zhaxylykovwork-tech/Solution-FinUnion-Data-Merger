# Матрица мастер-систем

Мастер — единственный авторитет для конкретной записи/атрибута на данный момент. Источник первого создания, физическое хранилище и мастер могут отличаться. Например, CRM принимает заявку изменить контакт, Hub после проверки публикует золотое значение, DWH хранит производную историю. В 3 месяца FU/RB мастера финансовых сущностей разделены по origin_bank и портфелю; они не конкурируют за одну запись.

| Сущность | Создание / As-Is физические источники | Мастер 3 месяца | Мастер 12 месяцев после gates | BIAN / причина |
|---|---|---|---|---|
| E01 Customer | Onboarding/KYC → FU/RB CRM; копии Core/Loans | Hub для global ID/общих атрибутов; CRM подаёт проверенные изменения | Hub; FU CRM — интерфейс, не второй мастер | Party Reference Data Directory: единый профиль |
| E02 Identifier | Local ID создаёт source; crosswalk создаёт Hub | Hub | Hub с историей | Party reference: разрешение идентичности |
| E03 Agreement | FU/RB Core для счетов, Cards для карточного продукта, Loans для кредита | Создавшая профильная система по origin/domain | FU Core/Cards/Loans по типу договора | Sales Product Agreement: юридические условия у профильного owner |
| E04 AgreementParty | FU/RB профильная система договора | Мастер соответствующего Agreement | FU профильная система | Agreement: роли и полномочия не определяются matching |
| E05 Account | FU/RB Core | Core своего портфеля | FU Core | Current/Corporate Current Account: ACID/остатки |
| E06 Card | FU/RB Cards | Cards своего портфеля | FU Cards, RB только для явно неперенесённых исключений | Credit Card / Card Authorization: lifecycle процессинга |
| E07 Loan | FU/RB Loans | Loans своего портфеля | FU Loans, gate по графикам и договорам | Consumer/Corporate Loan: кредитные расчёты |
| E08 Posting | FU/RB Core при проведении | Origin Core; immutable прошлые записи | FU Core для новых движений; legacy history read-only с прежним origin | Position Keeping: проводки не редактируются Hub |
| E09 Payment | Платёжный модуль Core принимает поручение из канала | FU/RB Core по origin, без повторного исполнения | FU Core payments | Payment Execution: один state machine |
| E10 Product | Продуктовая команда; FU/RB справочники | MDM Reference Hub после утверждения crosswalk | MDM Reference Hub | Product Directory: канонический каталог |
| E11 Tariff | Продуктовый комитет; Core/Cards/Loans | Hub — опубликованные версии; договор хранит выбранную версию | Hub; профильная система применяет закреплённые условия | Product Directory + product agreement: унификация без смены действующих ставок |
| E12 Branch | Владелец сети; FU/RB Core/reference | Hub | Hub | Location Data Management: один код с bank_id |
| E13 Segment | CRM/бизнес-владелец | Hub — определения и утверждённое присвоение; CRM — предложение | Hub | Локальная классификация Customer domain |
| E14 Case | FU/RB CRM из каналов | Origin CRM | FU CRM | Customer Case Management: история обслуживания |
| E15 Consent | FU/RB CRM принимает подтверждение/отзыв | Origin CRM — evidence и события; Hub — консервативная проекция по scope | FU CRM consent service — evidence; Hub — projection | Customer domain: отсутствие основания запрещает соответствующее использование |
| E16 Document | CRM/Core/Cards/Loans создают метаданные; payload в закрытом хранилище | Origin document registry + object storage | Единый document registry/storage, owner — создавший домен | Документное доказательство, не MDM payload |

Если RB не поддерживает новый reference API, адаптер материализует локальную версию с mapping_id; это кеш, не право самовольно исправить эталон. Для карточных/кредитных договоров финансовая часть и статус принадлежат профильному мастеру; Core владеет только учётными движениями. DWH agreement index объединяет ссылки и не является мастер-реестром условий.

## Переключение авторитета

Registry `(entity_type, source_key, cohort, effective_from, master_system, epoch)` управляет маршрутизацией. До gate RB принимает команды по своей когорте, FU — по своей. При доменном cutover старый writer блокируется fencing token/epoch, незавершённые команды завершаются или остаются закреплёнными за старым мастером. После согласованного watermark FU становится единственным writer новой эпохи. Старые consumer-проекции не должны порождать обратные команды; origin_event_id и поле projection_only разрывают циклы.

Решения об истинности клиентских атрибутов и процедура merge/unmerge находятся в [data-ownership.md](data-ownership.md). Финансовая миграция переносит записи и opening positions с lineage; платёжные поручения из истории никогда не исполняются заново.
