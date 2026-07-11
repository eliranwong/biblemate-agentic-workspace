---
name: testimony
description: Retrieve verified real-life and missionary testimonies from local database or online research, including background details and fact-checking sources.
---

# Testimony Retrieval & Generation Skill

## Overview
This standalone skill enables any agent to find, verify, and write real-life or missionary-historical testimonies that address the user's specific input, struggle, or sermon topic. All testimonies must be completely real and verified.

## Guidelines & Objectives
When executing this skill:
- **Absolute Integrity**: The testimony must be completely real. Never fabricate or embellish details.
- **Background & Context**: Provide historical context, biographical details of the key persons, and locations.
- **Verification & Sources**: List books, articles, or reputable website URLs along with brief notes on how a user can fact-check the testimony.
- **Scripture Integrity**: Retrieve all related scriptures using the local `bible` skill (e.g. `python3 .agents/skills/bible/bible_retriever.py "<query>"`). Never quote scripture from memory.
- **Save Study Output**: Save the complete final testimony document to the `biblemate/` directory with the timestamp prefix in the format `YYYY-MM-DD-HH-MM-SS_testimony_<slug>.md` and confirm the path.

## Instructions
1. **Search Local Registry**:
   Run the local python retriever script first to see if a matching historical/missionary testimony is available in the local database:
   ```bash
   python3 .agents/skills/testimony/testimony_retriever.py "<query>"
   ```
2. **Perform Online Search (if needed)**:
   If no direct match is found in the local registry, or if a specific modern scenario is queried:
   - Use the `search_web` tool to search for real-life testimonies, modern missionary reports, or news articles.
   - Use the `read_url_content` tool to fetch pages and verify the details.
   - Compile the narrative, biographical background, and fact-checking sources.
3. **Retrieve and Quote Bible Passages**:
   Identify the theological themes or verses connected to the testimony, and retrieve the exact text of those verses using the local `bible` skill.
4. **Draft and Integrate**:
   - Write a compelling narrative fit for encouragement or preaching.
   - Structure the output clearly: Title, Biographical Info, Narrative Story, Scripture Connection, and Verification/Sources.
5. **Save the Output**:
   - If not saved automatically by the script, save the compiled testimony document to the `biblemate/` directory as `biblemate/YYYY-MM-DD-HH-MM-SS_testimony_<slug>.md`.
   - Confirm the saved file path.
