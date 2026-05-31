# Visual Channel

Визуальный канал — **независимый источник знаний** (диаграммы, модели, демо), а не иллюстрации к транскрипту. ROI визуала зависит от типа видео.

---

## Три уровня

| Уровень | Типы видео | Что делать | Почему |
|---------|-----------|-----------|--------|
| **Полный** | Tutorial/Demo, Review/Analysis, Short/Clip | Скачать → ffmpeg → filter → MCP классификация → включить в документ | Визуал = основной источник знаний |
| **Лёгкий** | Lecture/Educational | Скачать → ffmpeg → filter → кадры в `keyframes/` | Спикер озвучивает слайды — визуал подтверждает, а не добавляет |
| **Пропустить** | Interview/Podcast, Vlog/Narrative | Ничего не делать | Talking head, визуальных знаний нет |

**Лёгкий режим для лекций — обоснование:** Тест на 40-мин лекции: ~55K токенов → 3 из 14 кадров содержали уникальное знание. ROI: 5-10% знаний за 60-70% времени обработки. Кадры сохраняются для анализа по запросу.

---

## Полный уровень (Tutorial/Demo, Review, Short)

### Шаги

1. Скачать видео: `yt-dlp -f "best[height<=720]" URL -o video.mp4`
2. Извлечь кадры: `ffmpeg -i video.mp4 -vf "select=gt(scene\,0.4)" -vsync vfr keyframes/scene_%04d.png`
3. Удалить talking heads: `python3 ~/.claude/skills/video-knowledge-extraction/scripts/filter-talking-heads.py keyframes/ --delete --verbose`
4. MCP-классификация оставшихся кадров (batch по 5-10):
   > "Classify these 5 video frames. For each: talking head (skip) or contains visual knowledge (describe). Return as numbered list."
5. Для каждого кадра, включаемого в документ — **Read tool** проверка:
   - **Условие A:** Нет человека крупным планом, содержимое читаемо
   - **Условие B:** Содержимое совпадает с темой секции, куда помещается
6. Результат: индекс визуальных знаний + inline-изображения

### Threshold по типу видео

| Тип | Threshold | Почему |
|-----|-----------|--------|
| Tutorial/Demo | `0.4` | Частая смена экрана |
| Review/Analysis | `0.4` | Графики и скриншоты |
| Short/Clip | periodic каждые 30 сек | Короткое видео — periodic лучше |

### Batch классификация через MCP

Группировать кадры по 5-10 в один вызов `mcp__zai-mcp-server__analyze_image`:
> "Classify these 5 video frames. For each: talking head (skip) or contains visual knowledge (describe). Return as numbered list."

### Two-pass для длинных видео (>30 мин)

```
Pass 1 (coarse): 1 кадр каждые 120 сек → MCP классификация → найти «интересные» регионы
Pass 2 (fine): scene-detection ТОЛЬКО в интересных регионах → 30-50 кадров вместо 150+
```

### Скрипт vs Read tool

`filter-talking-heads.py` ловит ~60% talking heads (close-ups), но пропускает split-view (спикер + слайд — формат YC/TED) и даёт false negatives. Для YC/TED-формата скрипт может удалить 0 кадров — **вся ответственность на Read tool проверке**.

**Скрипт = фильтр первого прохода, Read tool = финальная проверка.**

---

## Лёгкий уровень (Lecture)

```bash
yt-dlp -f "best[height<=720]" URL -o video.mp4
ffmpeg -i video.mp4 -vf "select=gt(scene\,0.5)" -vsync vfr keyframes/scene_%04d.png
python3 ~/.claude/skills/video-knowledge-extraction/scripts/filter-talking-heads.py keyframes/ --delete --verbose
```

Кадры лежат в `keyframes/`. **Не классифицировать, не включать в документ.**

В документе знаний секция «Визуальные знания»:
> «Кадры извлечены в `keyframes/` ({N} файлов). Визуальный анализ не проводился (тип видео: Lecture). Запросите анализ при необходимости.»

---

## Пропустить (Interview, Vlog)

Не скачивать видео, не извлекать кадры. Секция «Визуальные знания»:
> «Недоступно (тип видео: Interview/Podcast — визуальных знаний нет)»

---

## Inline-изображения (только Полный уровень)

Изображения встраиваются **рядом с соответствующим знанием**, не ломая чтение:

- **Максимум 1 изображение** между двумя абзацами текста
- **Текст до и после** каждого изображения. Стена из 3+ изображений = нарушение
- **Секция «Визуальные знания» обязательна** — inline-изображения дополняют, не заменяют
- **Только со значимым визуальным содержанием** — talking head, пустой слайд, общие фото не включать

**Проверка перед включением** (Read tool для каждого кадра):
- Условие A: нет человека крупным планом, содержимое читаемо
- Условие B: содержимое совпадает с темой секции
- Оба обязательны. Невыполнение любого = кадр не включается
