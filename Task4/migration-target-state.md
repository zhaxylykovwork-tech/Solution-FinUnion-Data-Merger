# Образ результата миграции

| Объект | Остаётся / выводится | Данные / переключение | Exit gate |
|---|---|---|---|
| FU CRM | Целевой канал профиля и обращений | RB Case/history и consent evidence с lineage; common customer ID из Hub | Роли/доступы/история/отзывы проверены, нет потерянных открытых обращений |
| Customer/Reference Hub | Новый постоянный мастер Customer/crosswalk/reference | Golden profiles, alias/unmerge history, Product/Tariff/Branch/Segment | One-current mapping, спорные пары изолированы, audit и restore проверены |
| FU Core | Целевой учётный мастер после cutover каждой когорты | Счета, договорные ссылки, opening positions, проводки/история; незавершённые платежи закреплены за исходным executor | Нулевые необъяснённые расхождения по валюте/счёту/дню, закрытие дня и rollback rehearsal приняты |
| FU Cards | Целевой процессинг | Tokens/status/agreements; перенос/перевыпуск по правилам схем и процессинга | Сертификация, успешные тесты авторизации/клиринга/споров, нет двух активных исполнителей |
| FU Loans | Целевая кредитная система | Договоры, графики, principal/interest/overdue с версией | Приёмка расчётов, юридическая допустимость, сверка к Core и Loans source |
| DWH + BI | Общие PostgreSQL DWH и certified metrics | Данные обоих банков, report snapshots, legacy mapping; cutover Read endpoints и export jobs | 10 рабочих дней parallel reconciliation, Finance sign-off, восстановление и фолбэк в RTO |
| Lakehouse | История и события | Архивы RB/Cards, channel events, curated аналитика | Manifest/lineage, replay/snapshot/erasure/ACL испытаны; нет дублирования ledger totals |
| ESB/adapters/Kafka | Общая управляемая интеграция | Point-to-point переводятся на канонические versioned contracts | Инвентаризация consumers, alarms, retry/DLQ/replay drill, отключён старый маршрут после gate |
| DataHub | Единый каталог | Metadata всех критичных наборов/BI | 100% critical assets имеют owner, sensitivity, lineage, согласованные glossary terms |
| RB CRM | Вывод после переноса обслуживания | По когорте write freeze на операции профиля, маршруты → FU; доказательства/архив отдельно | Нет активных writers/читателей старого API, обращения и согласия сверены |
| RB Core/Cards/Loans | Вывод по доменам и портфелям | Domain-by-domain master_epoch, legacy history становится read-only | Все gates выше плюс подтверждённые внешние dependencies; непереносимые портфели удерживают исключение открытым |
| RB DWH/BI | Сначала parallel, затем read-only архив/вывод runtime | Сохранить закрытые отчёты/семантику/retention; consumers → общий serving | Подтверждение всех owners/получателей и отсутствие трафика старых jobs за полный отчётный цикл |

Сохранение «legacy history» не означает сохранение полной legacy runtime-системы навсегда. После проверки архив содержит разрешённые snapshots, manifests, исходные keys, документы и возможность retrieval в требуемый срок. Удаление старых runtime/backup проводится по утверждённой retention policy, legal hold и акту закрытия. Секреты/доступы интеграций отзываются после завершения зависимостей, не во время незавершённой сверки.

Полная готовность 12 месяцев означает выполненные exit gates, а не наличие галочек развёртывания технологий. Если технически/юридически нельзя перенести часть карт/кредитов, программа документирует остаточный портфель, его мастер, риски, операционные затраты и новый срок; завершение отключения RB не декларируется.
