---
description: Generate a comprehensive introduction to a book of the Bible.
---

Adopt the **OT Bible Scholar** (for Old Testament books) or **NT Bible Scholar** (for New Testament books) persona from `.agents/agents.md`.

First, run the database retriever script to search the local database for baseline book introduction data:
`python3 .agents/skills/book-analysis/book_analysis_retriever.py "$1"` (use language flags like `--sc` or `--tc` if query is in Chinese).

Then, write a detailed introduction on the book in the bible, integrating and fully expounding the retrieved baseline database contents (Overview, Structural Outline, Logical Flow, Historical Setting, Themes, Keywords, Theology, Canonical Placement, Practical Living, Summary) while considering all the following questions:
1. Who is the author or attributed author of the book?
2. What is the date or time period when the book was written?
3. What is the main theme or purpose of the book?
4. What are the significant historical events or context surrounding the book?
5. Are there any key characters or figures in the book?
6. What are some well-known or significant passages from the book?
7. How does the book fit into the overall structure and narrative of the Bible?
8. What lessons or messages can be learned from the book?
9. What is the literary form or genre of the book (e.g. historical, prophetic, poetic, epistle, etc.)?
10. Are there any unique features or controversies surrounding the book?
I want the introduction to be comprehensive and informative, fully expounding the retrieved details.
When you explain, quote specific words or phrases from relevant bible verses, if any.
Answer all these relevant questions mentioned above, in the introduction, pertaining to the following bible book.

# Bible book name

$1 $2 $3 $4 $5
