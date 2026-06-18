# Slash Commands & Workflows Reference Guide

This guide details all 37 custom slash commands (workflows) available in the **Antigravity Bible Study Agents** ecosystem, categorized by their study focus.

---

## 1. Exegesis & Translation Commands

These commands focus on original languages, structural analysis, and the logical argument of the text.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/translate_greek`** | Translates a Greek verse, gives transliteration and word-by-word mapping. | Biblical Translator | A Koine Greek verse | `/translate_greek John 1:1` |
| **`/translate_hebrew`** | Translates a Hebrew verse, gives transliteration and word-by-word mapping. | Biblical Translator | A biblical Hebrew verse | `/translate_hebrew Genesis 1:1` |
| **`/keywords`** | Extracts key words and studies original Greek/Hebrew meanings. | Oxford Bible Scholar | A bible passage or chapter | `/keywords Romans 3:21-26` |
| **`/insights`** | Provides exegetical, literary, and spiritual insights on a passage. | Oxford Bible Scholar | A bible passage | `/insights Galatians 2:20` |
| **`/flow`** | Traces the author's logical argument and thought progression. | Oxford Bible Scholar | A bible passage or chapter | `/flow Hebrews 1` |
| **`/outline`** | Generates a highly detailed structural outline of a passage or book. | Oxford Bible Scholar | A bible book or passage | `/outline Colossians` |

---

## 2. Context & Historical Background Commands

These commands locate the scripture within its historical-cultural setting and its place in the biblical storyline.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/introduce_book`** | Generates a comprehensive scholarly introduction to a bible book. | Oxford Bible Scholar | A bible book | `/introduce_book Philippians` |
| **`/chapter_summary`** | Generates a detailed chapter interpretation, structure, and exegesis. | Oxford Bible Scholar | A bible chapter | `/chapter_summary John 3` |
| **`/canon`** | Explains how a text connects to the grand storyline and covenants of Scripture. | Oxford Bible Scholar | A book, chapter, or passage | `/canon Genesis 12:1-3` |
| **`/ot_context`** | Provides historical-cultural context for an Old Testament passage. | Oxford Bible Scholar | An OT passage | `/ot_context Exodus 3` |
| **`/nt_context`** | Provides historical-cultural context for a New Testament passage. | Oxford Bible Scholar | A NT passage | `/nt_context Acts 2` |
| **`/ot_highlights`** | Outlines major historical events, covenants, and highlights in an OT text. | Oxford Bible Scholar | An OT passage | `/ot_highlights Genesis 15` |
| **`/nt_highlights`** | Outlines major historical events, covenants, and highlights in a NT text. | Oxford Bible Scholar | A NT passage | `/nt_highlights Matthew 2` |
| **`/ot_highligths`** | *Compatibility duplicate of `/ot_highlights`.* | Oxford Bible Scholar | An OT passage | `/ot_highligths Genesis 15` |

---

## 3. Theology & Doctrinal Commands

These commands synthesize the systematic doctrines, theological messages, and worldview connections.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/meaning`** | Analyzes the core theological meaning and authorial intent. | Cambridge Theologian | A bible passage | `/meaning Romans 5:1-11` |
| **`/ot_meaning`** | Analyzes the meaning of an OT passage in its covenant context. | Cambridge Theologian | An OT passage | `/ot_meaning Psalm 23` |
| **`/nt_meaning`** | Analyzes the meaning of a NT passage in its covenant context. | Cambridge Theologian | A NT passage | `/nt_meaning Ephesians 1:3-14` |
| **`/theology`** | Summarizes the systematic doctrines and redemptive message of a text. | Cambridge Theologian | A bible passage | `/theology Galatians 3` |
| **`/themes`** | Conducts a systematic thematic study of a passage. | Cambridge Theologian | A bible passage | `/themes Romans 8` |
| **`/ot_themes`** | Conducts a systematic thematic study of an OT passage. | Cambridge Theologian | An OT passage | `/ot_themes Isaiah 53` |
| **`/nt_themes`** | Conducts a systematic thematic study of a NT passage. | Cambridge Theologian | A NT passage | `/nt_themes 1 John 4` |
| **`/topic`** | Performs an in-depth topical study from Genesis to Revelation. | Cambridge Theologian | A biblical topic or word | `/topic Justification` |
| **`/perspective`** | Evaluates a secular article, quote, or idea from a biblical worldview. | Biblical Content Interpreter | A contemporary quote or text | `/perspective "The meaning of life is what you make it"` |
| **`/summary`** | Summarizes text in reference to biblical principles. | Cambridge Theologian | Any text or passage | `/summary [Paste text]` |

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
| **`/short_prayer`** | Writes a brief, direct scriptural prayer (single paragraph) based on the text. | Compassionate Pastor | A bible passage | `/short_prayer Psalm 19` |
| **`/promises`** | Quotes and explains biblical promises related to a topic. | Verse Scripter | A biblical topic | `/promises Anxiety` |
| **`/quotes`** | Finds and quotes multiple relevant cross-references. | Verse Scripter | A biblical topic or query | `/quotes Covenant` |
| **`/bible`** | Retrieves and compares Bible verses line-by-line from local databases. | Verse Scripter | A bible version(s) and reference(s) | `/bible NET CUV John 3:16-18` |

---

## 5. Workspace & Repository Commands

These commands help manage the workspace files and synchronize changes with remote repositories.

| Command | Description | Assigned Persona | Expected Input | Example |
| :--- | :--- | :--- | :--- | :--- |
| **`/sync`** | Stages, commits, and pushes all latest workspace changes to the remote repository. | Verse Scripter | Optional custom commit message | `/sync "Added sync command"` |
| **`/md`** | Converts a file to markdown, or exports the last response/conversation to export/md. | Verse Scripter | Optional file path or export keyword (e.g., 'whole', 'conversation') | `/md export/docx/README.md` or `/md whole` |
| **`/docx`** | Converts a file to Word docx format, or exports the last response/conversation to export/docx. | Verse Scripter | Optional file path or export keyword (e.g., 'whole', 'conversation') | `/docx README.md` or `/docx whole` |


