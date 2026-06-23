# Конвертация книг в Markdown

Используется ТОЛЬКО для форматов, которые агент не может прочитать напрямую: .doc, .docx, .pdf, .rtf, .mobi.
Для epub, fb2, HTML, markdown, txt — конвертация не нужна (см. матрицу в SKILL.md).

---

## Этап 1: Discovery

### 1.1 Анализ структуры файла

- Определить формат (.doc, .docx, .pdf, .rtf, .mobi)
- Проверить метаданные (автор, дата, страницы)
- Определить кодировку

```bash
file book.doc
```

### 1.2 Определение типа содержимого

- Проверить наличие текстового содержимого
- Проверить наличие изображений
- Тип: **текстовый** / **отсканированный** / **смешанный**

```bash
antiword book.doc | head -20
```

### 1.3 Валидация метаданных

- Если < 1000 слов для книги → вероятно отсканированный
- Если файл большой (> 5MB) но слов мало → проверить изображения

---

## Этап 2: Research

### Матрица совместимости методов

| Метод | .doc (OLE2) | .docx | .pdf | .mobi | .rtf | OCR |
|-------|-------------|-------|------|-------|------|-----|
| **pdftotext (poppler)** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **ocrmypdf** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **LibreOffice+Pandoc** | ✅ | ✅ | ⚠️ | ❌ | ✅ | ⚠️ |
| **antiword** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **mammoth** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **calibre ebook-convert** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Tesseract OCR** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |

### Матрица выбора метода

| Формат | Тип содержимого | Метод | Альтернатива |
|--------|----------------|-------|--------------|
| .doc | Текстовый | LibreOffice+Pandoc | antiword |
| .doc | Отсканированный | LibreOffice+Pandoc + OCR | Tesseract OCR |
| .docx | Текстовый | Pandoc | mammoth |
| .docx | Отсканированный | Pandoc + OCR | Tesseract OCR |
| .pdf | Текстовый | `pdftotext` (poppler) | `mutool draw -F txt` |
| .pdf | Отсканированный | `ocrmypdf` | Tesseract OCR |
| .rtf | Любой | `textutil -convert txt` (macOS) | Pandoc |
| .mobi | Любой | calibre `ebook-convert` | — |

---

## Этап 3: Conversion

### pdftotext (для текстового .pdf) — первый выбор

```bash
pdftotext -layout book.pdf book.txt   # -layout сохраняет структуру абзацев и таблиц
head -50 book.txt
```
Если текст «съезжает» или рвётся по колонкам — попробуйте `mutool draw -F txt book.pdf > book.txt`.

### LibreOffice + Pandoc (для .doc, .docx)

```bash
# .doc → .docx → .md
libreoffice --headless --convert-to docx book.doc
pandoc book.docx -o book.md --extract-media=images
head -50 book.md
```

### antiword (альтернатива для текстовых .doc)

```bash
antiword book.doc > book.txt
```

### calibre ebook-convert (для .mobi)

```bash
ebook-convert book.mobi book.epub   # → epub (затем читаем напрямую)
# или
ebook-convert book.mobi book.md     # → markdown
```

### textutil (macOS, для .rtf)

```bash
textutil -convert txt book.rtf -output book.txt
# или через pandoc:
pandoc book.rtf -o book.md
```

### Отсканированные .pdf — `ocrmypdf` (одна команда)

```bash
# Накладывает текстовый слой на PDF, делая его searchable
ocrmypdf -l rus+eng book.pdf book_searchable.pdf
pdftotext -layout book_searchable.pdf book.md
```
Ручной путь через tesseract (если ocrmypdf недоступен): `pdftoppm` → постраничный tesseract → `cat`. Дольше и хуже по качеству сборки — `ocrmypdf` предпочтительнее.

---

## Этап 4: Sanitization

Конвертация через pandoc/calibre часто оставляет артефакты. Очистите результат:

```bash
# Удалить CSS-классы: {.calibre1}, {.bold} и т.д.
sed -E 's/\{(\.[a-zA-Z0-9_ -]+)\}//g' book.md > book_clean.md

# Удалить пустые ::: div-обёртки
sed -E '/^::+:?$/d' book_clean.md > book_clean2.md

# Схлопнуть [[text]{.class}] → text
sed -E 's/\[\[([^]]+)\]\{[^}]+\}\]/\1/g' book_clean2.md > book_clean3.md

# Удалить якоря {#fileposXXX}
sed -E 's/\{#[^}]+\}//g' book_clean3.md > book_final.md
```

---

## Этап 5: Validation

### Структурная валидация

```bash
grep -c "^# " book.md    # заголовки H1
grep -c "^## " book.md   # заголовки H2
grep -c "^### " book.md  # заголовки H3
grep -c "^- " book.md    # списки
grep -c "^|" book.md     # таблицы
grep -c "!\[" book.md    # изображения
file -I book.md           # кодировка (должна быть UTF-8)
```

### Проверка чистоты (после sanitization)

```bash
# Должно быть 0
grep -c "{\." book.md    # CSS-классы
grep -c ":::" book.md    # div-обёртки
grep -c "filepos" book.md # якоря
```

### Качественная валидация

- Файл читаем от начала до конца
- Все заголовки конвертированы, иерархия сохранена
- Списки конвертированы, вложенность сохранена
- Изображения извлечены, ссылки работают
- Количество слов совпадает ±5%

---

## Восстановление структуры глав PDF

`pdftotext` даёт текст, но на дизайнерских PDF (двухколоночных, с врезками) **теряет структуру глав**: заголовки не размечаются, печатное оглавление перемешивается с телом, таблицы «Было/Стало» рассыпаются в линейный текст. Для fan-out «по главам» это блокер. Способы восстановления — по убыванию качества:

1. **Bookmarks / outline PDF** (лучший). Встроенные закладки хранят дерево глав:
   ```bash
   qpdf --show-pages book.pdf                      # диапазоны страниц (если есть qpdf)
   python3 -c "import pypdf as p; print(p.PdfReader('book.pdf').outline)"  # bookmarks
   # или: mutool show book.pdf outline
   ```
   Bookmarks → список (глава, страница) → нарезать `pdftotext -f N -l M` по этим диапазонам. Это даёт чистые семантические чанки.

2. **Печатное оглавление** (если bookmarks пустые). TOC обычно на первых страницах — извлечь `pdftotext -f 1 -l 10` и распарсить «название → страница». На двухколоночных PDF оглавление тоже ломается — сверяйте с чистой копией.

3. **Fallback: чанки по диапазонам страниц** (структура невосстановима). Нарезать `pdftotext -f N -l M` равными диапазонами (~60 страниц). Границы тем будут размыты — **обязательно декларируйте** в метаданных knowledge-файла: `Охват: постранично, структура глав не восстановлена`.

### Санитизация PDF-текста

Дизайнерские PDF добавляют шум, который `pdftotext` не убирает:
- **Колонтитулы и нумерация страниц** повторяются — вырезайте по регулярке.
- **Вклеенное оглавление** внутри body выглядит как подзаголовки — отличайте по повторяющимся паттернам (строка + изолированный номер страницы).
- **Справочные перечни** (списки стоп-слов, словари) — справочный аппарат, не извлекайте каждое слово; сошлитесь на перечень целиком.
- **Таблицы** (`-layout` сохраняет хрупко) — для критичных таблиц проверяйте вручную.

---

## Установка инструментов

```bash
brew install poppler          # pdftotext, pdftoppm, pdfimages
brew install ocrmypdf         # OCR-слой на PDF одной командой
brew install libreoffice pandoc
brew install antiword
brew install tesseract tesseract-lang
brew install calibre
```
