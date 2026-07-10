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

# Chinese mappings
CHINESE_BOOK_MAP = {
    1: ["创世记", "创世記", "创", "創"],
    2: ["出埃及记", "出埃及記", "出"],
    3: ["利未记", "利未記", "利"],
    4: ["民数记", "民数記", "民"],
    5: ["申命记", "申命記", "申"],
    6: ["约书亚记", "约书亚記", "约书亞记", "約書亞記", "书", "書"],
    7: ["士师记", "士师記", "士師記", "士"],
    8: ["路得记", "路得記", "得"],
    9: ["撒母耳记上", "撒母耳記上", "撒上"],
    10: ["撒母耳记下", "撒母耳記下", "撒下"],
    11: ["列王纪上", "列王紀上", "列王記上", "王上"],
    12: ["列王纪下", "列王紀下", "列王記上", "王下"],
    13: ["历代志上", "歷代志上", "代上"],
    14: ["历代志下", "歷代志下", "代下"],
    15: ["以斯拉记", "以斯拉記", "拉"],
    16: ["尼希米记", "尼希米記", "尼"],
    17: ["以斯帖记", "以斯帖記", "帖"],
    18: ["约伯记", "约伯記", "約伯記", "伯"],
    19: ["诗篇", "詩篇", "诗", "詩"],
    20: ["箴言", "箴"],
    21: ["传道书", "傳道書", "传", "傳"],
    22: ["雅歌", "歌"],
    23: ["以赛亚书", "以賽亞書", "赛", "賽"],
    24: ["耶利米书", "耶利米書", "耶"],
    25: ["耶利米哀歌", "哀"],
    26: ["以西结书", "以西結書", "结", "結"],
    27: ["但以理书", "但以理書", "但"],
    28: ["何西阿书", "何西阿書", "何"],
    29: ["约耳书", "约耳書", "約耳書", "珥"],
    30: ["阿摩司书", "阿摩司書", "摩"],
    31: ["俄巴底亚书", "俄巴底亞書", "俄"],
    32: ["约拿书", "约拿書", "約拿書", "拿"],
    33: ["弥迦书", "弥迦書", "彌迦書", "弥", "彌"],
    34: ["那鸿书", "那鸿書", "那鴻書", "鸿", "鴻"],
    35: ["哈巴谷书", "哈巴谷書", "哈"],
    36: ["西番雅书", "西番雅書", "番"],
    37: ["哈该书", "哈该書", "哈該書", "该", "該"],
    38: ["撒迦利亚书", "撒迦利亚書", "撒迦利亞書", "亚", "亞"],
    39: ["玛拉基书", "玛拉基書", "瑪拉基書", "玛", "瑪"],
    40: ["马太福音", "馬太福音", "太"],
    41: ["马可福音", "馬可福音", "可"],
    42: ["路加福音", "路加福音", "路"],
    43: ["约翰福音", "約翰福音", "约", "約"],
    44: ["使徒行传", "使徒行傳", "徒"],
    45: ["罗马书", "羅馬書", "罗", "羅"],
    46: ["哥林多前书", "哥林多前書", "林前"],
    47: ["哥林多后书", "哥林多後書", "林后", "林後"],
    48: ["加拉太书", "加拉太書", "加"],
    49: ["以弗所书", "以弗所書", "弗"],
    50: ["腓立比书", "腓立比書", "腓"],
    51: ["歌罗西书", "歌羅西書", "西"],
    52: ["帖撒罗尼迦前书", "帖撒羅尼迦前書", "帖前"],
    53: ["帖撒罗尼迦后书", "帖撒羅尼迦後書", "帖后", "帖後"],
    54: ["提摩太前书", "提摩太前書", "提前"],
    55: ["提摩太后书", "提摩太後書", "提后", "提後"],
    56: ["提多书", "提多書", "多"],
    57: ["腓利门书", "腓利門書", "门", "門"],
    58: ["希伯来书", "希伯來書", "希"],
    59: ["雅各书", "雅各書", "雅"],
    60: ["彼得前书", "彼得前書", "彼前"],
    61: ["彼得后书", "彼得後書", "彼后", "彼後"],
    62: ["约翰一书", "約翰一書", "约一", "約一"],
    63: ["约翰二书", "約翰二書", "约二", "約二"],
    64: ["约翰三书", "約翰三書", "约三", "約三"],
    65: ["犹大书", "猶大書", "犹", "猶"],
    66: ["启示录", "啟示錄", "启", "啟"]
}

# Populating BOOK_MAP
for book_num, aliases in raw_mappings.items():
    BOOK_MAP[OFFICIAL_BOOK_NAMES[book_num].lower()] = book_num
    for alias in aliases:
        BOOK_MAP[alias] = book_num

for book_num, aliases in CHINESE_BOOK_MAP.items():
    for alias in aliases:
        BOOK_MAP[alias.lower()] = book_num

SECTION_NAMES = {
    0: "Overview",
    1: "Structural Outline",
    2: "Logical Flow",
    3: "Historical Setting",
    4: "Themes",
    5: "Keywords",
    6: "Theology",
    7: "Canonical Placement",
    8: "Practical Living",
    9: "Summary"
}

def get_book_number(book_name):
    normalized = book_name.strip().lower().replace('.', '')
    normalized = re.sub(r'\s+', ' ', normalized)
    return BOOK_MAP.get(normalized, None)

def clean_content_text(text):
    if not text:
        return ""
    # Replace <br> with newlines
    t = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    # Replace <ref onclick="...">text</ref> with just text
    t = re.sub(r'<ref[^>]*>(.*?)</ref>', r'\1', t, flags=re.DOTALL | re.IGNORECASE)
    # Strip any other HTML tags
    t = re.sub(r'<[^>]+>', '', t)
    # Resolve HTML entities
    t = t.replace('&#147;', '“').replace('&#148;', '”').replace('&#146;', '’').replace('&#145;', '‘')
    t = t.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

def detect_chinese_lang(query_str):
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in query_str)
    if not has_chinese:
        return 'en'
    traditional_chars = {'記', '書', '約', '傳', '後', '馬', '啟', '羅', '林', '帖', '彌', '門', '猶'}
    if any(char in traditional_chars for char in query_str):
        return 'tc'
    return 'sc'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 book_analysis_retriever.py [--lang en|sc|tc] [--section <0-9>] <Book>")
        print("Example: python3 book_analysis_retriever.py --section 0 Ezra")
        sys.exit(1)

    args = sys.argv[1:]
    
    # Parse options
    lang = None
    section_to_fetch = None
    query_parts = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ('--lang', '-l') and i + 1 < len(args):
            lang = args[i+1].lower()
            i += 2
        elif arg in ('--sc', '-sc'):
            lang = 'sc'
            i += 1
        elif arg in ('--tc', '-tc'):
            lang = 'tc'
            i += 1
        elif arg in ('--en', '-en'):
            lang = 'en'
            i += 1
        elif arg in ('--section', '-s') and i + 1 < len(args):
            try:
                section_to_fetch = int(args[i+1])
            except ValueError:
                print(f"Error: Invalid section index '{args[i+1]}'. Must be 0-9.")
                sys.exit(1)
            i += 2
        else:
            query_parts.append(arg)
            i += 1

    query_str = " ".join(query_parts).strip()
    if not query_str:
        print("Error: No bible book specified.")
        sys.exit(1)

    # Detect language if not explicitly specified
    if not lang:
        lang = detect_chinese_lang(query_str)

    book_num = get_book_number(query_str)
    if not book_num:
        print(f"Error: Unknown book name or abbreviation: '{query_str}'")
        sys.exit(1)

    # Resolve database path portably
    home = os.path.expanduser('~')
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    
    if lang == 'sc':
        db_filename = 'book_analysis_sc.data'
    elif lang == 'tc':
        db_filename = 'book_analysis_tc.data'
    else:
        db_filename = 'book_analysis.data'

    db_path = os.path.join(base, 'data', 'data', db_filename)

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if section_to_fetch is not None:
            cursor.execute("SELECT Section, Content FROM Introduction WHERE Book = ? AND Section = ?", (book_num, section_to_fetch))
        else:
            cursor.execute("SELECT Section, Content FROM Introduction WHERE Book = ? ORDER BY Section ASC", (book_num,))
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
        sys.exit(1)

    if not rows:
        lang_label = "Traditional Chinese" if lang == 'tc' else ("Simplified Chinese" if lang == 'sc' else "English")
        print(f"No local book analysis data found for {OFFICIAL_BOOK_NAMES[book_num]} ({lang_label}).")
        sys.exit(0)

    for section_idx, content in rows:
        section_name = SECTION_NAMES.get(section_idx, f"Section {section_idx}")
        cleaned_content = clean_content_text(content)
        if len(rows) > 1:
            print(f"## {section_name}\n")
            print(cleaned_content)
            print("\n" + "="*80 + "\n")
        else:
            print(cleaned_content)

if __name__ == "__main__":
    main()
