#!/usr/bin/env python3
import os
import sys
import sqlite3
import re

# Standard Protestant Bible Books Mapping
OFFICIAL_BOOK_NAMES = [
    "", # Index 0 is empty
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude",
    "Revelation"
]

# Generate standard abbreviations map to book number
BOOK_MAP = {}
raw_mappings = {
    1: ["genesis", "gen", "ge", "gn"],
    2: ["exodus", "exod", "exo", "ex"],
    3: ["leviticus", "lev", "le", "lv"],
    4: ["numbers", "num", "nu", "nm", "nb"],
    5: ["deuteronomy", "deut", "de", "dt"],
    6: ["joshua", "josh", "jos", "js"],
    7: ["judges", "judg", "jdg", "jg", "jgs"],
    8: ["ruth", "rut", "ru"],
    9: ["1 samuel", "1 sam", "1 sa", "1s", "i samuel", "i sam", "1sam"],
    10: ["2 samuel", "2 sam", "2 sa", "2s", "ii samuel", "ii sam", "2sam"],
    11: ["1 kings", "1 ki", "1 kgs", "1 k", "1k", "i kings", "i ki", "1kings"],
    12: ["2 kings", "2 ki", "2 kgs", "2 k", "2k", "ii kings", "ii ki", "2kings"],
    13: ["1 chronicles", "1 chr", "1 ch", "1chron", "1ch"],
    14: ["2 chronicles", "2 chr", "2 ch", "2chron", "2ch"],
    15: ["ezra", "ezr", "ez"],
    16: ["nehemiah", "neh", "ne"],
    17: ["esther", "esth", "est", "es"],
    18: ["job", "jb"],
    19: ["psalms", "psalm", "ps", "psa", "pss"],
    20: ["proverbs", "prov", "pro", "pr", "pv"],
    21: ["ecclesiastes", "eccles", "ecc", "ec"],
    22: ["song of solomon", "song of songs", "song", "so", "sng", "canticles", "cant"],
    23: ["isaiah", "isa", "is"],
    24: ["jeremiah", "jer", "je", "jr"],
    25: ["lamentations", "lam", "la"],
    26: ["ezekiel", "ezek", "eze", "ek"],
    27: ["daniel", "dan", "da", "dn"],
    28: ["hosea", "hos", "ho"],
    29: ["joel", "joe", "jl"],
    30: ["amos", "amo", "am"],
    31: ["obadiah", "obad", "oba", "ob"],
    32: ["jonah", "jon", "jnh"],
    33: ["micah", "mic", "mc"],
    34: ["nahum", "nah", "na"],
    35: ["habakkuk", "hab", "hb"],
    36: ["zephaniah", "zeph", "zep", "zp"],
    37: ["haggai", "hagg", "hag", "hg"],
    38: ["zechariah", "zech", "zec", "zc"],
    39: ["malachi", "mal", "ml"],
    40: ["matthew", "matt", "mat", "mt"],
    41: ["mark", "mrk", "mk"],
    42: ["luke", "luk", "lk"],
    43: ["john", "joh", "jhn", "jn"],
    44: ["acts", "act", "ac"],
    45: ["romans", "rom", "rm", "ro"],
    46: ["1 corinthians", "1 cor", "1 co", "1c", "i corinthians", "i cor", "1cor"],
    47: ["2 corinthians", "2 cor", "2 co", "2c", "ii corinthians", "ii cor", "2cor"],
    48: ["galatians", "gal", "ga"],
    49: ["ephesians", "eph", "ep"],
    50: ["philippians", "phil", "php", "pp"],
    51: ["colossians", "col", "co"],
    52: ["1 thessalonians", "1 thess", "1 th", "1ts", "i thessalonians", "i thess", "1thess"],
    53: ["2 thessalonians", "2 thess", "2 th", "2ts", "ii thessalonians", "ii thess", "2thess"],
    54: ["1 timothy", "1 tim", "1 ti", "1t", "i timothy", "i tim", "1tim"],
    55: ["2 timothy", "2 tim", "2 ti", "2t", "ii timothy", "ii tim", "2tim"],
    56: ["titus", "tit", "ti", "ts"],
    57: ["philemon", "philem", "phm", "pm"],
    58: ["hebrews", "heb", "he"],
    59: ["james", "jas", "jm"],
    60: ["1 peter", "1 pet", "1 pe", "1 pt", "1p", "i peter", "i pet", "1pet"],
    61: ["2 peter", "2 pet", "2 pe", "2 pt", "2p", "ii peter", "ii pet", "2pet"],
    62: ["1 john", "1 jn", "1 joh", "1 jhn", "1j", "i john", "i jn", "1john"],
    63: ["2 john", "2 jn", "2 joh", "2 jhn", "2j", "ii john", "ii jn", "2john"],
    64: ["3 john", "3 jn", "3 joh", "3 jhn", "3j", "iii john", "iii jn", "3john"],
    65: ["jude", "jud", "jd"],
    66: ["revelation", "rev", "re", "the revelation"]
}

for book_num, aliases in raw_mappings.items():
    BOOK_MAP[OFFICIAL_BOOK_NAMES[book_num].lower()] = book_num
    for alias in aliases:
        BOOK_MAP[alias] = book_num

STOP_WORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'if', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'as'}

def get_book_number(book_name):
    normalized = book_name.strip().lower().replace('.', '')
    normalized = re.sub(r'\s+', ' ', normalized)
    return BOOK_MAP.get(normalized, None)

def parse_single_ref(ref_str):
    # Pattern 1: Book C:V-V (e.g. John 3:16-18)
    m1 = re.match(r'^\s*(.*?)\s*(\d+)\s*:\s*(\d+)\s*-\s*(\d+)\s*$', ref_str)
    if m1:
        return {
            'book_name': m1.group(1).strip(),
            'type': 'verse_range',
            'chapter': int(m1.group(2)),
            'verse_start': int(m1.group(3)),
            'verse_end': int(m1.group(4))
        }
        
    # Pattern 2: Book C:V (e.g. John 3:16)
    m2 = re.match(r'^\s*(.*?)\s*(\d+)\s*:\s*(\d+)\s*$', ref_str)
    if m2:
        return {
            'book_name': m2.group(1).strip(),
            'type': 'single_verse',
            'chapter': int(m2.group(2)),
            'verse': int(m2.group(3))
        }
        
    # Pattern 3: Book C-C (e.g. Rom 5-8)
    m3 = re.match(r'^\s*(.*?)\s*(\d+)\s*-\s*(\d+)\s*$', ref_str)
    if m3:
        return {
            'book_name': m3.group(1).strip(),
            'type': 'chapter_range',
            'chapter_start': int(m3.group(2)),
            'chapter_end': int(m3.group(3))
        }
        
    # Pattern 4: Book C (e.g. John 3)
    m4 = re.match(r'^\s*(.*?)\s*(\d+)\s*$', ref_str)
    if m4:
        return {
            'book_name': m4.group(1).strip(),
            'type': 'single_chapter',
            'chapter': int(m4.group(2))
        }
        
    return None

def parse_references(ref_expr):
    parts = [p.strip() for p in ref_expr.split(';') if p.strip()]
    parsed_refs = []
    for part in parts:
        ref = parse_single_ref(part)
        if ref:
            book_num = get_book_number(ref['book_name'])
            if book_num:
                ref['book_num'] = book_num
                parsed_refs.append(ref)
            else:
                # Invalid book name
                return []
        else:
            # Invalid reference format
            return []
    return parsed_refs

def parse_query_string(query_str):
    # Splits by " in " case-insensitively
    pattern = re.compile(r'\s+in\s+', re.IGNORECASE)
    matches = list(pattern.finditer(query_str))
    
    if not matches:
        # Assume whole string is references
        parsed_refs = parse_references(query_str)
        if parsed_refs:
            return None, parsed_refs
        return None, []
        
    # Start checking from the last match backwards
    for m in reversed(matches):
        left = query_str[:m.start()].strip()
        right = query_str[m.end():].strip()
        
        parsed_refs = parse_references(right)
        if parsed_refs:
            return left, parsed_refs
            
    # Fallback: parse entire string as reference
    parsed_refs = parse_references(query_str)
    return None, parsed_refs

def is_row_match(word, row):
    # Check Word, Lexeme, Transliteration, Translation, Gloss
    fields = [row['Word'], row['Lexeme'], row['Transliteration'], row['Translation'], row['Gloss']]
    word_lower = word.lower()
    for f in fields:
        if f and word_lower in f.lower():
            return True
    return False

def match_subsequence(q_idx, row_start, rows, q_words):
    if q_idx == len(q_words):
        return []
    for i in range(row_start, len(rows)):
        if is_row_match(q_words[q_idx], rows[i]):
            rest = match_subsequence(q_idx + 1, i + 1, rows, q_words)
            if rest is not None:
                return [i] + rest
    return None

def get_bible_verse_text(book_num, chapter, verse):
    home = os.path.expanduser('~')
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    bible_paths = [
        os.path.join(base, 'data', 'bibles', 'NET.bible'),
        os.path.join(base, 'data', 'bibles', 'BSB.bible'),
        os.path.join(base, 'data', 'bibles', 'KJV.bible')
    ]
    for path in bible_paths:
        if os.path.exists(path):
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT Scripture FROM Verses WHERE Book = ? AND Chapter = ? AND Verse = ?", (book_num, chapter, verse))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return row[0]
            except Exception:
                pass
    return None

def filter_verse_rows(verse_rows, query_phrase):
    q_words = [w.strip() for w in query_phrase.lower().split() if w.strip()]
    if not q_words:
        return verse_rows
        
    # 1. Try strict subsequence match first
    matched_indices = match_subsequence(0, 0, verse_rows, q_words)
    if matched_indices:
        return [verse_rows[idx] for idx in matched_indices]
        
    # 2. Try unordered match on non-stop words
    major_words = [w for w in q_words if w not in STOP_WORDS]
    if not major_words:
        major_words = q_words # if all are stop words, search for all
        
    # Check if all major words are present in the verse
    all_present = True
    for mw in major_words:
        any_match = any(is_row_match(mw, row) for row in verse_rows)
        if not any_match:
            all_present = False
            break
            
    if all_present:
        # Return all rows in the verse that match any of the query words
        matched_rows = []
        for row in verse_rows:
            if any(is_row_match(qw, row) for qw in q_words):
                matched_rows.append(row)
        return matched_rows
        
    # 3. Fallback: try positional alignment with English Bible translation
    if verse_rows:
        book_num = verse_rows[0]['Book']
        chapter = verse_rows[0]['Chapter']
        verse = verse_rows[0]['Verse']
        text_eng = get_bible_verse_text(book_num, chapter, verse)
        if text_eng:
            # Clean and tokenize English text
            eng_words = [w.strip("(),.?!;:\"'").lower() for w in text_eng.split() if w.strip("(),.?!;:\"'")]
            
            # Tokenize morphology translations/glosses
            morph_words = []
            for idx, row in enumerate(verse_rows):
                m_val = ((row['Translation'] or "") + " " + (row['Gloss'] or "")).strip()
                words = [w.strip("(),.?!;:\"'").lower() for w in m_val.split() if w.strip("(),.?!;:\"'")]
                morph_words.append((idx, words))
                
            # Align query words
            aligned_indices = set()
            for qw in q_words:
                for e_idx, e_w in enumerate(eng_words):
                    if qw in e_w or e_w in qw:
                        # Find direct matches first to see what's already mapped
                        direct_mappings = {}
                        used_rows = set()
                        for i, ew in enumerate(eng_words):
                            for r_idx, m_ws in morph_words:
                                if r_idx not in used_rows:
                                    if any(ew in mw or mw in ew for mw in m_ws):
                                        direct_mappings[i] = r_idx
                                        used_rows.add(r_idx)
                                        break
                                        
                        if e_idx in direct_mappings:
                            aligned_indices.add(direct_mappings[e_idx])
                        else:
                            # Positional fallback for this specific word
                            unmapped_rows = [r_idx for r_idx, _ in morph_words if r_idx not in used_rows]
                            if unmapped_rows:
                                best_row_idx = min(unmapped_rows, key=lambda r_idx: abs((r_idx / len(verse_rows)) - (e_idx / len(eng_words))))
                                aligned_indices.add(best_row_idx)
                                
            if aligned_indices:
                return [verse_rows[idx] for idx in sorted(list(aligned_indices))]
                
    return []

def query_db(db_path, parsed_refs):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
        
    all_rows = []
    for ref in parsed_refs:
        book_num = ref['book_num']
        ref_type = ref['type']
        
        if ref_type == 'single_verse':
            query = "SELECT * FROM morphology WHERE Book = ? AND Chapter = ? AND Verse = ? ORDER BY WordID"
            params = (book_num, ref['chapter'], ref['verse'])
        elif ref_type == 'verse_range':
            query = "SELECT * FROM morphology WHERE Book = ? AND Chapter = ? AND Verse >= ? AND Verse <= ? ORDER BY WordID"
            params = (book_num, ref['chapter'], ref['verse_start'], ref['verse_end'])
        elif ref_type == 'single_chapter':
            query = "SELECT * FROM morphology WHERE Book = ? AND Chapter = ? ORDER BY WordID"
            params = (book_num, ref['chapter'])
        elif ref_type == 'chapter_range':
            query = "SELECT * FROM morphology WHERE Book = ? AND Chapter >= ? AND Chapter <= ? ORDER BY WordID"
            params = (book_num, ref['chapter_start'], ref['chapter_end'])
        else:
            continue
            
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            # Convert row objects to dicts
            all_rows.extend([dict(r) for r in rows])
        except Exception as e:
            print(f"Error querying database for {ref}: {e}")
            
    conn.close()
    return all_rows

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 morphology_retriever.py <query>")
        print("Examples:")
        print("  python3 morphology_retriever.py \"John 3:16\"")
        print("  python3 morphology_retriever.py \"love the world in John 3:16\"")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:]).strip()
    query_phrase, parsed_refs = parse_query_string(query_str)
    
    if not parsed_refs:
        print("Error: Could not parse reference expression or find valid book name.")
        print("Please verify references (e.g. 'John 3:16', 'Genesis 1:1-3', 'Rom 5-8').")
        sys.exit(1)
        
    db_path = os.path.join(os.environ.get('BIBLEMATE_DATA') or os.path.join(os.path.expanduser('~'), 'biblemate'), 'data', 'morphology.sqlite')
    if not os.path.exists(db_path):
        print(f"Error: Morphology database not found at {db_path}.")
        sys.exit(1)
        
    raw_rows = query_db(db_path, parsed_refs)
    
    if not raw_rows:
        print("No morphology data found for the specified references.")
        sys.exit(1)
        
    # Group rows by Book, Chapter, Verse to perform verse-level keyword filtering
    grouped_rows = {}
    for r in raw_rows:
        key = (r['Book'], r['Chapter'], r['Verse'])
        if key not in grouped_rows:
            grouped_rows[key] = []
        grouped_rows[key].append(r)
        
    final_rows = []
    for key, verse_rows in grouped_rows.items():
        if query_phrase:
            matched_verse_rows = filter_verse_rows(verse_rows, query_phrase)
            final_rows.extend(matched_verse_rows)
        else:
            final_rows.extend(verse_rows)
            
    if not final_rows:
        print(f"No matching morphology data found for query '{query_phrase}' in the specified verses.")
        sys.exit(0)
        
    # Print results formatted in Markdown tables for each word
    for row in final_rows:
        book_name = OFFICIAL_BOOK_NAMES[row['Book']]
        ref_str = f"{book_name} {row['Chapter']}:{row['Verse']}"
        
        # Clean any trailing commas/spacing in morphology and entries
        morph_details = row['Morphology'].strip().rstrip(',')
        lex_entry = row['LexicalEntry'].strip().rstrip(',')
        
        print(f"### {ref_str} (Word ID: {row['WordID']}, Clause ID: {row['ClauseID']})")
        print("| Attribute | Value |")
        print("| :--- | :--- |")
        print(f"| **Word / Lexeme** | {row['Word']} / {row['Lexeme']} |")
        print(f"| **Transliteration / Pronunciation** | `{row['Transliteration']}` / `{row['Pronunciation']}` |")
        print(f"| **Lexical Entry** | `{lex_entry}` |")
        print(f"| **Morphology Code** | `{row['MorphologyCode']}` |")
        print(f"| **Morphology Details** | {morph_details} |")
        print(f"| **Translation / Gloss** | **{row['Translation']}** (gloss: *{row['Gloss']}*) |")
        print(f"| **Interlinear** | `{row['Interlinear']}` |")
        print()

if __name__ == '__main__':
    main()
