# Slash Commands & Workflows Reference Guide

This guide details all 113 custom slash commands (workflows) available in the **Antigravity Bible Study Agents** ecosystem, categorized by their study focus.

---

## 1. Exegesis & Translation Commands

These commands focus on original languages, structural analysis, and the logical argument of the text.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/translate-greek`** | Translates a Greek verse, gives transliteration and word-by-word mapping. | Biblical Translator | A Koine Greek verse | `/translate-greek John 1:1` |
| **`/translate-hebrew`** | Translates a Hebrew verse, gives transliteration and word-by-word mapping. | Biblical Translator | A biblical Hebrew verse | `/translate-hebrew Genesis 1:1` |
| **`/keywords`** | Extracts key words and studies original Greek/Hebrew meanings. | Oxford Bible Scholar | A bible passage or chapter | `/keywords Romans 3:21-26` |
| **`/insights`** | Provides exegetical, literary, and spiritual insights on a passage. | Oxford Bible Scholar | A bible passage | `/insights Galatians 2:20` |
| **`/flow`** | Traces the author's logical argument and thought progression. | Oxford Bible Scholar | A bible passage or chapter | `/flow Hebrews 1` |
| **`/outline`** | Generates a highly detailed structural outline of a passage or book. | Oxford Bible Scholar | A bible book or passage | `/outline Colossians` |
| **`/morphology`** | Retrieves word-by-word grammar and morphology data, with optional keyword or phrase filtering. | Verse Scripter | A bible reference(s) with optional keyword filtering | `/morphology love the world in John 3:16` |
| **`/original`** | Retrieves the original Greek or Hebrew text of a Bible verse using the local OHGB database. | Verse Scripter | A bible reference(s) | `/original John 1:1` |
| **`/interlinear`** | Retrieves the interlinear Greek/Hebrew text of a Bible verse using the local OHGBi database. | Verse Scripter | A bible reference(s) | `/interlinear John 1:1` |

---

## 2. Context & Historical Background Commands

These commands locate the scripture within its historical-cultural setting and its place in the biblical storyline.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/introduce-book`** | Generates a comprehensive scholarly introduction to a bible book. | Oxford Bible Scholar | A bible book | `/introduce-book Philippians` |
| **`/chapter-summary`** | Generates a detailed chapter interpretation, structure, and exegesis. | Oxford Bible Scholar | A bible chapter | `/chapter-summary John 3` |
| **`/canon`** | Explains how a text connects to the grand storyline and covenants of Scripture. | Oxford Bible Scholar | A book, chapter, or passage | `/canon Genesis 12:1-3` |
| **`/ot-context`** | Provides historical-cultural context for an Old Testament passage. | Oxford Bible Scholar | An OT passage | `/ot-context Exodus 3` |
| **`/nt-context`** | Provides historical-cultural context for a New Testament passage. | Oxford Bible Scholar | A NT passage | `/nt-context Acts 2` |
| **`/ot-highlights`** | Outlines major historical events, covenants, and highlights in an OT text. | Oxford Bible Scholar | An OT passage | `/ot-highlights Genesis 15` |
| **`/nt-highlights`** | Outlines major historical events, covenants, and highlights in a NT text. | Oxford Bible Scholar | A NT passage | `/nt-highlights Matthew 2` |
| **`/ot-highligths`** | *Compatibility duplicate of `/ot-highlights`.* | Oxford Bible Scholar | An OT passage | `/ot-highligths Genesis 15` |

---

## 3. Theology & Doctrinal Commands

These commands synthesize the systematic doctrines, theological messages, and worldview connections.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/meaning`** | Analyzes the core theological meaning and authorial intent. | Cambridge Theologian | A bible passage | `/meaning Romans 5:1-11` |
| **`/ot-meaning`** | Analyzes the meaning of an OT passage in its covenant context. | Cambridge Theologian | An OT passage | `/ot-meaning Psalm 23` |
| **`/nt-meaning`** | Analyzes the meaning of a NT passage in its covenant context. | Cambridge Theologian | A NT passage | `/nt-meaning Ephesians 1:3-14` |
| **`/theology`** | Summarizes the systematic doctrines and redemptive message of a text. | Cambridge Theologian | A bible passage | `/theology Galatians 3` |
| **`/themes`** | Conducts a systematic thematic study of a passage. | Cambridge Theologian | A bible passage | `/themes Romans 8` |
| **`/ot-themes`** | Conducts a systematic thematic study of an OT passage. | Cambridge Theologian | An OT passage | `/ot-themes Isaiah 53` |
| **`/nt-themes`** | Conducts a systematic thematic study of a NT passage. | Cambridge Theologian | A NT passage | `/nt-themes 1 John 4` |
| **`/topic`** | Performs an in-depth topical study from Genesis to Revelation. | Cambridge Theologian | A biblical topic or word | `/topic Justification` |
| **`/perspective`** | Evaluates a secular article, quote, or idea from a biblical worldview. | Biblical Content Interpreter | A contemporary quote or text | `/perspective "The meaning of life is what you make it"` |
| **`/summary`** | Summarizes text in reference to biblical principles. | Cambridge Theologian | Any text or passage | `/summary [Paste text]` |
| **`/online`** | Searches, fetches, and integrates real-time online data (scholarly articles, legislation, testimonies, archaeology) for biblical study. | Biblical Content Interpreter | A research topic or query | `/online "religious freedom legislation affecting churches 2026"` |

---

## 4. Devotional, Application, & Ministry Commands

These commands focus on practical living, personal prayer, and preparing to teach or preach scripture.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/sermon`** | Generates a detailed homiletical sermon outline and content. | Compassionate Pastor | A bible passage | `/sermon 1 Peter 1:3-9` |
| **`/devotion`** | Generates a deep, gospel-centered devotional reflection and prayer. | Compassionate Pastor | A bible passage | `/devotion Psalm 103` |
| **`/application`** | Outlines practical, personal, and heart applications of a text. | Compassionate Pastor | A bible passage | `/application James 1:19-27` |
| **`/questions`** | Generates observation, interpretation, and application study questions. | Compassionate Pastor | A bible passage | `/questions Luke 15:11-32` |
| **`/prayer`** | Writes a rich scriptural prayer in the first person based on the text. | Compassionate Pastor | A bible passage | `/prayer Philippians 4:4-7` |
| **`/short-prayer`** | Writes a brief, direct scriptural prayer (single paragraph) based on the text. | Compassionate Pastor | A bible passage | `/short-prayer Psalm 19` |
| **`/promises`** | Quotes and explains biblical promises related to a topic. | Verse Scripter | A biblical topic | `/promises Anxiety` |
| **`/quotes`** | Finds and quotes multiple relevant cross-references. | Verse Scripter | A biblical topic or query | `/quotes Covenant` |
| **`/bible`** | Retrieves and compares Bible verses line-by-line from local databases. | Verse Scripter | A bible version(s) and reference(s) | `/bible NET CUV John 3:16-18` |
| **`/commentary`** | Retrieves and compares Bible commentaries from local databases, extracting verse-specific sections. | Verse Scripter | A commentary version(s) and reference(s) | `/commentary AIC BI John 3:16-18` |
| **`/xrefs`** | Retrieves and compares Bible cross-references from the local cross-reference database. | Verse Scripter | A bible version(s) and reference(s) | `/xrefs NET CUV John 3:16-18` |
| **`/search`** | Searches for words or phrases with wildcards and logical operators. | Verse Scripter | Search query with optional versions | `/search NET KJV love*God` |
| **`/<Book>`** | Searches for words or phrases within a specific Bible book (66 book-specific commands, e.g., `/Gen`, `/Matt`, `/Rev`). | Verse Scripter | Search query with optional versions | `/Matt NET KJV love*God` |
| **`/lexicon`** | Retrieves and compares definitions for Strong's numbers or original language keys. | Verse Scripter | Strong's number(s) with optional versions | `/lexicon BDB SECE H148` |

### Book-Specific Search Commands

To search for words or phrases within a single book, you can use the following 66 book-specific slash commands:

*   **Old Testament:** `/Gen`, `/Exod`, `/Lev`, `/Num`, `/Deut`, `/Josh`, `/Judg`, `/Ruth`, `/1Sam`, `/2Sam`, `/1Kgs`, `/2Kgs`, `/1Chr`, `/2Chr`, `/Ezra`, `/Neh`, `/Esth`, `/Job`, `/Ps`, `/Prov`, `/Eccl`, `/Song`, `/Isa`, `/Jer`, `/Lam`, `/Ezek`, `/Dan`, `/Hos`, `/Joel`, `/Amos`, `/Obad`, `/Jonah`, `/Mic`, `/Nah`, `/Hab`, `/Zeph`, `/Hag`, `/Zech`, `/Mal`
*   **New Testament:** `/Matt`, `/Mark`, `/Luke`, `/John`, `/Acts`, `/Rom`, `/1Cor`, `/2Cor`, `/Gal`, `/Eph`, `/Phil`, `/Col`, `/1Thess`, `/2Thess`, `/1Tim`, `/2Tim`, `/Titus`, `/Phlm`, `/Heb`, `/Jas`, `/1Pet`, `/2Pet`, `/1John`, `/2John`, `/3John`, `/Jude`, `/Rev`

---

## 5. Workspace & Repository Commands

These commands help manage the workspace files and synchronize changes with remote repositories.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/data`** | Lists all available versions of Bibles, commentaries, or lexicons by dynamically scanning storage folders. | Verse Scripter | Resource type (`bible`, `commentary`, or `lexicon`) | `/data bible` |
| **`/sync`** | Stages, commits, and pushes all latest workspace changes to the remote repository. | Verse Scripter | Optional custom commit message | `/sync "Added sync command"` |
| **`/md`** | Converts a file to markdown, or exports the last response/conversation to export/md. | Verse Scripter | Optional file path or export keyword (e.g., 'whole', 'conversation') | `/md export/docx/README.md` or `/md whole` |
| **`/docx`** | Converts a file to Word docx format, or exports the last response/conversation to export/docx. | Verse Scripter | Optional file path or export keyword (e.g., 'whole', 'conversation') | `/docx README.md` or `/docx whole` |
| **`/zip`** | Creates a `manual_setup.zip` file in the root directory containing `.agents/` and `preferences/` folders for manual setup. | Verse Scripter | None | `/zip` |


