#!/usr/bin/env python3
"""
export_bible.py — Export a .bible SQLite `Bible` table into Markdown files.

Output layout:
  <ABBR>/
    00-Intro/   (if Book = 0 exists)
      000.md / 001.md ...
    01-Gen/
      001.md
      002.md
      ...
    66-Rev/
      001.md
      ...
"""

import argparse
import glob
import html
import os
import re
import sqlite3
import sys

BOOK_ABBR = {
    0: "Intro",
    1: "Gen", 2: "Exod", 3: "Lev", 4: "Num", 5: "Deut",
    6: "Josh", 7: "Judg", 8: "Ruth", 9: "1Sam", 10: "2Sam",
    11: "1Kgs", 12: "2Kgs", 13: "1Chr", 14: "2Chr", 15: "Ezra",
    16: "Neh", 17: "Esth", 18: "Job", 19: "Ps", 20: "Prov",
    21: "Eccl", 22: "Song", 23: "Isa", 24: "Jer", 25: "Lam",
    26: "Ezek", 27: "Dan", 28: "Hos", 29: "Joel", 30: "Amos",
    31: "Obad", 32: "Jonah", 33: "Mic", 34: "Nah", 35: "Hab",
    36: "Zeph", 37: "Hag", 38: "Zech", 39: "Mal",
    40: "Matt", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts",
    45: "Rom", 46: "1Cor", 47: "2Cor", 48: "Gal", 49: "Eph",
    50: "Phil", 51: "Col", 52: "1Thess", 53: "2Thess", 54: "1Tim",
    55: "2Tim", 56: "Titus", 57: "Phlm", 58: "Heb", 59: "Jas",
    60: "1Pet", 61: "2Pet", 62: "1John", 63: "2John", 64: "3John",
    65: "Jude", 66: "Rev",
}

BOOK_NAMES = {
    0: "Introduction",
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
    6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
    11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles", 15: "Ezra",
    16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms", 20: "Proverbs",
    21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah", 24: "Jeremiah", 25: "Lamentations",
    26: "Ezekiel", 27: "Daniel", 28: "Hosea", 29: "Joel", 30: "Amos",
    31: "Obadiah", 32: "Jonah", 33: "Micah", 34: "Nahum", 35: "Habakkuk",
    36: "Zephaniah", 37: "Haggai", 38: "Zechariah", 39: "Malachi",
    40: "Matthew", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts",
    45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians", 48: "Galatians", 49: "Ephesians",
    50: "Philippians", 51: "Colossians", 52: "1 Thessalonians", 53: "2 Thessalonians", 54: "1 Timothy",
    55: "2 Timothy", 56: "Titus", 57: "Philemon", 58: "Hebrews", 59: "James",
    60: "1 Peter", 61: "2 Peter", 62: "1 John", 63: "2 John", 64: "3 John",
    65: "Jude", 66: "Revelation",
}


def discover_bibles():
    """Return list of (abbr, title, path) from standard BibleMate directories."""
    home = os.path.expanduser("~")
    search_dirs = [
        os.path.join(home, "biblemate", "data_custom", "bibles"),
        os.path.join(home, "biblemate", "data", "bibles"),
        os.path.abspath("biblemate_tagged_bibles"),
        os.path.abspath("biblemate_bibles"),
    ]
    seen_abbr = {}
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fp in sorted(glob.glob(os.path.join(d, "*.bible"))):
            stem = os.path.splitext(os.path.basename(fp))[0]
            if stem.lower() in seen_abbr:
                continue
            title = ""
            det_abbr = ""
            try:
                conn = sqlite3.connect(f"file:{fp}?mode=ro", uri=True)
                has_det = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Details'"
                ).fetchone()
                if has_det:
                    row = conn.execute("SELECT Title, Abbreviation FROM Details LIMIT 1").fetchone()
                    if row:
                        title = (row[0] or "").strip()
                        det_abbr = (row[1] or "").strip()
                conn.close()
            except Exception:
                pass
            seen_abbr[stem.lower()] = (stem, det_abbr, title, fp)
    return list(seen_abbr.values())


def resolve_bible(query: str):
    """Resolve a version name, abbreviation, or .bible path to (abbr, path)."""
    if os.path.isfile(query):
        return os.path.splitext(os.path.basename(query))[0], query

    q = query.strip().lower()
    entries = discover_bibles()

    # 1. Exact filename stem match
    for stem, _, _, fp in entries:
        if stem.lower() == q:
            return stem, fp

    # 2. Exact Details.Abbreviation match (skip generic 'BIBLE')
    for stem, det_abbr, _, fp in entries:
        if det_abbr and det_abbr.lower() != "bible" and det_abbr.lower() == q:
            return stem, fp

    # 3. Exact or substring Details.Title match
    for stem, _, title, fp in entries:
        if title and title.lower() == q:
            return stem, fp
    for stem, _, title, fp in entries:
        if title and q in title.lower():
            return stem, fp

    # 4. Partial stem match
    for stem, _, _, fp in entries:
        if q in stem.lower():
            return stem, fp

    return None, None


def html_to_markdown(raw_html: str) -> str:
    """Convert BibleMate `Bible.Scripture` HTML into clean Markdown."""
    if not raw_html:
        return ""
    text = raw_html
    # Normalize line breaks
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    # Strip word-level tags while keeping inner text
    text = re.sub(r"</?(?:en|zh|w)(?:\s+[^>]*)?>", "", text, flags=re.I)
    # Convert verse numbers
    text = re.sub(r"<vid\b[^>]*>(.*?)</vid>", r"**\1** ", text, flags=re.S | re.I)
    # Convert headings / bold / italic
    text = re.sub(r"<u>\s*<b>(.*?)</b>\s*</u>", lambda m: f"### {m.group(1).strip()}", text, flags=re.S | re.I)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.S | re.I)
    text = re.sub(r"<(?:i|em)>(.*?)</(?:i|em)>", r"*\1*", text, flags=re.S | re.I)
    # Convert inline notes / refs
    text = re.sub(r"<mbn>(.*?)</mbn>", r" *[\1]* ", text, flags=re.S | re.I)
    text = re.sub(r"<ref\b[^>]*>(.*?)</ref>", r"\1", text, flags=re.S | re.I)
    # Verse boundaries -> blank line / newline
    text = re.sub(r"<verse>", "", text, flags=re.I)
    text = re.sub(r"</verse>", "\n\n", text, flags=re.I)
    # Strip any remaining HTML/XML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities (&emsp;, &nbsp;, &amp;, etc.)
    text = html.unescape(text).replace("\u2003", "  ").replace("\xa0", " ")
    # Clean trailing spaces per line and excessive blank lines
    lines = [ln.rstrip() for ln in text.splitlines()]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"^\s+(#{1,6}\s)", r"\1", cleaned, flags=re.M)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def default_out_dir() -> str:
    """Resolve `<repo_root>/bibles` portably relative to this script."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    return os.path.join(repo_root, "bibles")


def export_bible(version_query: str, out_dir: str = ""):
    if not out_dir:
        out_dir = default_out_dir()
    abbr, db_path = resolve_bible(version_query)
    if not db_path:
        available = ", ".join(stem for stem, _, _, _ in discover_bibles())
        print(f"Error: Could not find Bible matching '{version_query}'.", file=sys.stderr)
        if available:
            print(f"Available versions: {available}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    has_bible_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Bible'"
    ).fetchone()
    if not has_bible_table:
        conn.close()
        print(f"Error: '{db_path}' does not contain a `Bible` table.", file=sys.stderr)
        sys.exit(1)

    rows = conn.execute(
        "SELECT Book, Chapter, Scripture FROM Bible ORDER BY Book, Chapter"
    ).fetchall()
    conn.close()

    target_root = os.path.join(out_dir, abbr)
    os.makedirs(target_root, exist_ok=True)

    books_seen = set()
    files_written = 0
    for book, chapter, scripture in rows:
        book_abbr = BOOK_ABBR.get(book, f"Book{book}")
        book_folder = os.path.join(target_root, f"{book:02d}-{book_abbr}")
        os.makedirs(book_folder, exist_ok=True)
        books_seen.add(book)

        book_name = BOOK_NAMES.get(book, f"Book {book}")
        header = f"# {book_name}" if book == 0 else f"# {book_name} {chapter}"
        body = html_to_markdown(scripture)
        content = f"{header}\n\n{body}\n" if body else f"{header}\n"

        chap_path = os.path.join(book_folder, f"{chapter:03d}.md")
        with open(chap_path, "w", encoding="utf-8") as f:
            f.write(content)
        files_written += 1

    print(f"Exported {abbr} ({db_path}) -> {os.path.abspath(target_root)}")
    print(f"Books: {len(books_seen)}, Chapter files: {files_written}")


def main():
    parser = argparse.ArgumentParser(description="Export a .bible `Bible` table to Markdown files.")
    parser.add_argument("version", help="Bible version name, abbreviation, or .bible path")
    parser.add_argument("--out-dir", default="", help="Parent directory for the <ABBR> folder (default: <repo_root>/bibles)")
    args = parser.parse_args()
    export_bible(args.version, args.out_dir)


if __name__ == "__main__":
    main()
