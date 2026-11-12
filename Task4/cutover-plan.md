# Cutover критичного домена «Управленческая отчётность»

Охват: RB+FU customer/account/product/posting marts и соответствующие BI datasets; регуляторный пакет готовится в общем DWH, но отправляется лишь по отдельному Finance-approved календарю. Это переключение чтения и публикации, operational masters Core/CRM/Cards/Loans не меняются. Полной остановки клиентских сервисов нет. Время T — утверждённое Finance окно после закрытия банковского дня; ниже не реальное расписание банка, а шаблон runbook.

| Шаг / когда | Действие / исполнитель | Доказательство / решение |
|---|---|---|
| C01, T−14д | DWH team инвентаризирует отчёты, SQL jobs, endpoints и consumer owners; фиксирует scope банков/дат/валют | Подписанный consumer registry; неизвестный downstream = No-Go |
| C02, T−14..−2д | Finance проводит минимум 10 рабочих дней параллельного расчёта на одинаковом watermark и metric version | Ноль необъяснённых count/sum/balance differences; объяснённые семантические изменения согласованы письменно |
| C03, T−2д | Platform/ИБ проверяют RBAC/RLS/masks, backup/restore DWH и Hub, secret rotation readiness, failback rehearsal | Restore ≤4ч аналитического RTO, smoke и доступы приняты; snapshot/restore IDs записаны |
| C04, T−1д | Release manager фиксирует SQL Git SHA, schema/reference/FX/calendar versions, old/new endpoints и rollback feature flag | Immutable release manifest, ответственные on-call и escalation назначены |
| C05, T−30мин | Finance вводит **publication freeze**: нельзя менять отчётные формулы/справочники для закрываемой версии, активировать новые BI datasets и рассылать пакет | Новые операционные данные продолжают поступать в raw/delta; клиентские сервисы доступны. Срочное исправление означает отмену cutover и новый manifest |
| C06, T | Core teams подтверждают закрытый bank_date и source watermarks W_FU/W_RB; ingestion снимает финальные deltas до каждого W | Manifest snapshot+delta без gaps, deletion/closure entries включены; более новые события идут в следующую версию |
| C07, T+ | DWH team загружает deltas в shadow, pins dim/reference versions, строит весь scope; transform повторяемый | Batch_id unique, all inputs accounted; hash files и canonical keyed-row digests совпали после утверждённой нормализации |
| C08 | Data QA выполняет техническую сверку: keys/counts/FK/duplicates/NULL/intervals и mapping coverage | Rejected/pending отдельно учтены. Нельзя скрыть missing posting исключением из scope |
| C09 | Finance сверяет debit/credit и closing balances по банку/счёту/дню/валюте, фиксирует внутренние переводы, FX rates, customer/product totals | Ноль необъяснённых финансовых differences; totals сравниваются на одном W, source sign-off |
| C10 | Go/No-Go: Finance Owner принимает финансовое качество, Customer Owner mappings, ИБ доступы, IT готовность; Release manager исполняет | Любой обязательный gate не пройден → No-Go, старый endpoint продолжает работу; freeze снимается, новые данные не теряются |
| C11 | Атомарно активировать published_version, переключить BI dataset alias/read endpoint и report generation job; старые export jobs fenced | Только один активный publisher/exporter данного report_id/period; old version read-only доступна on-call |
| C12 | BI owner выполняет smoke: утверждённые dashboards, роли, as_of, сверка контрольного отчёта; наблюдение 1ч | При p95>5с устойчиво 15мин, access incident или любом необъяснённом mismatch — rollback decision, freeze новых exports |
| C13 | Finance снимает publication freeze и отдельно утверждает первый package_id/report_version; доставка с checksum/ack | До передачи пакета наружу cutover полностью обратим по read route. После передачи нельзя «отменить отправку»: нужна корректирующая версия по процедуре получателя |
| C14, T+1..10 раб.дней | Platform+Finance сверяют daily totals, late events, freshness, ошибки, отчётные сроки и feedback | Отклонения зарегистрированы, closure/gap stats доступны; old stack не удалён |
| C15, полный цикл | Consumer owners подтверждают переход; IT по акту выключает старые jobs после archive retrieval/retention проверки | Архив report versions/lineage сохранён, нет трафика старых endpoints; завершение cutover |

## Контрольные суммы и бизнес-проверки

Файл проверяется по SHA-256 и manifest; это доказывает целостность передачи, но не правильность преобразования. Для source/target сравнивается canonical row digest по отсортированным business keys с утверждёнными decimal/date/code mappings, плюс отдельные counts и sums; raw-byte hashes разных форматов не обязаны совпадать. Рассматривается весь охват, а не только sample. Двойная бухгалтерская запись сверяется по source transaction/currency, остатки — по правилам знака конкретного типа счёта. Финансовый gate не допускает «почти сошлось».

Количество клиентов различает source records, distinct global IDs и possible duplicates. Уменьшение числа после legitimate merge объясняется таблицей crosswalk, а не считается потерей клиента. У договоров сохраняются участники/тарифные версии; unresolved matches не дают менеджеру чужих счетов. Документы сверяются по reference+hash, raw payload не попадает в BI.

## Фолбэк до/после внешнего отчёта

До C13 Release manager останавливает новые export jobs, фиксирует incident и bad publish_version, возвращает BI alias и publisher flag на последнюю сертифицированную legacy version. Raw ingestion не останавливается, offsets/checkpoints сохраняются; поздние deltas доигрываются и сверяются. На экране виден реальный as_of старой версии. Цель route rollback ≤15мин проверяется на репетиции; полный аналитический restore при повреждении ≤4ч — отдельная цель.

После C13 возврат dashboard возможен, но внешний пакет уже передан. Finance Owner блокирует новые пакеты и выпускает согласованное исправление с новым report_version/reference на исходный package_id; transport ack не трактуется как подтверждение правильности регулятором. Скрыто заменить файл под прежним ID запрещено. Новое включение общего publisher требует повторного Go по affected scope.

Мониторинг: source/consumer lag, missing manifests, rejected/pending counts, control total deltas, RLS audit, report as_of, query p95, successful package ack/deadline. Platform on-call отвечает за доставку, Finance — за публикацию и корректировки, Customer steward — за crosswalk; один Release manager ведёт журнал решений.
