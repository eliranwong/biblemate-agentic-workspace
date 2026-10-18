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

def get_available_commentaries():
    home = os.path.expanduser('~')
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    paths = [
        os.path.join(base, 'data', 'commentaries'),
        os.path.join(base, 'data_custom', 'commentaries')
    ]
    commentaries = {}
    for p in paths:
        if os.path.exists(p):
            for filepath in glob.glob(os.path.join(p, 'c*.commentary')):
                filename = os.path.basename(filepath)
                ver_name = filename[1:-11].upper()
                commentaries[ver_name] = filepath
    return commentaries

def parse_query(query_str):
    available_commentaries = get_available_commentaries()
    tokens = query_str.strip().split()
    if not tokens:
        return [], []
        
    versions = []
    ref_start_idx = 0
    
    for i, token in enumerate(tokens):
        clean_token = token.strip(',;').upper()
        if clean_token in available_commentaries:
            if clean_token not in versions:
                versions.append(clean_token)
            ref_start_idx = i + 1
        else:
            break
            
    default_version = 'AIC'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pref_path = os.path.abspath(os.path.join(script_dir, '..', '..', 'preferences', 'commentary.md'))
    if os.path.exists(pref_path):
        try:
            with open(pref_path, 'r', encoding='utf-8') as f:
                pref_content = f.read().strip().upper()
                if pref_content:
                    default_version = pref_content
        except Exception:
            pass

    if not versions:
        if default_version in available_commentaries:
            versions = [default_version]
        elif available_commentaries:
            versions = [sorted(available_commentaries.keys())[0]]
        else:
            print("Error: No commentary databases found in ~/biblemate/data/commentaries or ~/biblemate/data_custom/commentaries.")
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

def clean_commentary_html(text):
    if not text:
        return ""
    t = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    t = re.sub(r'</p>', '\n\n', t, flags=re.IGNORECASE)
    t = re.sub(r'<hr\s*/?>', '\n---\n', t, flags=re.IGNORECASE)
    t = re.sub(r'<[^>]+>', '', t)
    
    t = t.replace('&#147;', '“').replace('&#148;', '”').replace('&#146;', '’').replace('&#145;', '‘')
    t = t.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

def extract_from_vid_tags(text, book, chapter, target_verses):
    pattern = re.compile(r'<vid\s+id=["\']v(\d+)\.(\d+)\.(\d+)["\'][^>]*>.*?</vid>', re.IGNORECASE | re.DOTALL)
    matches = []
    for m in pattern.finditer(text):
        b = int(m.group(1))
        c = int(m.group(2))
        v = int(m.group(3))
        if b == book and c == chapter:
            matches.append({
                'start': m.start(),
                'end': m.end(),
                'verse': v
            })
            
    if not matches:
        return clean_commentary_html(text)
        
    segments = []
    for i in range(len(matches)):
        start_pos = matches[i]['end']
        end_pos = matches[i+1]['start'] if i < len(matches) - 1 else len(text)
        segment_text = text[start_pos:end_pos]
        segments.append({
            'verses': [matches[i]['verse']],
            'text': segment_text
        })
        
    merged_segments = []
    pending_verses = []
    
    for seg in segments:
        text_content = re.sub(r'<[^>]+>', '', seg['text']).strip()
        if not text_content:
            pending_verses.extend(seg['verses'])
        else:
            current_verses = pending_verses + seg['verses']
            merged_segments.append({
                'verses': current_verses,
                'text': seg['text']
            })
            pending_verses = []
            
    if pending_verses and merged_segments:
        merged_segments[-1]['verses'].extend(pending_verses)
        
    matching_texts = []
    for seg in merged_segments:
        intersection = set(seg['verses']).intersection(target_verses)
        if intersection:
            cleaned = clean_commentary_html(seg['text'])
            if cleaned:
                vs_str = ",".join(str(v) for v in sorted(seg['verses']))
                matching_texts.append(f"[Commentary for Verse(s) {vs_str}]:\n{cleaned}")
                
    return "\n\n".join(matching_texts).strip()

def fetch_commentary(db_path, book_num, ref_info):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database {db_path}: {e}")
        return []
        
    try:
        cursor.execute("PRAGMA table_info(Commentary)")
        cols = [row[1] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error reading table info from {db_path}: {e}")
        conn.close()
        return []
        
    if not cols:
        conn.close()
        return []
        
    has_verse = 'Verse' in cols
    text_col = 'Scripture'
    if 'Content' in cols:
        text_col = 'Content'
    elif 'Scripture' in cols:
        text_col = 'Scripture'
    else:
        text_col = cols[-1]
        
    ref_type = ref_info['type']
    
    if has_verse:
        if ref_type == 'verse_range':
            query = f"SELECT Chapter, Verse, {text_col} FROM Commentary WHERE Book = ? AND Chapter = ? AND Verse >= ? AND Verse <= ? ORDER BY Chapter, Verse"
            params = (book_num, ref_info['chapter'], ref_info['verse_start'], ref_info['verse_end'])
        elif ref_type == 'single_verse':
            query = f"SELECT Chapter, Verse, {text_col} FROM Commentary WHERE Book = ? AND Chapter = ? AND Verse = ? ORDER BY Chapter, Verse"
            params = (book_num, ref_info['chapter'], ref_info['verse'])
        elif ref_type == 'chapter_range':
            query = f"SELECT Chapter, Verse, {text_col} FROM Commentary WHERE Book = ? AND Chapter >= ? AND Chapter <= ? ORDER BY Chapter, Verse"
            params = (book_num, ref_info['chapter_start'], ref_info['chapter_end'])
        elif ref_type == 'single_chapter':
            query = f"SELECT Chapter, Verse, {text_col} FROM Commentary WHERE Book = ? AND Chapter = ? ORDER BY Chapter, Verse"
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
            
        results = []
        for ch, vs, text in rows:
            if ch == 0 or vs == 0:
                continue
            # Note: For verse-level commentary, we do NOT want to fully strip layout but clean HTML tags.
            cleaned_text = clean_commentary_html(text)
            results.append((ch, vs, cleaned_text))
        return results
        
    else:
        if ref_type in ('verse_range', 'single_verse', 'single_chapter'):
            query = f"SELECT Chapter, {text_col} FROM Commentary WHERE Book = ? AND Chapter = ? ORDER BY Chapter"
            params = (book_num, ref_info['chapter'])
        elif ref_type == 'chapter_range':
            query = f"SELECT Chapter, {text_col} FROM Commentary WHERE Book = ? AND Chapter >= ? AND Chapter <= ? ORDER BY Chapter"
            params = (book_num, ref_info['chapter_start'], ref_info['chapter_end'])
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
            
        results = []
        for ch, text in rows:
            if ch == 0 or not text:
                continue
                
            if ref_type in ('verse_range', 'single_verse'):
                target_verses = set()
                if ref_type == 'verse_range':
                    target_verses = set(range(ref_info['verse_start'], ref_info['verse_end'] + 1))
                else:
                    target_verses = {ref_info['verse']}
                    
                extracted_text = extract_from_vid_tags(text, book_num, ch, target_verses)
                if extracted_text:
                    results.append((ch, None, extracted_text))
            else:
                cleaned_text = clean_commentary_html(text)
                results.append((ch, None, cleaned_text))
        return results

def format_version_commentary(ver_name, book_name, ref_info, results):
    if not results:
        return f"No commentary found for {book_name} in translation {ver_name}."
        
    output_lines = []
    has_verse_precision = any(vs is not None for ch, vs, text in results)
    
    if has_verse_precision:
        for ch, vs, text in results:
            output_lines.append(f"**{book_name} {ch}:{vs}**")
            output_lines.append(text)
            output_lines.append("")
    else:
        for ch, vs, text in results:
            if ref_info['type'] == 'verse_range':
                output_lines.append(f"**{book_name} {ch}:{ref_info['verse_start']}-{ref_info['verse_end']}**")
            elif ref_info['type'] == 'single_verse':
                output_lines.append(f"**{book_name} {ch}:{ref_info['verse']}**")
            else:
                output_lines.append(f"**{book_name} {ch}**")
            output_lines.append(text)
            output_lines.append("")
            
    return "\n".join(output_lines).strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 commentary_retriever.py [versions] [references]")
        print("Example: python3 commentary_retriever.py AIC BI John 3:16-18")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:])
    available_commentaries = get_available_commentaries()
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
            
        current_book_name = OFFICIAL_BOOK_NAMES[book_num]
        ref_output = []
        
        if len(versions) == 1:
            ver = versions[0]
            db_path = available_commentaries[ver]
            results = fetch_commentary(db_path, book_num, parsed_ref)
            formatted = format_version_commentary(ver, current_book_name, parsed_ref, results)
            ref_output.append(f"### {current_book_name} ({ver})\n\n{formatted}")
        else:
            ref_output.append(f"### Commentary Comparison for {ref_item}")
            for ver in versions:
                db_path = available_commentaries[ver]
                results = fetch_commentary(db_path, book_num, parsed_ref)
                formatted = format_version_commentary(ver, current_book_name, parsed_ref, results)
                ref_output.append(f"#### [{ver}]\n{formatted}")
                
        output_parts.append("\n\n".join(ref_output).strip())
        
    print("\n\n---\n\n".join(output_parts))

if __name__ == "__main__":
    main()
