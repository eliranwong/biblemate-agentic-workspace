---
description: Get a detailed summary and interpretation of a bible chapter.
---

Adopt the **OT Bible Scholar** (for Old Testament chapters) or **NT Bible Scholar** (for New Testament chapters) persona from `.claude/agents.md`.

Use the **chapter-summary** skill to retrieve baseline chapter summary data.

Always execute:
`python3 .claude/skills/chapter-summary/chapter_summary_retriever.py "$1 $2 $3 $4 $5"`
(and add any language options like `--sc` or `--tc` if the input is in Chinese or requested).

Use the retrieved database output as the baseline information. Combine it with your assigned scholar persona and relevant scripture references to write a detailed, comprehensive, and informative interpretation on the bible chapter, addressing all of the following questions:
1. What is the overview of the chapter? (Expand on the overview retrieved from the database)
2. How are the verses in this chapter structured or organized? (Elaborate on the structural outline retrieved from the database)
3. Are there any key verses or passages in the chapter? (Cite and explain them)
4. Are there any significant characters, events, or symbols in the chapter?
5. What is the main themes or messages of the chapter? (Deepen the themes retrieved from the database)
6. What historical or cultural context is important to understand the chapter?
7. How have theologians, scholars, or religious leaders interpreted this chapter?
8. Are there any popular interpretations or controversies related to this chapter?
9. How does this chapter relate to other chapters, books, or themes in the Bible?
10. What lessons or morals can be taken from the chapter?

When you explain, quote specific words or phrases from relevant bible verses. All quoted verse content must be verified and retrieved using the local `bible` skill rather than from memory.

# Bible chapter

$ARGUMENTS

