# Deep Overall Retro

## Situation

За один день проект прошёл через несколько фаз:

- initial tooling bootstrap
- hardening metrics semantics
- переход от `tasks` к `goals + entries`
- выравнивание cost semantics
- product framing и PM-переоценку

К концу серии стало ясно, что локальных ретро уже много, но нужен один общий разбор:

- почему работа так сильно ушла в `meta` и `retro`
- какая была настоящая первопричина повторяющихся product misses
- что из этого должно стать постоянным правилом в `AGENTS.md`

## What Happened

Система стала намного сильнее инженерно:

- появились `goals + entries`
- разделились effective goal truth и raw retry pressure
- появились real invariant checks
- usage/cost начали подтягиваться автоматически
- появился verify stack и более зрелая тестовая пирамида

Но по ходу работы несколько раз повторялась одна и та же продуктовая проблема:

- делалось что-то полезное и технически умное
- но не всегда это было именно тем outcome, который нужен пользователю в данный момент

Самые заметные формы этого:

- pricing-only решение вместо полного автоматического cost tracking
- draft product framing без подтверждения от пользователя
- brittle `Complete Cost per Success`, который был формально честным, но продуктово почти бесполезным
- сильный уклон в polishing measurement system до окончательного закрепления operator loop

## 5 Whys

### Problem

Почему проект так легко уходил в adjacent work, meta-работу и уточнение измерений вместо самого короткого пути к операторской ценности?

### Why 1

Потому что мы часто оптимизировали ближайший технический под-вопрос, а не проверенный пользовательский outcome.

### Why 2

Потому что локально каждый такой шаг выглядел разумным:

- улучшить validation
- улучшить schema
- сделать metrics честнее
- сделать cost semantics строже

Но эти шаги не всегда проверялись против главного вопроса: помогает ли это оператору быстрее понять, что в работе с Codex реально выгодно.

### Why 3

Потому что главная продуктовая рамка была подтверждена поздно.

До явного проговаривания operator JTBD проект развивался как trustworthy metrics engine, а не как operator decision tool.

### Why 4

Потому что engineering rigor был сильнее product framing.

Команда быстро строила guardrail-ы, валидацию, тесты и policy, но реже останавливала себя вопросом:

- это устраняет главное ограничение системы
- или просто улучшает уже сильный слой

### Why 5

Потому что основной системный constraint был не в коде, а в product alignment.

Пока не было точно зафиксировано:

- кто пользователь
- какое решение он хочет принимать
- какой сигнал для него важнее остальных

любая следующая итерация имела высокий шанс уйти в locally rational, but globally suboptimal work.

## Theory of Constraints

### Constraint

Главное ограничение проекта на протяжении большей части работы было не:

- не тесты
- не архитектура
- не производительность updater

Главное ограничение было таким:

`система слабо помогала оператору принять следующий правильный ход`

То есть bottleneck был в operator decision loop.

### What we did before recognizing the constraint

Мы много улучшали subordinate layers:

- truthfulness
- bookkeeping semantics
- schema shape
- cost math
- reporting integrity

Это было важно, но в какой-то момент стало видно, что constraint уже сместился.

### What changed after recognizing it

После явной product framing и внешнего аудита следующие шаги стали заметно лучше по ROI:

- operator review layer
- clearer cost coverage semantics
- отказ от brittle all-or-nothing KPI
- прямое обсуждение user intent вместо догадок

### TOC conclusion

Для этого проекта нельзя продолжать долго оптимизировать measurement sophistication, если operator loop остаётся недостаточно ясным.

Когда текущий constraint находится в product interpretation, новые raw metrics и новые refactors должны ждать.

## Retrospective

Что сработало хорошо:

- маленькие обратимые изменения
- очень быстрый learning loop
- превращение pain points в tests, rules и validation
- честное разделение goal truth и retry history
- постепенный отказ от красивых, но misleading KPI

Что сработало хуже:

- слишком рано оформленные выводы о product vision
- слишком поздняя фиксация operator JTBD
- несколько циклов локальной оптимизации до проверки главного ограничения

## Conclusions

1. Главный failure mode этого проекта не “плохой код”, а `adjacent completion instead of requested outcome`.
2. Главный системный constraint для текущей стадии проекта находится в operator decision usefulness.
3. Если product framing ещё не подтверждён, любые vision-формулировки должны считаться hypothesis draft, а не settled truth.
4. Для partial data metrics coverage + subset averages полезнее, чем brittle all-or-nothing KPI.
5. После достижения acceptable engineering rigor дальнейший рост ценности должен идти через better decision support, а не через endless semantics polishing.

## Permanent Changes

- В `AGENTS.md` нужно явно закрепить, что неподтверждённый product framing оформляется как hypothesis draft и не объявляется финальным без подтверждения пользователя.
- В `AGENTS.md` нужно явно закрепить, что `adjacent but not requested` результат считается первичным quality failure.
- В `AGENTS.md` нужно закрепить constraint-first правило: перед новым polishing или refactoring спрашивать, находится ли bottleneck действительно в этом слое.
- В `AGENTS.md` нужно закрепить правило для partial data metrics: prefer explicit coverage and covered-subset averages over brittle all-or-nothing KPI.
