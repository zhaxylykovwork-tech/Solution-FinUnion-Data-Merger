# Проблемные зависимости

| Зависимость / проблема | Последствие | Контроль / условие | Владелец |
|---|---|---|---|
| Разные local customer ID; возможен ID reuse | Неверный Customer 360 и дедупликация оборотов | Составной ключ source+ID, history, детерминированный matching и ручная очередь | Customer Owner |
| Тариф зависит от версии продукта/договора | Унификация справочника меняет действующие начисления | Pin tariff_version в договоре; утверждённый crosswalk без ретроактивной подмены | Product Owner |
| Posting зависит от Account, AgreementParty и Customer mapping | Потеря строк при inner join или чужой продукт | Deferred FK/pending, unknown dimension, totals до/после join; gate перед cutover | Accounting + Customer |
| Платёж и проводка имеют разные ключи/статусы | Двойной оборот или повторное исполнение | Разные сущности; только проведённые записи в ledger mart; repayment command replay запрещён | Payment Owner |
| Валюты, timezone и банковская дата различаются | Ложный дисбаланс и некорректный закрытый день | Сохранять UTC+zone+bank_date, суммы по currency, утверждённый FX rate/version | Finance |
| CDC зависит от доступного журнала и schema | Незаметный пробел/остановка source при WAL overflow | Source-native assessment, monitoring, pinned schema, snapshot+delta manifests | Core + Integration |
| Cards/Loans lifecycle зависит от внешней сертификации/контракта | Нельзя безопасно выключить RB по календарю | Небольшие когорты; непереносимые договоры остаются в реестре исключений и старом мастере | Cards/Loans owners |
| Consent зависит от цели, юрлица и доказательства | Неправомерная коммуникация после merge | Не объединять grants логическим OR; консервативная projection, отзыв имеет приоритет в scope | Customer + Privacy |
| Старые отчёты/партнёры читают RB напрямую | Скрытая зависимость ломается при shutdown | DataHub lineage + анализ логов/опрос consumer owners, контракт и период наблюдения | Data Office + IT |
| Согласованная отчётность зависит от общих формул | Две «верные» суммы разных BI | Один certified metric layer, Finance sign-off, pinned reference версии и as_of | Finance + BI |
