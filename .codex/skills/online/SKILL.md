---
name: online
description: Search, fetch, and integrate latest online information for scholarly theological discussions, bible-related legislation, real-people testimonies, and archaeological discoveries. Use when the user runs /online or requests this BibleMate workflow.
---

# Online Search & Synthesis Skill

## Overview
This standalone skill enables any agent to leverage the web search and fetching capabilities of Codex (`web.run` search, `web.run` open) to retrieve and synthesize real-time scholarly, historical, legal, and personal testimony information that directly enhances Bible study.

## Guidelines & Objectives
When executing this skill:
- **Reputable Sourcing**: Focus on high-quality, reputable Christian and academic resources (e.g., seminary publications, peer-reviewed journals, recognized ministry archives, legal defense databases like Becket or ADF, and archaeological authorities).
- **Zero Hallucination for Quotes**: Retrieve exact quotes from the sources and provide proper URLs or titles.
- ** worldviews Integration**: Present the information through a clear Christian worldview, contrasting it with secular perspectives with grace and truth.
- **Structure**: Group the search findings into relevant categories based on the user's query:
  - Latest Scholarly/Theological Discussions
  - Legal Developments & Legislation
  - Real-People Testimonies & Ministry Reports
  - Historical & Archaeological Discoveries

## Instructions
1. **Search Phase**: Perform focused queries using `web.run` search to locate recent (or historically significant) articles, papers, news, and testimonies relevant to the query.
2. **Fetch Phase**: Read the most relevant search results using `web.run` open to extract details, quotes, and citations.
3. **Synthesis**:
   - Compile the findings into a clear, structured markdown report.
   - List key insights, modern applications, and how these findings enrich our understanding of the related Bible verses or topics.
   - Provide clickable links and citations for all referenced sources.

## Codex Runtime Notes

- Use this `.codex/skills/online/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
