# Как пользоваться AM Skills

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone %%AM_SKILLS_URL%% ~/Documents/Code_projects/am-skills
   ```
2. Запустите установщик — он поставит симлинки в `~/.claude/skills/` (глобально):
   ```bash
   cd ~/Documents/Code_projects/am-skills
   ./link.sh
   ```
3. Перезапустите Claude Code.

Скиллы появляются как слеш-команды и срабатывают по триггерам из [`_INDEX.md`](_INDEX.md).

## Как звать скилл

Опишите задачу словами или вызовите слеш-команду:

- «изучи фичу X», «как работает X» → `/am-research`
- «прожарь документацию», «найди неточности» → `/am-grill-docs`
- «оцени фичу», «стоит ли делать» → `/am-grill-feature`
- «напиши jtbd», «заголовок задачи» → `/jtbd`
- «поправь стиль», «напиши текст» → `/infostyle`
- «боли из демо», «проанализируй встречу» → `/am-pain-mining`
- «напиши требования», «подготовь аналитику» → `/am-write-specs`

Не грузите всё сразу — берите скилл под конкретную задачу.

## Обновление

```bash
cd ~/Documents/Code_projects/am-skills
git pull
./link.sh
```

## NMT (JTBD-методология Ивана Замина) — отдельно, опционально

Скиллы `/nmt-chat`, `/nmt-diagnose` и другие NMT **не входят** в am-skills: они связаны с внешним каноном (лицензия CC BY-NC-SA), который мы не перераспространяем. Поставьте их сами из первоисточника:

```bash
cd ~/Documents/Code_projects
git clone --depth 1 https://github.com/zamesin/Next-Move-Theory-Canon-and-Skills.git
```

Затем следуйте инструкции внутри клона — он сам линкует канон и скиллы в проект.

## Engineering-скиллы (Matt Pocock) — отдельно

`tdd`, `code-review`, `diagnosing-bugs`, `wayfinder`, `implement`, `research`, `prototype` и другие engineering-процедуры **не входят** в am-skills: это набор Matt Pocock (`github.com/mattpocock/skills`, лицензия MIT). Каждый ставит его сам с upstream — так мы не форкаем чужой контент и всегда synced с обновлениями автора.

```bash
# Поставить весь набор:
npx skills add mattpocock/skills

# Почистить личное и устаревшее, не нужное в командной работе:
npx skills remove edit-article obsidian-vault scaffold-exercises writing-beats \
  writing-fragments writing-shape loop-me wizard migrate-to-shoehorn claude-handoff \
  teach design-an-interface qa request-refactor-plan ubiquitous-language grill-me \
  find-skills -g -y
```

Когда какой engineering-скилл звать — в `meta/skills-guide.md` мета-репо Astra.

## Контекст Astra

Скиллы — это общий слой возможностей. Контекст продукта (архитектура, реестр исследований, реестр возможностей, подход мета-репо) живёт в мета-репо Astra. Откройте `HARNESS.md` в корне Astra — там описано, как скиллы сочетаются с подходом мета-репо и с чего начать день-1 по ролям (аналитик, сейлз, продукт).
