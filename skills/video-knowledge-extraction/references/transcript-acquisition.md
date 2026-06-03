# Transcript Acquisition

Получение чистого транскрипта из любого источника.

---

## Матрица источников

| Источник | Транскрипт | Визуальный канал |
|----------|------------|-------------------|
| **YouTube URL** | yt-dlp субтитры → you-tldr → parakeet-mlx | Доступен (по типу видео) |
| **Локальное видео** (.mp4, .mkv, .mov) | parakeet-mlx → WhisperNotes | Доступен (по типу видео) |
| **Транскрипт** (.srt, .vtt, .txt) | Прямое чтение | Недоступен |
| **Только аудио** (.mp3, .m4a) | parakeet-mlx → WhisperNotes | Недоступен |

---

## YouTube: цепочка fallback

### 1. yt-dlp субтитры (быстрее всего)

Проверить наличие субтитров → скачать → очистить.

```bash
# Проверить доступные субтитры
yt-dlp --list-subs URL

# Скачать ручные субтитры
yt-dlp --write-sub --sub-lang en,ru --convert-subs srt URL

# Скачать автогенерированные (если ручных нет)
yt-dlp --write-auto-sub --sub-lang en,ru --convert-subs srt URL
```

**Очистка:**
- Ручные субтитры (VTT): `sed 's/<[^>]*>//g' subtitles.vtt > clean.txt`
- Автосубтитры (SRT): rolling captions → `srt-clean.py` (см. ниже)

### 2. you-tldr (fallback #1)

`you-tldr.com/transcript/{video_id}` — быстрый, чистый результат. Нужен интернет и доступ к сервису.

### 3. parakeet-mlx (fallback #2, или основной для локальных файлов)

NVIDIA Parakeet TDT 0.6B v3. 25 языков, точность Whisper Large V3, скорость ~30x realtime на Apple Silicon.

```bash
# Установка
uv tool install parakeet-mlx -U

# Использование
parakeet-mlx audio.mp3                        # → SRT (по умолчанию)
parakeet-mlx audio.mp3 --output-format txt    # → чистый текст
parakeet-mlx audio.mp3 --output-format json   # → word-level timestamps
parakeet-mlx audio.mp3 --output-format vtt    # → WebVTT
```

### 4. WhisperNotes (ручной fallback)

Открыть аудио/видео в приложении → экспортировать как SRT/TXT.

**Если все программные методы недоступны** — запросить транскрипт у пользователя: «Не удалось получить транскрипт автоматически. Пожалуйста, предоставьте транскрипт (.srt/.vtt/.txt) или используйте [WhisperNotes](https://apps.apple.com/app/whisper-notes) для ручной транскрипции.»

---

## Извлечение аудио (для parakeet-mlx)

```bash
# Из YouTube
yt-dlp -x --audio-format mp3 URL

# Из локального видео
ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3
```

---

## Очистка rolling captions (YouTube auto-subs)

YouTube auto-captions используют **progressive reveal**: каждый SRT-блок содержит предыдущий текст + новую фразу. Между реальными блоками — «переходные кадры» длительностью ~10мс.

**Структура:**
```
Блок 1:  [00:00 → 00:02.23]  "A few months ago, I wrote a few"        ← реальный
Блок 2:  [00:02.23 → 00:02.24]  "A few months ago, I wrote a few"     ← переходный (10мс, skip)
Блок 3:  [00:02.24 → 00:04.75]  "A few months ago, I wrote a few\nsentences, about four sentences, that"  ← реальный
```

Уникальный контент — **последняя строка** каждого реального блока. Переходные блоки (duration < 100мс) — мусор.

```bash
# Автоматическая очистка
python3 ~/.claude/skills/video-knowledge-extraction/scripts/srt-clean.py subtitles.srt transcript.txt
```

Скрипт автоматически:
- Пропускает переходные кадры (duration < 100мс)
- Извлекает последнюю строку каждого реального блока
- Склеивает orphan-фрагменты (edge case: пустая строка в первом блоке)

**Проверка:** прочитать начало результата — первая фраза не обрезана, фразы не повторяются.

---

## Quality gate (перед extraction)

- [ ] Транскрипт чистый (без HTML-артефактов, без повторов Whisper/rolling captions)
- [ ] Визуальный канал выполнен по уровню (см. visual-channel.md)
- [ ] Длительность видео определена
- [ ] Количество говорящих определено (для интервью/подкастов)
