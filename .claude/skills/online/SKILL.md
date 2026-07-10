---
name: online
description: Search, fetch, and integrate latest online information for scholarly theological discussions, bible-related legislation, real-people testimonies, and archaeological discoveries.
---

# Online Search & Synthesis Skill

## Overview
This standalone skill enables any agent to leverage the web search and fetching capabilities of the Antigravity platform (`search_web`, `read_url_content`) to retrieve and synthesize real-time scholarly, historical, legal, and personal testimony information that directly enhances Bible study.

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
1. **Search Phase**: Perform focused queries using `search_web` to locate recent (or historically significant) articles, papers, news, and testimonies relevant to the query.
2. **Fetch Phase**: Read the most relevant search results using `read_url_content` to extract details, quotes, and citations.
3. **Synthesis**:
   - Compile the findings into a clear, structured markdown report.
   - List key insights, modern applications, and how these findings enrich our understanding of the related Bible verses or topics.
   - Provide clickable links and citations for all referenced sources.
