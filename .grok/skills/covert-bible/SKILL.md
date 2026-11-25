---
name: covert-bible
description: Convert Bible source files (USFM, OSIS, TSV, EPUB/HTML, or text) into the BibleMate AI SQLite `.bible` format. Use when the user runs /covert-bible or requests converting a Bible translation into BibleMate format.
---

# Convert Bible to BibleMate SQLite Format

## Overview
This skill guides you through converting user-provided Bible source materials into a `.bible` SQLite database compatible with the BibleMate AI ecosystem and BibleMateWeb.

## SQLite Database Schema

Every converted `.bible` file must use the following SQLite tables:

1. **`Bible`** — Formatted chapter entries (used for rich reading views in BibleMateWeb):
   ```sql
   CREATE TABLE Bible (Book INT, Chapter INT, Scripture TEXT);
   ```
   - One row per chapter (`Book` `1`–`66`, `Chapter` `1`–`N`).

2. **`Verses`** — Plain-text verse entries (used by BibleMate AI retrieval, search, and morphology skills):
   ```sql
   CREATE TABLE Verses (Book INT, Chapter INT, Verse INT, Scripture TEXT);
   ```
   - **Required metadata row `(0, 0, 0)`**: Must contain a brief description/title of the Bible (e.g. `(0, 0, 0, 'The Holy Bible, Berean Study Bible, BSB')`).
   - One row per verse (`Book` `1`–`66`, `Chapter` `>= 1`, `Verse` `>= 1`).
   - `Scripture` must be plain text only (no HTML tags, no `&emsp;`, no section headings, no Psalm superscriptions `\d`, and no footnotes).
   - If a translation omits certain critical-text verses (e.g., Matt 17:21, 18:11, 23:14, Mark 7:16, 9:44, 9:46, 11:26, 15:28, Luke 17:36, 23:17, John 5:4, Acts 8:37, 15:34, 24:7, 28:29, Rom 16:24), insert `(Book, Chapter, Verse, '')` so standard 31,102-verse numbering remains intact.

3. **`Notes`** — Inline Bible footnotes/study notes (create and populate whenever the source contains inline notes):
   ```sql
   CREATE TABLE Notes (Book INT, Chapter INT, Verse INT, ID TEXT, Note TEXT);
   ```
   - Keyed by `(Book, Chapter, Verse, ID)` where `ID` is a bracketed 1-based string per verse (e.g., `"[1]"`, `"[2]"`).

4. **`Details`** — Version metadata:
   ```sql
   CREATE TABLE Details (
       Title NVARCHAR(100),
       Abbreviation NVARCHAR(50),
       Information TEXT,
       Version INT,
       OldTestament BOOL,
       NewTestament BOOL,
       Apocrypha BOOL,
       Strongs BOOL,
       Language NVARCHAR(10)
   );
   ```
   - Insert one row describing the translation (e.g. `('Berean Study Bible', 'BSB', '', 1, 1, 1, 0, 0, 'en')`).

---

## Formatting Requirements

### 1. `Bible.Scripture` (Chapter HTML)
- **Verse wrappers & verse numbers**:
  Wrap each verse in `<verse>...</verse>` (separated by spaces) and mark the verse number with `<vid>`:
  ```html
  <verse><vid id="v{Book}.{Chapter}.{Verse}" onclick="luV({Verse})">{Verse}</vid> ...</verse>
  ```
- **Headings & cross-references** (placed inside `<verse>` right before `<vid>`):
  - Major section (`\ms`): `<u><b>{text}</b></u><br><br>`
  - Major section reference (`\mr`): `<u><b><i>{text}</i></b></u><br><br>`
  - Section heading (`\s1`, `\s2`): `<u><b>{heading}</b></u><br><br>`
  - Section heading followed by cross-references (`\r`):
    ```html
    <u><b>{heading}<br><em><ref onclick="bcv({B},{C},{V})">{Display}</ref>; ...</em></b></u><br><br>
    ```
    (For single-chapter books such as Obadiah, Philemon, 2 John, 3 John, Jude, map to chapter `1`.)
  - Descriptive title / Psalm superscription (`\d`): `<u><b><i>{text}</i></b></u><br><br>` (do not include `\d` text in `Verses.Scripture`).
  - Acrostic headings (`\qa`, e.g., Psalm 119): `<u><b>{text}</b></u><br><br>`.
- **Paragraphs, poetry, and lists**:
  - Paragraph breaks (`\p`, `\m`, `\pmo`, `\pc`): `<br><br>`.
  - Indented / poetic / list lines (`\pmo`, `\q1`, `\q2`, `\li1`, `\li2`, `\qr`, `\pc`): prefix with `<br>&emsp;&emsp;` (or `&emsp;&emsp;` immediately after a heading's `<br><br>`).
  - Stanza break (`\b`): `<br>`.
- **Words of Jesus** (`\wj ... \wj*`):
  - Wrap in `<woj>...</woj>`. Keep `<woj>` balanced within each `<verse>...</verse>` block (close `</woj>` before `</verse>` and reopen `<woj>` in the next verse if a speech spans multiple verses), and keep leading spaces outside `<woj>`.

### 2. Inline Notes (`Bible.Scripture` + `Notes` Table)
For BibleMateWeb footnote popups to work properly:
- **Quoted string ID is required**: The 4th argument of `bn(...)` **must be a quoted string** (e.g. `"[1]"`), **never** an unquoted integer like `0`.
- **In `Bible.Scripture`**, replace each inline note at its exact position with:
  ```html
  <sup><ref onclick='bn({Book}, {Chapter}, {Verse}, "[{N}]")'>&oplus;</ref></sup>
  ```
  where `N` is `1, 2, ...` per verse (matching `ID = "[1]"`, `"[2]"`, ... in `Notes`).
- **In `Notes.Note`**, format the note body cleanly with HTML:
  - Verse reference prefix (e.g. `\fr C:V `): `{Verse} `
  - Quoted alternate/original terms (`\fqa ...`): `<em>...</em>`
  - Verse numbers inside notes (`\fv N\fv*`): `<b>N</b> `
  - Scripture cross-references (`\ref Display|Target\ref*`): `<ref onclick="bcv(B,C,V)">Display</ref>` (or plain `Display` for non-canonical books).
  - Normalize extra whitespace before punctuation (`;`, `,`, `.`).
- **In `Verses.Scripture`**, strip all footnotes completely.

---

## Conversion Workflow

1. **Think First — Evaluate and Choose the Best Source(s)**:
   Users may provide multiple kinds or formats of Bible sources (e.g., USFM, OSIS XML, JSON, EPUB/HTML, TSV/CSV, or plain text). Before writing any converter:
   - **Inspect all available sources** to see what each format preserves (paragraphs, poetry indentation, section headings, cross-references, Words of Jesus, inline footnotes, and up-to-date text).
   - **Rank and choose the best source(s)** for the cleanest, richest result:
     1. **USFM / OSIS XML** (generally best): Explicitly encodes structure (`\p`, `\q1`/`\q2`, `\s1`, `\r`, `\d`, `\wj`, `\f`).
     2. **Structured JSON / EPUB / XHTML**: Good if USFM/OSIS is unavailable, though HTML/CSS classes require careful mapping.
     3. **TSV / CSV / Plain Text**: Use only when richer formats are unavailable, or as a supplementary source (e.g., if headings, footnotes, or verse boundaries are missing from another file).
   - If no single file has everything, combine the strongest primary text source with supplementary metadata/notes sources rather than settling for degraded formatting.
2. **Map Book Numbers**:
   - Map all 66 canonical books to `1`–`66` (Genesis = `1` through Revelation = `66`).
3. **Write and Run a Conversion Script**:
   - Parse chapters, verses, headings, paragraphs/poetry, Words of Jesus, and inline footnotes into `Bible`, `Verses`, `Notes`, and `Details`.
   - Ensure `(0, 0, 0)` is inserted into `Verses` with a brief description of the Bible.
   - **Output file naming & location**: Save the produced `.bible` file in `biblemate_bibles/<ABBR>.bible` (creating `biblemate_bibles/` if it does not exist). Use the abbreviation specified by the user (e.g., `BSB` -> `biblemate_bibles/BSB.bible`); if the user does not specify one, derive an appropriate abbreviation from the provided source materials (e.g., metadata, title, headers, or filenames).
4. **Verify the Generated `.bible` Database**:
   - Confirm `Bible` has all expected chapters (`1189` for full Protestant canon) and `Verses` has all expected verses plus `(0, 0, 0)`.
   - Confirm zero duplicate `(Book, Chapter, Verse)` rows in `Verses`.
   - Confirm zero leftover source markup (e.g., no stray `\...` USFM markers) in `Bible`, `Verses`, and `Notes`.
   - Confirm all HTML tags (`verse`, `u`, `b`, `em`, `i`, `woj`, `sup`, `vid`, `ref`) are balanced.
   - If `Notes` is present, verify every `bn(Book, Chapter, Verse, "[N]")` call in `Bible.Scripture` matches a `(Book, Chapter, Verse, ID)` row in `Notes` 1:1.

## Grok Build Runtime

Use this `.grok/skills/covert-bible/` copy. Do not run sibling copies under
`.agents/`, `.claude/`, `.codex/`, or `.cursor/`.

- Run the commands in this skill with `run_terminal_command` from the repository root.
- Inspect sources and outputs with `read_file`, `grep`, and `list_dir`.
- Create or revise the converter with `write` and `search_replace`.
- Do not save a `biblemate/` study file. Confirm the output path and the verification counts.
