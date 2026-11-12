# Риски миграции

Вероятности качественные, до discovery; это приоритеты проверки, а не измеренные частоты.

| Риск | Влияние | Вероятность | Митигация | Сигнал / действие / владелец |
|---|---|---|---|---|
| Ложный merge клиента | Чужие продукты в профиле, утечка/ошибки | Высокая | Консервативный match, conflict quarantine, four-eyes, reversible alias | Conflict/жалоба → отключить affected projection, unmerge и rebuild / Customer+ИБ |
| Пропуск/повтор CDC | Неполные либо двойные суммы | Средняя | T0 consistent snapshot, source version, dedup, retention, control totals | Offset gap/mismatch → hold publish, replay/resnapshot / Integration+Finance |
| WAL/journal переполнен из-за слота | Сбой операционного источника | Средняя | Замеры, alerts и лимиты, supported export fallback | Рост lag/disk → throttle backfill, согласованный resnapshot; не удалять журнал молча / Core+Platform |
| Некорректный тариф/FX/банк-дата | Неверные обязательства и отчёт | Высокая | Version pin, native currency controls, банковский календарь | Rule mismatch → No-Go, исправить mapping и rerun shadow / Product+Finance |
| Source schema breaking change | Потеря полей/остановка pipeline | Средняя | Registry, compatibility gate, staged rollout/new major | Unknown schema → quarantine+alert, не default zero / Source owner+Platform |
| Два writers/publishers | Повторный платёж/две версии отчёта | Средняя | Cohort/epoch fencing, idempotency, drain in-flight | Duplicate executor/report_id → остановить новые commands/exports в scope, reconcile / Domain owner |
| Недооценён поздний reversal | Старый отчёт поменялся без уведомления | Средняя | Immutable report versions, exception queue, correction process | Late posting закрытого периода → Finance correction, не silent overwrite / Finance |
| Утечка в raw/DLQ/logs/backup | ПДн/банковская информация раскрыта | Средняя | Сквозные теги, минимизация, encryption, ACL, маски | Необычный download/access → revoke affected role, incident response / ИБ |
| Отзыв согласия потерян при merge | Неправомерная коммуникация | Средняя | Purpose/scope/legal_entity, evidence, revocation propagation | Stale consent projection → fail-closed использование, rebuild / Privacy+Customer |
| Скрытый consumer RB | Простой интеграции/отчёта при shutdown | Высокая | DataHub+логи+опрос owners, parallel full cycle, deprecation notice | Трафик/неподписанный owner → остановить decommission / IT+Data Office |
| Непереносимый карточный/кредитный контракт | Срок вывода RB сорван | Средняя | Ранняя юридическая/процессинговая проверка, отдельные когорты, reissue plan | Нет certification/sign-off → оставить один RB master по исключению, пересогласовать срок / Cards+Loans |
| Backup есть, restore не работает | Невосстановимые отчётность/история | Средняя | Restore drills, encrypted off-zone copies, manifest/catalog backup | RTO test fail → No-Go следующей волны / Platform |
| Недостаток навыков/ресурсов | Lakehouse не поддерживается | Средняя | Skill assessment, обучение, малый trial, managed/vendor options после TCO | Нет on-call/runbook или cost превышен → не вводить trial в production / Programme Owner |
| Неверный sign/зерно join | Double count оборотов и остатков | Высокая | Posting grain, as-of SCD2, role bridge отдельно, native totals до/после joins | Изменилась cardinality/sum → block publish и поправить transform / DWH+Finance |

Общие stop-критерии: любое необъяснённое финансовое расхождение, незащищённый доступ, недоказанная полнота source history, отсутствие единственного writer или успешной репетиции восстановления. Риск календарной задержки принимается явно владельцем программы; он не оправдывает обход критичного gate.
