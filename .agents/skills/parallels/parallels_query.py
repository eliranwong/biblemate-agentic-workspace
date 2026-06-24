#!/usr/bin/env python3
import os
import sys
import re
import sqlite3
import datetime
import subprocess

# Load parallels_dict.py dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
dict_file = os.path.join(SCRIPT_DIR, 'data', 'parallels_dict.py')
PARALLEL = {}

try:
    with open(dict_file, 'r', encoding='utf-8') as f:
        file_content = f.read()
    local_vars = {}
    exec(file_content, {}, local_vars)
    PARALLEL = local_vars.get('PARALLEL', {})
except Exception as e:
    print(f"Error loading parallels database dictionary: {e}", file=sys.stderr)
    sys.exit(1)

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

def decode_bcv_args(args):
    if len(args) == 3:
        book_num, chap, verse = args
        if book_num < len(OFFICIAL_BOOK_NAMES):
            book = OFFICIAL_BOOK_NAMES[book_num]
            return f"{book} {chap}:{verse}"
    elif len(args) == 5:
        book_num, c_start, v_start, c_end, v_end = args
        if book_num < len(OFFICIAL_BOOK_NAMES):
            book = OFFICIAL_BOOK_NAMES[book_num]
            if c_start == c_end:
                return f"{book} {c_start}:{v_start}-{v_end}"
            else:
                return f"{book} {c_start}:{v_start}-{c_end}:{v_end}"
    return None

def parse_passages(passages_html):
    standardized = passages_html.replace('；', ';').replace('，', ',').replace('：', ':')
    parts = standardized.split(';')
    parsed_refs = []
    last_book = None
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        ref_match = re.search(r'<ref onclick="bcv\(([^)]+)\)">([^<]+)</ref>', part)
        if ref_match:
            bcv_args = [int(x.strip()) for x in ref_match.group(1).split(',')]
            book_num = bcv_args[0]
            if book_num < len(OFFICIAL_BOOK_NAMES):
                last_book = OFFICIAL_BOOK_NAMES[book_num]
                
            nums_match = re.search(r'(\d+)\s*:\s*(\d+)(?:\s*-\s*(?:(\d+)\s*:\s*)?(\d+))?', part)
            if nums_match:
                chap = nums_match.group(1)
                v_start = nums_match.group(2)
                v_end_chap = nums_match.group(3)
                v_end = nums_match.group(4)
                
                if v_end:
                    if v_end_chap:
                        ref_str = f"{last_book} {chap}:{v_start}-{v_end_chap}:{v_end}"
                    else:
                        ref_str = f"{last_book} {chap}:{v_start}-{v_end}"
                else:
                    ref_str = f"{last_book} {chap}:{v_start}"
                parsed_refs.append(ref_str)
            else:
                decoded = decode_bcv_args(bcv_args)
                if decoded:
                    parsed_refs.append(decoded)
        else:
            if last_book:
                cleaned_part = re.sub(r'<[^>]+>', '', part).strip()
                if re.match(r'^\d+', cleaned_part):
                    ref_str = f"{last_book} {cleaned_part}"
                    parsed_refs.append(ref_str)
                else:
                    parsed_refs.append(cleaned_part)
                    
    return parsed_refs

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
        
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def clean_key(key):
    # Decode html entities and replace <br> / <br/> with space
    k = key.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&').replace('&quot;', '"')
    k = re.sub(r'<br\s*/?>', ' ', k, flags=re.IGNORECASE)
    return k.strip()

def get_best_match(query, PARALLEL_dict):
    query_clean = query.strip().lower()
    
    # 1. Exact match (case-insensitive) of cleaned key or parts
    for raw_key in PARALLEL_dict:
        cleaned = clean_key(raw_key).lower()
        if cleaned == query_clean:
            return raw_key
        # Check individual parts split by space or sub-elements
        parts = [p.strip() for p in re.split(r'[\n\-\>\|~]', clean_key(raw_key)) if p.strip()]
        for part in parts:
            if part.lower() == query_clean:
                return raw_key
                
    # 2. Check for containment match (query is inside the key/parts)
    containment_matches = []
    for raw_key in PARALLEL_dict:
        cleaned = clean_key(raw_key).lower()
        parts = [p.strip() for p in re.split(r'[\n\-\>\|~]', clean_key(raw_key)) if p.strip()]
        if query_clean in cleaned or any(query_clean in part.lower() for part in parts):
            containment_matches.append(raw_key)
            
    if len(containment_matches) == 1:
        return containment_matches[0]
    elif len(containment_matches) > 1:
        # Sort by length to get the most specific/shortest matching key
        containment_matches.sort(key=lambda k: len(clean_key(k)))
        return containment_matches[0]
        
    # 3. Check for reverse containment match (key/parts are inside the query)
    reverse_matches = []
    for raw_key in PARALLEL_dict:
        cleaned = clean_key(raw_key).lower()
        if cleaned in query_clean:
            if len(cleaned) >= 4:
                reverse_matches.append(raw_key)
                
    if len(reverse_matches) == 1:
        return reverse_matches[0]
    elif len(reverse_matches) > 1:
        reverse_matches.sort(key=lambda k: len(clean_key(k)))
        return reverse_matches[0]
        
    # 4. Fuzzy match using Levenshtein distance on cleaned key or parts
    best_key = None
    min_distance = 9999
    
    for raw_key in PARALLEL_dict:
        cleaned = clean_key(raw_key).lower()
        parts = [p.strip() for p in re.split(r'[\n\-\>\|~]', clean_key(raw_key)) if p.strip()]
        
        for target in [cleaned] + parts:
            target_lower = target.lower()
            if not target_lower:
                continue
            dist = levenshtein_distance(query_clean, target_lower)
            if dist < min_distance:
                min_distance = dist
                best_key = raw_key
                
    threshold = 2
    if len(query_clean) <= 4:
        threshold = 1
    elif len(query_clean) > 8:
        threshold = 3
        
    if min_distance <= threshold:
        return best_key
        
    return None

def find_db_path():
    # 1. Check user home
    home = os.path.expanduser('~')
    p = os.path.join(home, 'biblemate', 'data', 'collections3.sqlite')
    if os.path.exists(p):
        return p
    # 2. Check workspace relative
    repo_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    p2 = os.path.join(repo_root, 'biblemate', 'data', 'collections3.sqlite')
    if os.path.exists(p2):
        return p2
    return None

def fetch_verse_text(ref, workspace_root):
    retriever_script = os.path.join(workspace_root, '.agents', 'skills', 'bible', 'bible_retriever.py')
    if not os.path.exists(retriever_script):
        return f"**{ref}**\n*(Reference retriever script not found)*"
    try:
        res = subprocess.run(['python3', retriever_script, ref], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        return f"**{ref}**\n*(Failed to retrieve verse text: {e})*"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parallels_query.py <parallels_topic>", file=sys.stderr)
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    best_match = get_best_match(query, PARALLEL)
    
    if not best_match:
        print(f"Error: Could not locate a matching Bible parallels category for '{query}'.", file=sys.stderr)
        sys.exit(1)
        
    entries = PARALLEL[best_match]
    db_path = find_db_path()
    
    if not db_path:
        print("Error: collections3.sqlite database file not found.", file=sys.stderr)
        sys.exit(1)
        
    workspace_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    md = []
    md.append(f"# Bible Parallels: {clean_key(best_match)}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        for tool, number in entries:
            c.execute("SELECT Topic, Passages FROM PARALLEL WHERE Tool = ? AND Number = ?", (int(tool), int(number)))
            row = c.fetchone()
            if not row:
                continue
            topic_name, passages_html = row
            md.append(f"\n## Parallel: {topic_name}\n")
            
            # Extract references from HTML with fallback carry-over parsing
            refs = parse_passages(passages_html)
            for ref in refs:
                verse_text = fetch_verse_text(ref, workspace_root)
                md.append(verse_text)
                md.append("\n---\n") # Section divider
                
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)
        
    md_content = "\n".join(md)
    
    # Save study output to biblemate/ in workspace
    biblemate_dir = os.path.join(workspace_root, 'biblemate')
    os.makedirs(biblemate_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_key(best_match).replace(' ', '_')).lower()
    clean_name = re.sub(r'_{2,}', '_', clean_name).strip('_')
    filename = f"{timestamp}_parallel_{clean_name}.md"
    file_path = os.path.join(biblemate_dir, filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    except Exception as e:
        print(f"Warning: Failed to save study output to {file_path}: {e}", file=sys.stderr)
        
    print(md_content)
    print(f"\n---")
    print(f"Study output saved to: biblemate/{filename}")

if __name__ == "__main__":
    main()
