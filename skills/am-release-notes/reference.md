# am-release-notes — reference

Copy-paste jq recipes, the epic→section map, and the three file templates. The
saved Jira result file is JSON (`.issues[]`); pass its path as `$F`.

## jq recipes

Set `F` to the saved result path first:

```bash
F="/path/to/mcp-jira-search_issues-NNN.txt"
```

### Aggregates (run before reading any issue)

```bash
# by status (spot Cancelled inside Done)
jq -r '.issues | group_by(.fields.status.name)[] | "\(.[0].fields.status.name)\t\(length)"' "$F" | sort -t$'\t' -k2 -rn

# by issuetype
jq -r '.issues | group_by(.fields.issuetype.name)[] | "\(.[0].fields.issuetype.name)\t\(length)"' "$F" | sort -t$'\t' -k2 -rn

# by epic (customfield_10300)
jq -r '.issues | group_by(.fields.customfield_10300 // "NO-EPIC")[] | "\(.[0].fields.customfield_10300 // "NO-EPIC")\t\(length)"' "$F" | sort -t$'\t' -k2 -rn
```

### Bullet lines, grouped by epic (functional, excludes Testing + Cancelled)

Reliable, typo-free key+summary lines — paste into the dev file under your thematic sections.

```bash
jq -r '
  .issues
  | map(select(.fields.status.name != "Cancelled" and .fields.customfield_10300 != "MON-3485"))
  | group_by(.fields.customfield_10300 // "NO-EPIC")
  | .[]
  | "### \(.[0].fields.customfield_10300 // "NO-EPIC") [\(length)]",
    ( .[] | "- \(.key) (https://jira.astralinux.ru/browse/\(.key)) - \(.fields.summary)" )
' "$F"
```

### Testing epic (MON-3485) — for the dev-file Testing section

```bash
jq -r '
  .issues
  | map(select(.fields.customfield_10300 == "MON-3485" and .fields.status.name != "Cancelled"))
  | sort_by(.key)
  | .[]
  | "- \(.key) (https://jira.astralinux.ru/browse/\(.key)) - \(.fields.summary)"
' "$F"
```

### Key-coverage check (step 5 — mandatory before delivery)

```bash
DEST="analytics-hub/internal_docs/docs/release-notes/YYYY-MM-DD-release-notes-dev.md"

# expected: every non-Cancelled key
jq -r '.issues[] | select(.fields.status.name != "Cancelled") | .key' "$F" | sort > /tmp/expected.txt

# actual unique keys in the dev file
grep -oE 'MON-[0-9]+' "$DEST" | sort -u > /tmp/actual.txt

comm -23 /tmp/expected.txt /tmp/actual.txt   # missing — must be empty
comm -13 /tmp/expected.txt /tmp/actual.txt   # extra   — must be empty

# duplicates: each listed issue appears twice (bullet prefix + URL); ≠2 means a mis-list
grep -oE 'MON-[0-9]+' "$DEST" | sort | uniq -c | awk '$1 != 2 {print}'   # must be empty
```

All three outputs empty ⇒ every issue listed exactly once.

## Epic → section map

Resolve epic keys to names with `mcp__jira__batch_get_issues(issue_keys=[...], fields=["summary"])`. Current MON epics:

| Epic | Name | Goes to |
|---|---|---|
| MON-3485 | Эпик для тестирования | **Testing** — dev file only; exclude from changelog + marketing |
| MON-3981 | Monitoring K8S | Мониторинг Kubernetes |
| MON-3970 | BTM | Мониторинг бизнес-транзакций |
| MON-3875 | Мониторы | Мониторы |
| MON-3877 | Метрики / Дашборды | Дашборды и метрики |
| MON-3878 | Логи | Логи / гибкая фильтрация логов |
| MON-3879 | Трейсы | Трейсы |
| MON-3880 | Агент | Агент |
| MON-3882 | Лицензирование | Лицензии |
| MON-3883 | Управление доступом | Управление доступом |
| MON-3884 | Инфраструктура | Инфраструктура (dev + changelog; internal-only items skip marketing) |
| MON-3886 | SNMP / IPMI | Сигналы / гибкая фильтрация сигналов |
| MON-3278 | Security | Security / Безопасность |

Issues with no epic (`NO-EPIC`) — classify by summary + components + labels. Re-verify this table each release: epics drift.

## Three file templates

Filename date = release date. Replace `X.Y.Z`, the date, and content.

### dev — `YYYY-MM-DD-release-notes-dev.md`

```markdown
# Release Notes v.X.Y.Z
**Дата релиза:** YYYY-MM-DD

---

## Added

### <Flagship / feature>

<1–2 sentence description>

- MON-XXXX (https://jira.astralinux.ru/browse/MON-XXXX) - <summary>
- MON-YYYY (https://jira.astralinux.ru/browse/MON-YYYY) - <summary>

---

## Changed

### <Subsection>

- MON-XXXX (...) - ...

---

## Fixed

### <Subsection>

- MON-XXXX (...) - ...

---

## Security

- MON-XXXX (...) - ...

> _Зависимостные уязвимости (Go/JS-deps) в Done-задачах fixVersion обычно не отражены — едут через инфру/CI без отдельных тикетов MON. Если есть список закрывших CVE — добавить сюда._

---

## Testing

- MON-XXXX (...) - ...

---

## Known Issues

На данный момент известных проблем нет.

## Breaking Changes

В этом релизе Breaking changes отсутствуют.
```

### changelog — `YYYY-MM-DD-changelog.md`

Style of `docs/source/changelog.md` (NOT Keep a Changelog). No Jira links. Exclude Testing, infra-internal, research.

```markdown
# Изменения

## X.Y.Z

### Новые возможности

- **<Feature>** — <развёрнутое предложение>

### Изменения

#### <Subsection>

- <пункт>

### Bug fixes

- **Исправлено: кратко** — <развёрнутое описание>

### Исправления безопасности

- <пункт>
```

Header is `# Изменения` (not «Changelog»); version is `## X.Y.Z` (no date, no brackets); each item starts with a **bold lead** + em-dash + description; subsections via `####`.

### marketing — `YYYY-MM-DD-release-notes-marketing.md`

Genre: release-notes/анонс — density = value, telegraph, strong position, one thought per 3–5 sentences. Run `infostyle-critic` (step 6) before delivery.

```markdown
# Мониторинг v.X.Y.Z — <flagship headline>

## Что нового в релизе?

<3–4 sentence annotation. Lead with the biggest flagship.>

---

# Ключевые возможности

## <Flagship 1>

<2–3 sentences, verb-led, concrete.>

### Возможности:
- <concrete bullet — new detail, not a restatement of the paragraph>
- ...

## <Flagship 2 / 3 / ...>

---

# Улучшения

## <Subsection>

<paragraph, active verbs>

---

# Безопасность

<what Jira shows; honest caveat if dep-vuln list is missing>

---

# Исправления

<one general paragraph, grouped; do not enumerate every fix>

---

# Итоги

- **N** крупные новые возможности
- **N** задачи выполнено
- **N** исправление безопасности
- **десятки** исправлений в мониторах и трейсах

**Астра Мониторинг v.X.Y.Z** доступен для обновления.
```

Marketing bullets must add a detail the paragraph did not say — a bullet that restates the paragraph is padding, the critic will flag it.
