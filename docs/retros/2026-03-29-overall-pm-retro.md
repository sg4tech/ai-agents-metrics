# Overall PM Retro

## Situation

После серии инженерных задач вокруг metrics updater стало важно посмотреть на результат не как на набор fixes и refactors, а как на продукт.

Главный вопрос с точки зрения PM и клиента был таким:

- делали ли мы вообще то, что было нужно пользователю
- какую ценность система теперь реально даёт
- где инструмент уже выглядит как usable product, а где ещё остаётся engineering-heavy

## What Happened

По факту работа шла в несколько слоёв.

Сначала был базовый CLI для metrics bookkeeping.

Потом постепенно были добавлены и исправлены ключевые продуктовые свойства:

- честная goal-модель вместо сырой task-only истории
- отдельный entry-level view, чтобы retries и failures не скрывались за итоговым success
- автоматический cost/usage ingestion там, где доступен Codex telemetry source
- строгая валидация history и summary invariants
- безопасные merge/supersession flows
- ретры, policy, verify-flow и reproducible test stack

На выходе получился не просто “скрипт для JSON”, а рабочая система учёта outcome, attempts, failure reasons и частично cost.

## Root Cause

Изначальная потребность пользователя была не в технической чистоте кода.

Она была в следующем:

- нужен доверяемый способ понять, помогает ли Codex реально доводить работу до результата
- нужны честные метрики, а не красивые summary
- нужен способ видеть retry pressure и failure modes
- нужен cost/accounting слой хотя бы в автоматизируемой части

То есть настоящий продуктовый запрос был про trustworthy delivery telemetry, а не про локальный utility script.

Часть ранней работы была слишком tool-centric, и только после нескольких ретро и аудитов система стала больше ориентироваться на outcome truth.

## Retrospective

С точки зрения PM сейчас картина уже хорошая.

Что реально доставлено:

- есть source of truth
- есть human-readable report
- есть goal-based success accounting
- есть separate attempt history
- есть failure reason visibility
- есть policy and process discipline
- есть автоподхват стоимости там, где есть usage source

Что особенно важно продуктово:

- система меньше врёт
- итоговый success больше не скрывает болезненный путь до него
- история не зависит от ручной правки generated files
- есть воспроизводимый verify-flow

Но важно и то, что пока ещё не идеально:

- `cost_per_success` часто остаётся `n/a`, потому что historical cost chains неполные
- UX всё ещё CLI-first, а не manager-first
- markdown report — это уже useful artifact, но ещё не полноценный dashboard
- часть ранней истории была восстановлена уже постфактум, поэтому historical completeness ограничена

## Conclusions

- Да, в целом была сделана именно та система, которая была нужна, а не просто инженерный refactor exercise.
- Самая большая доставленная ценность — переход от “лог успешных задач” к “честной системе учёта goals, attempts и failures”.
- Продукт уже полезен для внутреннего принятия решений и retrospective analysis.
- Следующий продуктовый шаг — не большой рефакторинг, а улучшение presentation/UX и постепенное усиление cost completeness.

## Permanent Changes

- Оценивать дальнейшую работу над metrics system прежде всего по продуктовой пользе: trustworthy reporting, visibility of retry pressure, and cost usefulness.
- Не считать goal-level success alone достаточной картиной здоровья системы; entry-level failures и failure reasons должны оставаться видимыми.
- Не продолжать large-scale refactoring без нового продуктового сигнала; дальше приоритет у targeted product improvements и quality hardening.
