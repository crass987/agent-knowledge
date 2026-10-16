# Каденс обслуживания харнесса

Одна строка на задачу: `имя | период дней | последний прогон | статус`.
Статус: `active` (участвует в напоминаниях) | `planned` (не построена — не напоминает).
Обновляй «последний прогон» при выполнении задачи (дата ISO YYYY-MM-DD).
Проверка: `scripts/cadence-check.sh` — печатает только просроченное active, молчит иначе.

store-check | 0 | never | planned
traverse | 14 | never | active
prune | 30 | 2026-10-08 | active
budgets | 30 | never | planned
estate | 7 | 2026-10-16 | active
