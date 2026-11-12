# Владение, изменение и качество

Назначены роли, а не вымышленные сотрудники. Data Owner утверждает смысл, доступ и критерии приёмки. Steward разбирает качество и согласует исправления. Producer создаёт события у своего мастера; Consumer получает разрешённую проекцию. Data Office задаёт единый стандарт и координирует конфликт, но не становится владельцем всех банковских фактов.

| Сущность | Data Owner / Steward | Producer | Consumers | Кто меняет / правила DQ |
|---|---|---|---|---|
| E01 Customer | Руководитель клиентского домена / KYC steward | Проверяющая CRM → Hub | CRM, Core, DWH, риск | Только verified proposal; обязательны тип лица и provenance, спорный match на review |
| E02 Identifier | Customer Owner / identity steward | Hub matching | Все адаптеры, DWH | Steward подтверждает спорный merge/unmerge; unique current source key |
| E03 Agreement | Владелец продуктового домена / contract steward | Core/Cards/Loans | CRM, DWH, документный контур | Уполномоченный сотрудник через master API; продукт/тариф и участники валидны |
| E04 AgreementParty | Владелец договора / legal operations steward | Master Agreement | Core, Cards, Loans, CRM | Проверка основания и срока роли; хотя бы один допустимый владелец активного договора |
| E05 Account | Операционный директор / accounting steward | Core | Cards, Loans, DWH | Только Core; уникальный bank+account, валюта/договор обязательны |
| E06 Card | Владелец карточного бизнеса / cards steward | Cards | Core, CRM, risk, DWH | Только процессинг; допустимые переходы статуса, валидный account/holder |
| E07 Loan | Владелец кредитования / credit steward | Loans | Core, risk, DWH | Кредитный workflow; версия графика, principal/проценты/просрочка сверены |
| E08 Posting | Главный бухгалтер / ledger steward | Core ledger | DWH, финансы, аудит | Коррекция отдельной проводкой; баланс группы, completeness по control totals |
| E09 Payment | Владелец платежей / payment operations | Core payments | Core ledger, CRM, DWH | State machine, idempotency key; финальный статус согласован с исполнением |
| E10 Product | Продуктовый комитет / catalogue steward | Reference Hub | Все product systems, DWH | Four-eyes публикация; unique code, family, version |
| E11 Tariff | Продуктовый комитет / tariff steward | Reference Hub | Core/Cards/Loans/DWH | Four-eyes; неперекрывающиеся версии, без молчаливой замены тарифа договора |
| E12 Branch | Руководитель сети / network steward | Reference Hub | Core, CRM, DWH | Утверждённое изменение сети; bank/local code mapping |
| E13 Segment | Customer business owner / segmentation steward | Hub из утверждённых правил | CRM, DWH | Версия definition и rule; одно current присвоение в данной классификации |
| E14 Case | Руководитель контактного центра / service steward | CRM | Менеджеры, BI | Авторизованный агент CRM; valid customer, opened≤closed, словарь статусов |
| E15 Consent | Customer Owner / privacy steward совместно с юристами | CRM consent API | Hub, разрешённые кампании | Только evidence-backed grant/revoke; отзыв приоритетен в совпадающем scope |
| E16 Document | Владелец исходного домена / records steward | Document registry | Уполномоченный KYC/сервис, аудит | Версионная загрузка и hash; не удалять при legal hold, payload соответствует метаданным |

## Авторитет по клиентским атрибутам

Hub владеет global_customer_id, alias и crosswalk. Юридическое имя/регистрация/документ принимаются от процесса KYC с доказательством и effective_at. Контакт получает authority только после проверки владения; более новое ingested_at не означает более достоверный контакт. При двух подтверждённых противоречащих сведениях сохраняются обе версии и открывается конфликт; нет случайного «FU всегда прав» или last-write-wins. Местные source IDs и договорные роли принадлежат исходной системе, Hub их не переписывает. Сегмент имеет версию правил; согласие оценивается отдельно для purpose/scope/legal_entity, исходный evidence остаётся у consent master.

## Matching и survivorship

1. Нормализовать пробелы, формат телефона, наименование и идентификаторы; сохранить original. Физлица и юрлица сравниваются раздельно. Значения документов доступны matching engine в закрытой зоне, в диагностике — токены.
2. Для юрлиц — согласованный состав подтверждённых регистрационных идентификаторов и страны; для физлиц — подтверждённый уникальный документ плюс согласованные ФИО/дата рождения. Совпадение одного ИНН/телефона/ФИО не является достаточным универсальным основанием.
3. Автообъединение разрешено только детерминированному правилу без конфликтов критичных атрибутов. Fuzzy score используется для приоритета ручной проверки. Порог допуска автоматического вероятностного merge не вводится без размеченной выборки и утверждённого false-positive budget.
4. Неоднозначные записи получают собственный global ID и статус possible_duplicate; очередь steward содержит rationale, pair IDs, rule version. На 3 месяца безопаснее неполный merge, чем чужие счета в профиле.
5. Решение merge версионируется с four-eyes для спорных случаев. Сохраняются alias, бывшие global IDs, crosswalk до/после, время и основания; контракты позволяют resolve(alias). Unmerge возвращает отдельные ID и пересчитывает витрины по lineage, но не меняет юридические договоры.

Предлагаемый gate: все автообъединения проходят проверку конфликтов; на согласованной контрольной выборке нет подтверждённых false merges; полнота matched/unmatched/quarantine в сумме равна входу. Размер/репрезентативность выборки задают KYC и риск до пилота. Продукты с неразрешённым клиентом не теряются: финансовые суммы остаются в отчёте с unknown customer, а клиентские метрики публикуются с полнотой и ограничением; активные account mappings должны быть исправлены до продуктового cutover.
