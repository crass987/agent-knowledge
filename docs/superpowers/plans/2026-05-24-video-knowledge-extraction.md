# Video Knowledge Extraction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone skill at `skills/video-knowledge-extraction/SKILL.md` that extracts structured knowledge from video content (YouTube, local files, transcripts).

**Architecture:** 4-phase pipeline — Source Acquisition (dual-channel: audio + visual) → Content Mapping (infer virtual chapters) → Knowledge Extraction (reused cognitive quality framework + compression principle) → Output (timestamped knowledge document). Skill mirrors the book-knowledge-extraction pattern but is rebuilt around video's lower information density and temporal structure.

**Tech Stack:** Markdown skill files, yt-dlp, ffmpeg, Whisper, MCP vision tools (analyze_image, extract_text_from_screenshot).

**Design spec:** `docs/superpowers/specs/2026-05-24-video-knowledge-extraction-design.md`

---

## File Structure

```
skills/video-knowledge-extraction/
├── SKILL.md                          # Main skill file (~300-400 lines)
└── references/
    ├── templates.md                  # Knowledge document template + per-category formats
    └── quality-checklists.md         # Pre/during/post extraction checklists

Files to modify in other locations:
├── skills/_INDEX.md                  # Add video skill entry to trigger table
└── AGENTS.md                         # Add video skill entry to router table
```

---

### Task 1: Create skill directory and SKILL.md with frontmatter and JTBD scenarios

**Files:**
- Create: `skills/video-knowledge-extraction/SKILL.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p skills/video-knowledge-extraction/references
```

- [ ] **Step 2: Write SKILL.md — frontmatter, description, and JTBD scenarios**

Write the beginning of the skill file. This includes YAML frontmatter, a one-line description, and 2 JTBD scenarios (single video knowledge extraction, and video + transcript as reusable artifacts). Follow the book skill's pattern exactly — the structure should feel familiar.

Content to write:

```markdown
---
name: video-knowledge-extraction
description: Извлечение структурированных знаний из видео (YouTube, локальные файлы, транскрипты) — идеи, проблемы, методология, инсайты с компрессией и временными метками
version: 1
---

# Video Knowledge Extraction

Извлечение структурированных знаний из видео для практического применения.

---

## JTBD-сценарии

### Сценарий 1: Извлечение знаний из видео

**Когда** пользователь хочет вычленить главные идеи, проблемы, методологию из видео,
**Роль** исследователь, методолог или практик,
**Хочет** получить структурированный набор знаний для практического применения,
**Закрывает потребность** в вооружении лучшей методологией из видеоконтента,
**Мы показываем** процесс извлечения и структурирования знаний → основное содержание этого файла

### Сценарий 2: Подготовка транскрипта и визуальных материалов

**Когда** пользователь хочет конвертировать видео в текстовый транскрипт с извлечёнными ключевыми кадрами,
**Роль** исследователь или аналитик,
**Хочет** получить читабельный транскрипт и индекс визуальных моментов для повторной обработки,
**Закрывает потребность** в удобном формате для повторного извлечения знаний или смены шаблона,
**Мы показываем** процесс получения и очистки транскрипта → Фаза 0 этого файла
```

- [ ] **Step 3: Commit**

```bash
git add skills/video-knowledge-extraction/SKILL.md
git commit -m "feat(video-skill): add frontmatter and JTBD scenarios"
```

---

### Task 2: Write Phase 0 — Source Acquisition

**Files:**
- Modify: `skills/video-knowledge-extraction/SKILL.md` (append after JTBD scenarios)

- [ ] **Step 1: Append Phase 0 to SKILL.md**

Append this content after the JTBD scenarios section:

```markdown

---

## Фаза 0: Приобретение источника

### Матрица источников

| Источник | Аудио-канал | Визуальный канал | Инструменты |
|----------|-------------|-------------------|-------------|
| **YouTube URL** | yt-dlp субтитры → Whisper fallback | yt-dlp thumbnails + извлечение ключевых кадров | yt-dlp, ffmpeg |
| **Локальное видео** (.mp4, .mkv, .mov) | Whisper транскрипция | Ключевые кадры через ffmpeg | Whisper, ffmpeg |
| **Транскрипт** (.srt, .vtt, .txt) | Прямое чтение | Недоступно (если видео не предоставлено) | Read tool, MCP vision |
| **Только аудио** (.mp3, .m4a) | Whisper транскрипция | Недоступно | Whisper |

### Аудио-канал

1. Проверить наличие субтитров (yt-dlp `--list-subs`)
2. Если есть: скачать `.vtt`/`.srt`, очистить HTML-артефакты временных меток
3. Если нет: извлечь аудио → Whisper (`base` для скорости, `large` для технического/многоязычного контента)
4. Результат: чистый транскрипт с временными метками на уровне предложений

```bash
# YouTube: проверить и скачать субтитры
yt-dlp --list-subs URL
yt-dlp --write-sub --sub-lang en,ru --convert-subs srt URL
yt-dlp --write-auto-sub --sub-lang en,ru --convert-subs srt URL  # автогенерированные

# Извлечение аудио (если субтитров нет)
yt-dlp -x --audio-format mp3 URL
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3  # из локального файла

# Whisper транскрипция
whisper audio.mp3 --model base --language en --output_format srt
whisper audio.mp3 --model large --language en --output_format srt  # для точности

# Очистка VTT/SRT
sed 's/<[^>]*>//g' subtitles.vtt > clean.txt
```

### Визуальный канал

1. Извлечь ключевые кадры: каждые 60 секунд + при смене сцены (ffmpeg `scene=0.3`)
2. Анализировать кадры инструментами MCP vision (`mcp__zai-mcp-server__analyze_image`, `mcp__zai-mcp-server__extract_text_from_screenshot`)
3. Классифицировать каждый кадр: diagram/chart, code on screen, slide presentation, demo, talking head (игнорировать)
4. Результат: Индекс визуальных моментов `{timestamp} → {type} → {description}`

```bash
# Извлечение ключевых кадров
ffmpeg -i video.mp4 -vf "fps=1/60" keyframes/periodic_%04d.png           # каждые 60 сек
ffmpeg -i video.mp4 -vf "select=gt(scene\,0.3)" -vsync vfr keyframes/scene_%04d.png  # смена сцены

# YouTube: скачать видео для анализа кадров
yt-dlp -f "best[height<=720]" URL -o video.mp4
```

**Классификация визуальных кадров через MCP:**

Для каждого извлечённого кадра — вызвать `mcp__zai-mcp-server__analyze_image` с промптом:
> "Classify this video frame as one of: diagram/chart, code on screen, slide presentation, live demo, talking head. If it's not a talking head, describe what visual knowledge it contains."

Talking head кадры игнорируются — они не несут визуальных знаний.

### Логика принятия решения

1. YouTube URL → скачать субтитры (если есть), иначе Whisper → скачать видео для ключевых кадров
2. Локальное видео → Whisper + ffmpeg ключевые кадры
3. Транскрипт (.srt/.vtt/.txt) → прямое чтение, визуальный канал недоступен
4. Только аудио → Whisper, визуальный канал недоступен

### Шлюз качества (перед Фазой 1)

- [ ] Транскрипт чистый (без HTML-артефактов субтитров, без повторов Whisper)
- [ ] Визуальный индекс классифицирует каждый извлечённый кадр
- [ ] Длительность видео определена
- [ ] Количество говорящих определено (для интервью/подкастов)
```

- [ ] **Step 2: Commit**

```bash
git add skills/video-knowledge-extraction/SKILL.md
git commit -m "feat(video-skill): add Phase 0 — source acquisition with dual-channel pipeline"
```

---

### Task 3: Write Phase 1 — Content Mapping

**Files:**
- Modify: `skills/video-knowledge-extraction/SKILL.md` (append after Phase 0)

- [ ] **Step 1: Append Phase 1 to SKILL.md**

```markdown

---

## Фаза 1: Картирование контента

В отличие от книг, видео не имеют оглавления. Навык должен **вывести** структуру.

### 1.1 Классификация типа видео

Определите тип — это определяет стратегию извлечения:

| Тип | Описание | Стратегия извлечения |
|-----|----------|---------------------|
| **Lecture/Educational** | Один спикер обучает теме | Временные темы, слайды как структурные маркеры |
| **Interview/Podcast** | Два или более спикера в разговоре | Тематические повороты, точки согласия/несогласия |
| **Review/Analysis** | Оценка продукта/идеи/события | Критерии оценки, выводы, рекомендации |
| **Tutorial/Demo** | Пошаговая демонстрация | Последовательность действий, визуальные демо как основное знание |
| **Vlog/Narrative** | Личная история, опыт | Таймлайн, ключевые повороты, lessons learned |
| **Short/Clip** | До 3 минут, высокая плотность | Одна тема, быстрое извлечение |

Результат классификации записывается в метаданные документа знаний.

### 1.2 Вывод структуры (Виртуальные главы)

Из транскрипта определить тематические сегменты:

- Искать переходные фразы ("Now let's talk about...", "Moving on to...", "Переходя к...")
- Визуальные изменения (новый слайд, переключение на демо) как границы сегментов
- Для интервью: смена говорящего как потенциальные границы
- Результат: Список тематических сегментов с временными метками начала и конца

```markdown
## Виртуальные главы

- [00:00–02:30] Introduction and context
- [02:30–08:15] Core concept: X
- [08:15–12:00] Case study: Y
- [12:00–15:00] Practical application
- [15:00–18:30] Q&A / Discussion
```

### 1.3 Оценка информационной плотности

Оценить, какая часть видео — контент vs. заполнитель:
- **Высокая плотность:** Лекция с плотным материалом, мало повторений. Компрессия умеренная.
- **Средняя плотность:** Типичный подкаст/интервью. Компрессия стандартная.
- **Низкая плотность:** Влог, много повторений, отклонения от темы. Агрессивная компрессия.

Оценка плотности определяет уровень компрессии в Фазе 2 — видео с низкой плотностью сжимаются агрессивнее.

**Для чего:** 30-минутное видео с высокой плотностью может дать документ знаний на 5 минут чтения. То же видео с низкой плотностью — на 2-3 минуты. Цель: документ всегда плотнее источника.
```

- [ ] **Step 2: Commit**

```bash
git add skills/video-knowledge-extraction/SKILL.md
git commit -m "feat(video-skill): add Phase 1 — content mapping with virtual chapters"
```

---

### Task 4: Write Phase 2 — Knowledge Extraction

**Files:**
- Modify: `skills/video-knowledge-extraction/SKILL.md` (append after Phase 1)

- [ ] **Step 1: Append Phase 2 to SKILL.md**

```markdown

---

## Фаза 2: Извлечение знаний

### 2.1 Когнитивное качество (Cognitive Quality)

Каждое извлечённое знание проверяется по четырём принципам — тем же, что и в навыке для книг:

**Принцип 1: Контекст и Применимость**
- Целевая аудитория: Novice / Pro
- Состояние читателя: Crisis / Growth / Stacking
- Цель потребления: Solve / Learn / Confirm

**Принцип 2: Типология Пользы (Utility Taxonomy)**
- **Функциональная:** Улучшает процесс, экономит ресурсы
- **Социальная:** Повышает статус, авторитет, аргументацию
- **Психологическая:** Снижает тревогу, даёт уверенность, развлекает

**Принцип 3: Синтаксис Действия (Actionable Syntax)**
- Тест на визуализацию: Можно ли изобразить концепт как сцену?
- Грамматика: Субъект + Глагол + Объект. Не абстракции.
- Приземление: Абстрактные принципы должны иметь конкретные примеры

**Принцип 4: Armament Test**
Можно ли использовать это знание как аргумент в дискуссии? Банальности ("надо планировать") не проходят.

### 2.2 Категории извлечения (адаптированные для видео)

| Категория | Адаптация для видео |
|-----------|-------------------|
| **Главные идеи** | Компрессия повторений — спикеры повторяют ключевые мысли 2-3 раза. Извлечь один раз. |
| **Проблемы** | Отметить, где в видео проблема визуально демонстрируется (демо, пример) |
| **Предпосылки** | В видео предпосылки часто неявные — спикер принимает их без озвучивания |
| **Последствия** | Без изменений |
| **Методология** | Для туториалов/демо: визуальная последовательность ЕСТЬ методология. Извлечь шаги из визуального канала. |
| **Инсайты** | Пометить: был инсайт вербальным (🗣) или визуальным (👁) |

### 2.3 Принцип компрессии

**Правило:** Документ знаний должен быть плотнее исходного видео. 30-минутное видео → документ знаний на 3-5 минут чтения.

Это ключевое отличие от навыка для книг (где документ ~1:10 размера книги). Видео имеет более низкую информационную плотность, поэтому компрессия агрессивнее (~1:6–1:10 времени чтения).

Как применять компрессию:
- Удалить словесные заполнители, отклонения от темы, повторения
- Преобразовать разговорную формулировку в письменную точность
- Консолидировать одну и ту же идею, выраженную несколько раз, в одно ясное утверждение
- Сохранять только уникальные, применимые знания

**Тест компрессии:** Если из документа знаний можно восстановить ход видео (кто что сказал, в каком порядке) — компрессия недостаточная. Документ должен содержать только знания, а не хронологию.

### 2.4 Процесс извлечения по категориям

Формат для каждой извлечённой единицы знания — см. `references/templates.md`.

Процесс для каждой категории:

1. **Главные идеи:** Прочитать каждую виртуальную главу → выделить 1-3 главные идеи → записать с компрессией → пометить источник (🗣/👁)
2. **Проблемы:** Выделить проблемы, которые видео решает/описывает → записать с контекстом и решениями → связать с визуальными демонстрациями
3. **Предпосылки:** Выделить явные и неявные предположения спикера → определить условия применимости → записать
4. **Последствия:** Выделить описанные и потенциальные последствия → записать
5. **Методология:** Выделить пошаговые процессы → для туториалов — извлечь из визуального канала → записать в формате инструкций
6. **Инсайты:** Выделить неожиданные идеи → пометить источник (🗣 verbal / 👁 visual) → записать с применением
```

- [ ] **Step 2: Commit**

```bash
git add skills/video-knowledge-extraction/SKILL.md
git commit -m "feat(video-skill): add Phase 2 — knowledge extraction with compression principle"
```

---

### Task 5: Write Phase 3 — Output and remaining sections

**Files:**
- Modify: `skills/video-knowledge-extraction/SKILL.md` (append after Phase 2)

- [ ] **Step 1: Append Phase 3, Quality Checklist, Output, Tools, and Action Plan to SKILL.md**

```markdown

---

## Фаза 3: Структурирование знаний

### 3.1 Шаблон документа знаний

Полный шаблон → `references/templates.md`. Краткий вид:

```markdown
# {Название видео} — Документ знаний

## Метаданные
- **Источник:** YouTube URL / путь к локальному файлу
- **Канал:** Название канала
- **Дата публикации:** Дата
- **Длительность:** XX:XX
- **Тип:** Lecture / Interview / Review / Tutorial / Vlog / Short
- **Плотность:** High / Medium / Low
- **Язык:** Язык оригинала

## Краткое содержание (3-5 предложений)

## Виртуальные главы
- [MM:SS–MM:SS] Тема 1
- ...

## Главные идеи
[Извлечено, сжато, с метками источника: 🗣 verbal / 👁 visual]

## Проблемы и решения

## Методология в действии
[Для туториалов/демо: последовательность шагов из визуального + аудио-канала]

## Ключевые инсайты

## Визуальные знания
[Диаграммы, схемы, демо — описано или связано с файлами ключевых кадров]

## Применимость
[Кто, в какой ситуации, для чего]
```

### 3.2 Организация файлов

```
knowledge-base/
└── videos/
    └── {video-title}/
        ├── source/
        │   └── {video-file or URL-reference.md}
        ├── transcript.txt
        ├── keyframes/
        │   ├── 00-02-30_diagram.png
        │   └── 00-15-00_demo.png
        └── {video-title}_knowledge.md
```

**Почему так:**
- Плоская структура по названию видео — канал, дата и URL в метаданных документа, а не в пути
- `source/` хранит оригинал для повторного извлечения или смены шаблона
- `keyframes/` — только значимые визуальные кадры (не talking head)
- `transcript.txt` — чистый транскрипт для повторной обработки

---

## Quality Checklist

Полные чеклисты → `references/quality-checklists.md`. Краткий вариант:

### Перед извлечением
- [ ] Источник получен (транскрипт + визуальный индекс, если видео доступно)
- [ ] Тип видео определён
- [ ] Виртуальные главы идентифицированы
- [ ] Информационная плотность оценена
- [ ] Оригинал видео/транскрипта сохранён в `source/`

### После извлечения
- [ ] Каждое знание проходит Armament Test
- [ ] Контекст определён (для кого, в какой ситуации)
- [ ] Тип пользы определён (Functional/Social/Psychological)
- [ ] Принцип компрессии применён (документ значительно плотнее видео)

### После структурирования
- [ ] Документ знаний следует шаблону
- [ ] Все категории заполнены (где применимо к типу видео)
- [ ] Метаданные полные
- [ ] Практическое применение определено
- [ ] Документ читаем без просмотра исходного видео
- [ ] Оригинал видео/транскрипта сохранён в `source/`

---

## Output

### Результат извлечения знаний

**Язык артефакта:** Финальный документ знаний (`_knowledge.md`) пишется на русском языке. Цитаты из оригинала оставляются на языке оригинала. Названия тем и ключевые термины — на языке оригинала, с русским объяснением.

**Файлы (в папке видео):**
1. `{video-title}_knowledge.md` — извлечённые знания
2. `source/{original-file or URL-reference}` — архив оригинала
3. `transcript.txt` — чистый транскрипт
4. `keyframes/` — извлечённые визуальные кадры (если применимо)

**Критерии готовности:**
- Знания структурированы по категориям
- Компрессия применена (3-5 мин чтения для 30-мин видео)
- Условия применения описаны
- Связи между идеями указаны
- Документ читаем без исходного видео
- Оригинал сохранён в `source/`

---

## Tools

```bash
# YouTube: субтитры и информация
yt-dlp --list-subs URL
yt-dlp --write-sub --sub-lang en,ru --convert-subs srt URL
yt-dlp --write-auto-sub --sub-lang en,ru --convert-subs srt URL
yt-dlp --write-thumbnail URL
yt-dlp -f "best[height<=720]" URL -o video.mp4
yt-dlp -x --audio-format mp3 URL

# Извлечение аудио
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3

# Whisper
whisper audio.mp3 --model base --language en --output_format srt
whisper audio.mp3 --model large --language en --output_format srt

# Ключевые кадры
ffmpeg -i video.mp4 -vf "fps=1/60" keyframes/periodic_%04d.png
ffmpeg -i video.mp4 -vf "select=gt(scene\,0.3)" -vsync vfr keyframes/scene_%04d.png

# Очистка субтитров
sed 's/<[^>]*>//g' subtitles.vtt > clean.txt
```

---

## Action Plan

- [ ] Протестировать навык на 3-5 видео разных типов (лекция, интервью, туториал)
- [ ] Добавить обработку плейлистов (по запросу)
- [ ] Скрипт для автоматического получения транскрипта + ключевых кадров
```

- [ ] **Step 2: Commit**

```bash
git add skills/video-knowledge-extraction/SKILL.md
git commit -m "feat(video-skill): add Phase 3, quality checklist, output, and tools sections"
```

---

### Task 6: Write references/templates.md

**Files:**
- Create: `skills/video-knowledge-extraction/references/templates.md`

- [ ] **Step 1: Write templates.md with knowledge document template and per-category format**

```markdown
# Шаблоны для извлечения знаний из видео

## Шаблон документа знаний

```markdown
# {Название видео} — Документ знаний

## Метаданные
- **Источник:** [YouTube URL / путь к файлу]
- **Канал:** [Название канала]
- **Дата публикации:** [Дата]
- **Длительность:** [XX:XX]
- **Тип:** [Lecture / Interview / Review / Tutorial / Vlog / Short]
- **Плотность:** [High / Medium / Low]
- **Язык:** [Язык оригинала]

## Краткое содержание
[3-5 предложений — о каких знаниях это видео. Не пересказ сюжета, а суть знаний.]

## Виртуальные главы
- [MM:SS–MM:SS] [Тема сегмента]
- [MM:SS–MM:SS] [Тема сегмента]
...

## Главные идеи

### [Идея 1] 🗣 / 👁
[Сжатое описание идеи — что именно утверждается, с конкретикой]
- **Контекст:** [для кого, в какой ситуации]
- **Тип пользы:** [Functional / Social / Psychological]
- **Временная метка:** [MM:SS]

### [Идея 2] 🗣
...

## Проблемы и решения

### [Проблема 1]
- **Описание:** [в чём проблема]
- **Решение:** [что предлагается]
- **Визуальная демонстрация:** [MM:SS — ссылка на keyframe или описание] (если есть)
- **Временная метка:** [MM:SS]

## Методология в действии

### [Процесс/метод 1]
[Пошаговый процесс — формат инструкций, не описаний]

**Шаг 1:** [конкретное действие]
**Шаг 2:** [конкретное действие]
...

**Условия применения:** [когда использовать]
**Источник:** 🗣 [MM:SS] / 👁 [визуальная демонстрация на MM:SS]

## Ключевые инсайты

### [Инсайт 1] 🗣 / 👁
[Неожиданная, контринтуитивная мысль]
- **Почему неочевидно:** [что это опровергает]
- **Практическое применение:** [как использовать]
- **Временная метка:** [MM:SS]

## Визуальные знания

### [Диаграмма/схема/демо на MM:SS]
![Описание](keyframes/{filename}.png)
[Описание визуального знания — что изображено, какую идею поддерживает, почему важно]

## Применимость
- **Для кого:** [кто может применить эти знания]
- **В какой ситуации:** [конкретные сценарии]
- **Для чего:** [какую потребность закрывают]
```

---

## Формат извлечения знаний по категориям

**Шаблон для каждой извлечённой единицы знания:**

```markdown
### [Название/тема] 🗣 / 👁

**Контекст:**
- **Виртуальная глава:** [какой сегмент]
- **Временная метка:** [MM:SS]

**Содержание:**
[Описание идеи/проблемы/методологии — сжатое, точное]

**Практическое применение:**
- **Когда использовать:** [условия]
- **Как применять:** [процесс]
- **Ожидаемый результат:** [что получим]

**Связи:**
- Связано с: [другие идеи]
- Противоречит: [если есть]
- Дополняет: [если есть]

**Цитата:**
"[прямая цитата из видео на языке оригинала]"
```

---

## Адаптация по типу видео

### Lecture/Educational
- Секции «Главные идеи» и «Ключевые инсайты» — основные
- Слайды = визуальные знания (диаграммы, модели)
- Методология — если лекция практическая

### Interview/Podcast
- Фокус на точки согласия/несогласия спикеров
- Секция «Проблемы» — часто центральная (спикеры обсуждают проблемы)
- Визуальный канал обычно не несёт знаний

### Review/Analysis
- Секция «Проблемы и решения» — основная
- Критерии оценки = методология
- Выводы и рекомендации = главные идеи

### Tutorial/Demo
- Секция «Методология в действии» — центральная
- Визуальный канал = основной источник знаний ( демо на экране)
- Компрессия минимальная — каждый шаг важен

### Vlog/Narrative
- Секция «Ключевые инсайты» — основная (lessons learned)
- Фокус на поворотные моменты и выводы
- Агрессивная компрессия — много нарратива, мало знаний

### Short/Clip
- Одна секция «Главные идеи»
- Быстрое извлечение без детализации
- Минимальный документ знаний
```

- [ ] **Step 2: Commit**

```bash
git add skills/video-knowledge-extraction/references/templates.md
git commit -m "feat(video-skill): add knowledge document template and per-category formats"
```

---

### Task 7: Write references/quality-checklists.md

**Files:**
- Create: `skills/video-knowledge-extraction/references/quality-checklists.md`

- [ ] **Step 1: Write quality-checklists.md**

```markdown
# Контрольные чеклисты для извлечения знаний из видео

## Pre-Acquisition Checklist

- [ ] Определён тип источника (YouTube URL / локальное видео / транскрипт / аудио)
- [ ] yt-dlp установлен и доступен (для YouTube URL)
- [ ] Whisper установлен и доступен (если нет субтитров или локальное видео)
- [ ] ffmpeg установлен и доступен (для ключевых кадров)

## Post-Acquisition Checklist

- [ ] Транскрипт получен (субтитры или Whisper)
- [ ] Транскрипт очищен от HTML-артефактов (если VTT/SRT)
- [ ] Транскрипт не содержит повторов Whisper
- [ ] Ключевые кадры извлечены (если видео доступно)
- [ ] Визуальный индекс создан (каждый кадр классифицирован)
- [ ] Длительность видео определена
- [ ] Количество говорящих определено (для интервью/подкастов)
- [ ] Оригинал сохранён в `source/`

## Content Mapping Checklist

- [ ] Тип видео определён (Lecture / Interview / Review / Tutorial / Vlog / Short)
- [ ] Виртуальные главы идентифицированы (тематические сегменты с временными метками)
- [ ] Информационная плотность оценена (High / Medium / Low)
- [ ] Переходные фразы и визуальные изменения использованы как границы сегментов

## Per-Category Extraction Checklist

### Главные идеи
- [ ] Выделены главные идеи из каждой виртуальной главы
- [ ] Повторения сжаты (одна идея — одна запись)
- [ ] Каждая идея помечена источником (🗣 verbal / 👁 visual)
- [ ] Идеи проходят Armament Test

### Проблемы
- [ ] Выделены проблемы, которые видео решает/описывает
- [ ] Связаны с визуальными демонстрациями (если есть)
- [ ] Записаны с контекстом и решениями

### Предпосылки
- [ ] Выделены явные предположения спикера
- [ ] Выделены неявные предположения (не озвученные, но принимаемые)
- [ ] Определены условия применимости

### Последствия
- [ ] Выделены описанные последствия
- [ ] Определены потенциальные последствия
- [ ] Определены риски применения

### Методология
- [ ] Выделены пошаговые процессы
- [ ] Для туториалов/демо — шаги извлечены из визуального канала
- [ ] Записаны в формате инструкций
- [ ] Определены условия применения

### Инсайты
- [ ] Выделены контринтуитивные, неочевидные мысли
- [ ] Каждый инсайт помечен источником (🗣 / 👁)
- [ ] Инсайты проходят тест: если можно переформулировать как банальность — удалить
- [ ] Практическое применение указано для каждого

## Compression Checklist

- [ ] Документ знаний плотнее исходного видео (3-5 мин чтения для 30-мин видео)
- [ ] Словесные заполнители удалены
- [ ] Разговорные формулировки преобразованы в письменную точность
- [ ] Одна и та же идея, выраженная несколько раз, консолидирована
- [ ] Тест компрессии пройден: из документа НЕЛЬЗЯ восстановить хронологию видео

## Structuring Checklist

- [ ] Документ знаний следует шаблону из `references/templates.md`
- [ ] Все категории заполнены (где применимо к типу видео)
- [ ] Метаданные полные (источник, канал, дата, длительность, тип, плотность, язык)
- [ ] Краткое содержание написано (3-5 предложений)
- [ ] Виртуальные главы с временными метками включены
- [ ] Визуальные знания описаны или связаны с файлами keyframes
- [ ] Практическая применимость определена

## Final Delivery Checklist

- [ ] Файл `{video-title}_knowledge.md` сохранён в папке видео
- [ ] `source/` содержит оригинал видео или ссылку на него
- [ ] `transcript.txt` содержит чистый транскрипт
- [ ] `keyframes/` содержит значимые визуальные кадры (если применимо)
- [ ] Документ читаем без просмотра исходного видео
- [ ] Язык: русский документ, цитаты и термины на языке оригинала
```

- [ ] **Step 2: Commit**

```bash
git add skills/video-knowledge-extraction/references/quality-checklists.md
git commit -m "feat(video-skill): add quality checklists for all phases"
```

---

### Task 8: Register skill in _INDEX.md and AGENTS.md

**Files:**
- Modify: `skills/_INDEX.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add video skill entry to `skills/_INDEX.md`**

Add this row to the trigger table:

```markdown
| video, YouTube, transcript, whisper, knowledge extraction, lecture, podcast | `video-knowledge-extraction/SKILL.md` |
```

- [ ] **Step 2: Add video skill entry to `AGENTS.md`**

Add this row to the Skills router table:

```markdown
| video, YouTube, transcript, whisper, lecture, podcast, knowledge extraction | `skills/video-knowledge-extraction/SKILL.md` |
```

- [ ] **Step 3: Commit**

```bash
git add skills/_INDEX.md AGENTS.md
git commit -m "feat(video-skill): register in _INDEX.md and AGENTS.md router tables"
```

---

### Task 9: Create symlink and validate

**Files:**
- Create: symlink `~/.claude/skills/video-knowledge-extraction` → `skills/video-knowledge-extraction/SKILL.md`

- [ ] **Step 1: Check existing symlink pattern**

```bash
ls -la ~/.claude/skills/ 2>/dev/null
```

Verify how other skills are linked (direct file symlinks or directory symlinks).

- [ ] **Step 2: Create symlink following existing pattern**

If existing skills are linked as files:
```bash
ln -s ~/Documents/Code_projects/agent-knowledge/skills/video-knowledge-extraction/SKILL.md ~/.claude/skills/video-knowledge-extraction.md
```

If existing skills are linked as directories:
```bash
ln -s ~/Documents/Code_projects/agent-knowledge/skills/video-knowledge-extraction ~/.claude/skills/video-knowledge-extraction
```

- [ ] **Step 3: Verify symlink works**

```bash
cat ~/.claude/skills/video-knowledge-extraction.md 2>/dev/null | head -5
# OR
cat ~/.claude/skills/video-knowledge-extraction/SKILL.md 2>/dev/null | head -5
```

Expected: Shows the YAML frontmatter of the skill file.

- [ ] **Step 4: Commit (if any new files created)**

```bash
git status
# Only commit changes in agent-knowledge repo, not the symlink
```

---

## Self-Review

### Spec Coverage

| Spec section | Task |
|---|---|
| Phase 0: Source Acquisition (input matrix, audio/visual pipelines, quality gate) | Task 2 |
| Phase 1: Content Mapping (video types, virtual chapters, density) | Task 3 |
| Phase 2: Knowledge Extraction (quality checks, categories, compression) | Task 4 |
| Phase 3: Output (template, file naming, quality checklist, tools) | Task 5 |
| Templates reference | Task 6 |
| Quality checklists reference | Task 7 |
| Router registration (_INDEX.md, AGENTS.md) | Task 8 |
| Symlink + validation | Task 9 |

### Placeholder Scan

No TBDs, TODOs, or "implement later" patterns found. Every step contains actual content.

### Type Consistency

- Video title used consistently as `{video-title}` across all templates and file naming conventions
- Source labels (🗣/👁) used consistently in Phase 2, templates, and quality checklists
- Video type classification (6 types) consistent between Phase 1, templates, and quality checklists
- Density levels (High/Medium/Low) consistent across all references
