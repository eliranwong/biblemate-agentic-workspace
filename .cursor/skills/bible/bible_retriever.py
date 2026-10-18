#!/usr/bin/env python3
import os
import sys
import sqlite3
import re
import glob

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
    9: ["1 samuel", "1 sam", "1 sa", "1s", "i samuel", "i sam", "1sam", "1sa"],
    10: ["2 samuel", "2 sam", "2 sa", "2s", "ii samuel", "ii sam", "2sam", "2sa"],
    11: ["1 kings", "1 ki", "1 kgs", "1 k", "1k", "i kings", "i ki", "1kings", "1ki", "1kgs"],
    12: ["2 kings", "2 ki", "2 kgs", "2 k", "2k", "ii kings", "ii ki", "2kings", "2ki", "2kgs"],
    13: ["1 chronicles", "1 chr", "1 ch", "1chron", "1ch", "1chr"],
    14: ["2 chronicles", "2 chr", "2 ch", "2chron", "2ch", "2chr"],
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
    46: ["1 corinthians", "1 cor", "1 co", "1c", "i corinthians", "i cor", "1cor", "1co"],
    47: ["2 corinthians", "2 cor", "2 co", "2c", "ii corinthians", "ii cor", "2cor", "2co"],
    48: ["galatians", "gal", "ga"],
    49: ["ephesians", "eph", "ep"],
    50: ["philippians", "phil", "php", "pp"],
    51: ["colossians", "col", "co"],
    52: ["1 thessalonians", "1 thess", "1 th", "1ts", "i thessalonians", "i thess", "1thess", "1th", "1the"],
    53: ["2 thessalonians", "2 thess", "2 th", "2ts", "ii thessalonians", "ii thess", "2thess", "2th", "2the"],
    54: ["1 timothy", "1 tim", "1 ti", "1t", "i timothy", "i tim", "1tim", "1ti"],
    55: ["2 timothy", "2 tim", "2 ti", "2t", "ii timothy", "ii tim", "2tim", "2ti"],
    56: ["titus", "tit", "ti", "ts"],
    57: ["philemon", "philem", "phm", "pm"],
    58: ["hebrews", "heb", "he"],
    59: ["james", "jas", "jm"],
    60: ["1 peter", "1 pet", "1 pe", "1 pt", "1p", "i peter", "i pet", "1pet", "1pe", "1pt"],
    61: ["2 peter", "2 pet", "2 pe", "2 pt", "2p", "ii peter", "ii pet", "2pet", "2pe", "2pt"],
    62: ["1 john", "1 jn", "1 joh", "1 jhn", "1j", "i john", "i jn", "1john", "1jn", "1jhn", "1joh"],
    63: ["2 john", "2 jn", "2 joh", "2 jhn", "2j", "ii john", "ii jn", "2john", "2jn", "2jhn", "2joh"],
    64: ["3 john", "3 jn", "3 joh", "3 jhn", "3j", "iii john", "iii jn", "3john", "3jn", "3jhn", "3joh"],
    65: ["jude", "jud", "jd"],
    66: ["revelation", "rev", "re", "the revelation"]
}

for book_num, aliases in raw_mappings.items():
    BOOK_MAP[OFFICIAL_BOOK_NAMES[book_num].lower()] = book_num
    for alias in aliases:
        BOOK_MAP[alias] = book_num

def get_available_versions():
    home = os.path.expanduser('~')
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    paths = [
        os.path.join(base, 'data', 'bibles'),
        os.path.join(base, 'data_custom', 'bibles')
    ]
    versions = {}
    for p in paths:
        if os.path.exists(p):
            for filepath in glob.glob(os.path.join(p, '*.bible')):
                filename = os.path.basename(filepath)
                ver_name = os.path.splitext(filename)[0].upper()
                versions[ver_name] = filepath
    return versions

def parse_query(query_str):
    available_versions = get_available_versions()
    tokens = query_str.strip().split()
    if not tokens:
        return [], []
        
    versions = []
    ref_start_idx = 0
    
    for i, token in enumerate(tokens):
        clean_token = token.strip(',;').upper()
        if clean_token in available_versions:
            if clean_token not in versions:
                versions.append(clean_token)
            ref_start_idx = i + 1
        else:
            break

    default_version = 'NET'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pref_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'preferences', 'bible.md'))
    if os.path.exists(pref_path):
        try:
            with open(pref_path, 'r', encoding='utf-8') as f:
                pref_content = f.read().strip().upper()
                if pref_content:
                    default_version = pref_content
        except Exception:
            pass

    if not versions:
        if default_version in available_versions:
            versions = [default_version]
        elif available_versions:
            versions = [sorted(available_versions.keys())[0]]
        else:
            print("Error: No bible databases found in ~/biblemate/data/bibles or ~/biblemate/data_custom/bibles.")
            sys.exit(1)
            
    ref_str = " ".join(tokens[ref_start_idx:])
    return versions, ref_str

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

def get_book_number(book_name):
    normalized = book_name.strip().lower().replace('.', '')
    normalized = re.sub(r'\s+', ' ', normalized)
    return BOOK_MAP.get(normalized, None)

def fetch_verses(db_path, book_num, ref_info):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database {db_path}: {e}")
        return []
        
    ref_type = ref_info['type']
    if ref_type == 'verse_range':
        query = "SELECT Chapter, Verse, Scripture FROM Verses WHERE Book = ? AND Chapter = ? AND Verse >= ? AND Verse <= ? ORDER BY Chapter, Verse"
        params = (book_num, ref_info['chapter'], ref_info['verse_start'], ref_info['verse_end'])
    elif ref_type == 'single_verse':
        query = "SELECT Chapter, Verse, Scripture FROM Verses WHERE Book = ? AND Chapter = ? AND Verse = ? ORDER BY Chapter, Verse"
        params = (book_num, ref_info['chapter'], ref_info['verse'])
    elif ref_type == 'chapter_range':
        query = "SELECT Chapter, Verse, Scripture FROM Verses WHERE Book = ? AND Chapter >= ? AND Chapter <= ? ORDER BY Chapter, Verse"
        params = (book_num, ref_info['chapter_start'], ref_info['chapter_end'])
    elif ref_type == 'single_chapter':
        query = "SELECT Chapter, Verse, Scripture FROM Verses WHERE Book = ? AND Chapter = ? ORDER BY Chapter, Verse"
        params = (book_num, ref_info['chapter'])
    else:
        conn.close()
        return []
        
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error executing query on {db_path}: {e}")
        rows = []
    finally:
        conn.close()
        
    cleaned_rows = []
    for chapter, verse, scripture in rows:
        if chapter == 0 or verse == 0:
            continue
        cleaned_text = re.sub(r'<[^>]+>', '', scripture).strip()
        cleaned_rows.append((chapter, verse, cleaned_text))
        
    return cleaned_rows

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bible_retriever.py [versions] [references]")
        print("Example: python3 bible_retriever.py NET CUV John 3:16-18")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:])
    available_versions = get_available_versions()
    versions, ref_str = parse_query(query_str)
    
    if not ref_str:
        print("Error: No bible reference specified.")
        sys.exit(1)
        
    individual_refs = [r.strip() for r in ref_str.split(';') if r.strip()]
    if not individual_refs:
        print("Error: Invalid bible reference specification.")
        sys.exit(1)
        
    output_parts = []
    
    for ref_item in individual_refs:
        parsed_ref = parse_single_ref(ref_item)
        if not parsed_ref:
            print(f"Error: Could not parse bible reference: '{ref_item}'")
            continue
            
        book_num = get_book_number(parsed_ref['book_name'])
        if not book_num:
            print(f"Error: Unknown bible book name or abbreviation: '{parsed_ref['book_name']}'")
            continue
            
        coords_map = {}
        all_coords = []
        
        for ver in versions:
            db_path = available_versions[ver]
            verses = fetch_verses(db_path, book_num, parsed_ref)
            for ch, vs, text in verses:
                coord = (ch, vs)
                if coord not in coords_map:
                    coords_map[coord] = {}
                    all_coords.append(coord)
                coords_map[coord][ver] = text
                
        all_coords.sort()
        
        if not all_coords:
            print(f"No verses found for reference '{ref_item}' in version(s) {', '.join(versions)}.")
            continue
            
        current_book_name = OFFICIAL_BOOK_NAMES[book_num]
        ref_output = []
        
        # Group consecutive verses into passage chunks
        chunks = []
        current_chunk = []
        for coord in all_coords:
            if not current_chunk:
                current_chunk.append(coord)
            else:
                last_coord = current_chunk[-1]
                # If they belong to the same chapter and verses are consecutive
                if coord[0] == last_coord[0] and coord[1] == last_coord[1] + 1:
                    current_chunk.append(coord)
                else:
                    chunks.append(current_chunk)
                    current_chunk = [coord]
        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            start_ch, start_vs = chunk[0]
            _, end_vs = chunk[-1]
            
            if len(chunk) == 1:
                ref_range = f"{start_ch}:{start_vs}"
            else:
                ref_range = f"{start_ch}:{start_vs}-{end_vs}"
                
            if len(versions) == 1:
                ver = versions[0]
                if len(chunk) == 1:
                    text = coords_map[chunk[0]].get(ver, "(Verse not found)")
                    ref_output.append(f"**{current_book_name} {ref_range} ({ver})**")
                    ref_output.append(text)
                else:
                    passage_parts = []
                    for ch, vs in chunk:
                        text = coords_map[(ch, vs)].get(ver, "(Verse not found)")
                        passage_parts.append(f"[{vs}] {text}")
                    ref_output.append(f"**{current_book_name} {ref_range} ({ver})**")
                    ref_output.append(" ".join(passage_parts))
                ref_output.append("")
            else:
                ref_output.append(f"**{current_book_name} {ref_range}**")
                for ver in versions:
                    if len(chunk) == 1:
                        text = coords_map[chunk[0]].get(ver, "(Verse not found)")
                        ref_output.append(f"- **[{ver}]** {text}")
                    else:
                        passage_parts = []
                        for ch, vs in chunk:
                            text = coords_map[(ch, vs)].get(ver, "(Verse not found)")
                            passage_parts.append(f"[{vs}] {text}")
                        ref_output.append(f"- **[{ver}]** {' '.join(passage_parts)}")
                ref_output.append("")
                
        output_parts.append("\n".join(ref_output).strip())
        
    print("\n\n---\n\n".join(output_parts))

if __name__ == "__main__":
    main()
