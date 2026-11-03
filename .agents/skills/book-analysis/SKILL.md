---
name: book-analysis
description: Produce a comprehensive introduction, historical background, and overview of a bible book. Use when the user runs /book-analysis or requests this BibleMate workflow.
---

# Book Analysis Skill

## Persona
Adopt the **OT Bible Scholar** (for Old Testament books) or **NT Bible Scholar** (for New Testament books) persona from `.agents/agents.md`.

## Overview
This standalone skill enables any agent to perform a high-quality introduce book study for a given Bible reference, text, or topic.

## Guidelines & Objectives
When executing this skill:
- Always run the python script located at `.agents/skills/book-analysis/book_analysis_retriever.py` to search the local database for baseline book introductions.
- Execute the script using: `python3 .agents/skills/book-analysis/book_analysis_retriever.py "<Book>"` (you can also pass language options like `--sc` or `--tc` if a Chinese translation is preferred, or the script will auto-detect Chinese characters).
- Retrieve and use the local database output as the baseline information. Combine it with your assigned persona, theological perspective, and relevant Scripture references to fully expound the book in detail.
- Keep explanations biblically accurate and structurally clear.
- Cite specific book, chapter, and verse references for all statements.
- Ensure that the output is comprehensive, addressing all prompt criteria without skipping sections.
- Focus strictly on the requirements of this specific study type.

## Instructions
Produce a comprehensive scholarly introduction and overview of a bible book. Integrate and fully expound the retrieved baseline data (Overview, Structural Outline, Logical Flow, Historical Setting, Themes, Keywords, Theology, Canonical Placement, Practical Living, Summary) to address:
1. **Historical Background**: Authorship, date, provenance, and target audience. Expand upon the retrieved Historical Setting and Overview.
2. **Literary Context**: Genre, structure, and style. Elaborate on the Structural Outline and Logical Flow retrieved from the database.
3. **Occasion and Purpose**: Why the book was written and the issues it addresses.
4. **Theological Themes**: Core doctrines, covenantal focus, and major teachings. Deepen the Themes, Keywords, and Theology retrieved from the database.
5. **Christological Focus**: How the book reveals Jesus Christ and the Gospel.
6. **Canonical Placement & Practical Application**: Setting the book's location in the grand storyline of scripture and outline practical applications for modern living. Incorporate the Canonical Placement and Practical Living sections retrieved from the database.

## Guiding Questions
Ensure the introduction comprehensively answers all of the following questions, quoting specific words or phrases from relevant Bible verses (retrieved via the `bible` skill):
1. Who is the author or attributed author of the book?
2. What is the date or time period when the book was written?
3. What is the main theme or purpose of the book?
4. What are the significant historical events or context surrounding the book?
5. Are there any key characters or figures in the book?
6. What are some well-known or significant passages from the book?
7. How does the book fit into the overall structure and narrative of the Bible?
8. What lessons or messages can be learned from the book?
9. What is the literary form or genre of the book (e.g., historical, prophetic, poetic, epistle, etc.)?
10. Are there any unique features or controversies surrounding the book?
