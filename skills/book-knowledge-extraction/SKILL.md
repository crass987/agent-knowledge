---
name: book-knowledge-extraction
description: Convert books (.doc/.docx/.pdf/.fb2) to Markdown and extract structured knowledge — ideas, problems, methodology, insights
---

# Book Conversion and Knowledge Extraction

## Purpose

Convert books from various formats (.doc, .docx, .pdf, .fb2) into readable Markdown, then extract key ideas, problems, prerequisites, consequences, methodology, and insights for practical application.

## When to use

- User wants to convert a book to Markdown for reading or analysis.
- User wants to extract structured knowledge from a book.
- User wants to build a knowledge base from multiple books.

---

## Part 1: Book Conversion

### Step 1 — Discovery (Required)

Determine document type and choose conversion method.

**Analyze the file:**

```bash
# Check file type
file book.doc

# Check metadata
python3 -c "import olefile; ole = olefile.OleFileIO('book.doc'); print(ole.listdir())"
```

**Determine content type:**

| Type | Description | Detection |
|------|-------------|-----------|
| Text | Readable text | `antiword book.doc \| head -20` succeeds |
| Scanned | Page images only | Metadata shows < 1000 words for a book |
| Mixed | Text + images | Both text and images present |

**Validate metadata:**
- Compare word count to file size — large file + few words = likely scanned
- Check encoding

### Step 2 — Research (Required)

Choose method based on format and content type.

**Method compatibility matrix:**

| Method | .doc (OLE2) | .docx | .pdf | Images | Text | OCR |
|--------|-------------|-------|------|--------|------|-----|
| LibreOffice+Pandoc | Yes | Yes | Yes | Yes | Yes | Partial |
| antiword | Yes | No | No | Partial | Yes | No |
| mammoth | No | Yes | No | Partial | Yes | No |
| textract | Partial | Yes | Yes | Partial | Yes | Partial |
| Tesseract OCR | No | No | Yes | Yes | Yes | Yes |

**Selection:**

| Document type | Format | Method | Alternative |
|--------------|--------|--------|-------------|
| Text | .doc | LibreOffice+Pandoc | antiword |
| Scanned | .doc | LibreOffice+Pandoc + OCR | Tesseract |
| Text | .docx | Pandoc | mammoth |
| Scanned | .docx | Pandoc + OCR | Tesseract |
| Text | .pdf | Pandoc | textract |
| Scanned | .pdf | Tesseract OCR | — |

### Step 3 — Conversion

**LibreOffice + Pandoc (recommended):**

```bash
libreoffice --headless --convert-to docx book.doc
pandoc book.docx -o book.md --extract-media=images
```

**antiword (alternative for text-only .doc):**

```bash
antiword book.doc > book.txt
# Requires manual formatting to .md
```

**Scanned documents (OCR):**

```bash
libreoffice --headless --convert-to pdf book.doc
pdfimages -all book.pdf page
for page in page-*.ppm; do
    tesseract $page ${page%.ppm} -l rus+eng
done
cat page-*.txt > book.md
```

### Step 4 — Validation

**Structural validation:**

```bash
# Count headers by level
grep -c "^# " book.md
grep -c "^## " book.md
grep -c "^### " book.md

# Count lists
grep -c "^- " book.md
grep -c "^[0-9]\. " book.md

# Count tables
grep -c "^|" book.md

# Count images and verify files exist
grep -c "!\[" book.md
grep -o "!\[.*\](.*)" book.md | sed 's/.*(\(.*\))/\1/' | while read img; do
  [ ! -f "$img" ] && echo "Missing image: $img"
done
```

**Quality validation:**
- Open in a Markdown editor — read several sections
- Check readability and visual rendering
- Compare word count with source (should be within ±5%)
- Verify encoding: `file -I book.md` → must show `charset=utf-8`

**Conversion checklist:**

- [ ] All headers converted with correct hierarchy (H1 > H2 > H3)
- [ ] All paragraphs preserved with proper spacing
- [ ] All lists converted (ordered and unordered, nesting preserved)
- [ ] All tables converted with correct structure
- [ ] All images extracted to `images/` folder with working links
- [ ] All hyperlinks converted to `[text](url)` format
- [ ] Blockquotes use `>` syntax
- [ ] Code blocks use triple backticks with language tag
- [ ] Encoding is UTF-8
- [ ] Document reads coherently from start to end

---

## Part 2: Knowledge Extraction

### Step 1 — Map the book structure

- Read the table of contents
- Identify parts, chapters, and key themes
- Create a structure map:

```markdown
# Book Structure: [Title]

## Part 1: [Name]
- Chapter 1: [Theme]
- Chapter 2: [Theme]
```

- Extract key terms, concepts, models
- Note important quotes

### Step 2 — Extract knowledge by category

**Six categories to extract from every chapter:**

**1. Main Ideas** — Key thoughts, conclusions, central concepts
**2. Problems** — What the book solves, describes, or creates during application
**3. Prerequisites** — Author's assumptions, conditions for applicability
**4. Consequences** — Results of applying the methodology, impact on practice
**5. Methodology** — Step-by-step processes, techniques, tools
**6. Insights** — Unexpected discoveries, counterintuitive ideas, breakthroughs

**Template for each extracted item:**

```markdown
## [Category]: [Title]

### Context
- **Chapter/Section:** [location]
- **Page:** [number if available]

### Content
[Description of the idea/problem/methodology]

### Practical application
- **When to use:** [conditions]
- **How to apply:** [steps]
- **Expected result:** [outcome]

### Connections
- **Related to:** [other concepts]
- **Contradicts:** [if applicable]
- **Complements:** [if applicable]

### Quote
"[Direct quote from the book]"
```

**Extraction checklist for each chapter:**

- [ ] 1-3 main ideas identified and recorded
- [ ] Problems (solved and described) recorded with context
- [ ] Explicit and implicit prerequisites identified
- [ ] Consequences (described and potential) recorded
- [ ] Step-by-step processes, methods, tools documented
- [ ] Unexpected/counterintuitive insights captured
- [ ] Cross-chapter connections verified

### Step 3 — Cognitive Quality Framework

Apply three principles to validate extracted knowledge:

**Principle 1: Context and Applicability**
Every extracted idea must define:
- **Target audience:** Novice or Pro?
- **Reader's situation:** Crisis / Growth / Stacking?
- **Consumption goal:** Solve / Learn / Confirm?

**Principle 2: Utility Taxonomy**
Classify each knowledge item's benefit type:
1. **Functional** — Improves a process, saves resources
2. **Social** — Increases status, authority, argumentation power
3. **Psychological** — Reduces anxiety, builds confidence, entertains

**Principle 3: Actionable Syntax**
Knowledge must be formulated so it can be "seen":
- **Visualization test:** Can this concept be drawn as a scene?
- **Grammar:** Subject + Verb + Object. Avoid abstractions ("Optimization") in favor of actions ("Director reduces").
- **Grounding:** Abstract principles must have concrete examples (case studies).

### Step 4 — Structure the output

**Knowledge document template:**

```markdown
# Extracted Knowledge: [Book Title]

## Metadata
- **Author:** [name]
- **Year:** [year]
- **Extraction date:** [date]
- **Source:** [path to .md file]

## Summary
[2-3 paragraphs on the book's central idea]

## Main Ideas
[Items by template]

## Problems
[Items by template]

## Prerequisites
[Items by template]

## Consequences
[Items by template]

## Methodology
[Items by template]

## Insights
[Items by template]

## Practical Application
### When to use this book
[Conditions for applying knowledge]

### How to apply
[Step-by-step process]

### Connections to other sources
[Links to other books/methodologies]

## Quotes
[Important quotes]
```

**Knowledge base structure (for multiple books):**

```
knowledge_base/
├── books/
│   ├── book1/
│   │   ├── book1.md              # Converted book
│   │   ├── book1_knowledge.md    # Extracted knowledge
│   │   └── images/
│   └── book2/
│       ├── book2.md
│       ├── book2_knowledge.md
│       └── images/
├── index.md                      # Index of all books
└── topics/
    ├── methodology.md            # Methodologies across all books
    ├── problems.md               # Problems across all books
    └── insights.md               # Insights across all books
```

---

## Quality metrics

**Conversion quality:**
- Content preserved: ≥ 95%
- Headers correct: 100%
- Lists correct: 100%
- Images extracted: 100%
- Links working: 100%
- Encoding: UTF-8

**Extraction quality:**
- Main ideas: ≥ 5 per book
- Problems: ≥ 3 per book
- Methodologies: ≥ 2 per book
- Insights: ≥ 3 per book
- All items have context, utility type, and visualization test applied

---

## Tools

**Install:**

```bash
brew install libreoffice pandoc antiword tesseract tesseract-lang
```

**Validate:**

```bash
grep -c "^# " book.md          # Headers
grep -c "!\[" book.md           # Images
file -I book.md                 # Encoding
wc -w book.doc book.md          # Word count comparison
```

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Old .doc format not fully supported | Use LibreOffice+Pandoc as universal method |
| Complex formatting lost | Document limitations, manual touch-up if needed |
| Scanned books have no text layer | OCR pipeline with Tesseract |
| Knowledge extraction is subjective | Structured template + checklist + Cognitive Quality framework |
| Incomplete extraction | Verify all 6 categories per chapter |
| Misinterpretation | Use direct quotes, verify context |

---

## Action Plan (improvements backlog)

- [ ] Add .epub and .mobi support
- [ ] Create automated conversion scripts
- [ ] Create automated knowledge extraction with AI
- [ ] Add templates for different book types (business, technical, fiction)
- [ ] Build searchable knowledge base
