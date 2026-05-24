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
| **LibreOffice+Pandoc** | ✅ | ✅ | ✅ | ❌ | ✅ | ⚠️ |
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
| .pdf | Текстовый | Pandoc | — |
| .pdf | Отсканированный | Tesseract OCR | — |
| .rtf | Любой | `textutil -convert txt` (macOS) | Pandoc |
| .mobi | Любой | calibre `ebook-convert` | — |

---

## Этап 3: Conversion

### LibreOffice + Pandoc (для .doc, .docx, .pdf)

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

### Отсканированные документы

```bash
# Извлечь изображения страниц
libreoffice --headless --convert-to pdf book.doc
pdfimages -all book.pdf page

# OCR
for page in page-*.ppm; do
    tesseract $page ${page%.ppm} -l rus+eng
done

# Объединить
cat page-*.txt > book.md
```

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

## Установка инструментов

```bash
brew install libreoffice pandoc
brew install antiword
brew install tesseract tesseract-lang
brew install calibre
```
