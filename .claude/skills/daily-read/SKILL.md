---
name: daily-read
description: Retrieve the scheduled daily bible readings for a given date or today, and retrieve the bible texts.
---

# Daily Read Skill

## Overview
This standalone skill calculates the day of the year (on a 365-day yearly basis) for a specified date or the current date. It maps the day of the year to a daily Bible reading plan and fetches the actual scripture texts using the local bible retrieval system.

## Guidelines & Objectives
When executing this skill:
- Run the python retriever script located at `.claude/skills/daily-read/daily_reader.py` to retrieve the readings and scripture texts.
- Execute the script using: `python3 .claude/skills/daily-read/daily_reader.py "[arguments]"` where `[arguments]` can include a date string, a day number (1-365), and/or bible versions (e.g. `NET`).
- Present the exact output of the script to the user without altering the biblical text, ensuring that the date, the day of the year, and the list of passages are clearly indicated.
