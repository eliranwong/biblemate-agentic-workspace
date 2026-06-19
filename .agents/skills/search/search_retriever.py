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

def get_available_versions():
    home = os.path.expanduser('~')
    paths = [
        os.path.join(home, 'biblemate', 'data', 'bibles'),
        os.path.join(home, 'biblemate', 'data_custom', 'bibles')
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
        return [], ""
        
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
            
    if not versions:
        if 'NET' in available_versions:
            versions = ['NET']
        elif available_versions:
            versions = [sorted(available_versions.keys())[0]]
        else:
            print("Error: No bible databases found in ~/biblemate/data/bibles or ~/biblemate/data_custom/bibles.")
            sys.exit(1)
            
    search_expr = " ".join(tokens[ref_start_idx:])
    return versions, search_expr

def wildcard_to_regex(pattern_str):
    escaped = re.escape(pattern_str)
    # Replace escaped wildcards with regex equivalents
    # re.escape escapes '*' as '\*' and '?' as '\?'
    regex_str = escaped.replace(r'\*', '.*').replace(r'\?', '.')
    return re.compile(regex_str, re.IGNORECASE)

def make_matcher(query_str):
    # Split by OR operator '|'
    or_parts = query_str.split('|')
    
    and_groups = []
    for part in or_parts:
        # Split by AND operator '+'
        and_parts = [p.strip() for p in part.split('+') if p.strip()]
        if and_parts:
            compiled_group = [wildcard_to_regex(term) for term in and_parts]
            and_groups.append(compiled_group)
            
    def match_text(text):
        if not text:
            return False
        # Strip html tags before matching
        clean_text = re.sub(r'<[^>]+>', '', text)
        for and_group in and_groups:
            group_matches = True
            for pattern in and_group:
                if not pattern.search(clean_text):
                    group_matches = False
                    break
            if group_matches:
                return True
        return False
        
    return match_text

def search_db(db_path, matcher):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT Book, Chapter, Verse, Scripture FROM Verses WHERE Book > 0 AND Chapter > 0 AND Verse > 0")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"Error querying database {db_path}: {e}")
        return {}
        
    matches = {}
    for book, chapter, verse, scripture in rows:
        if matcher(scripture):
            # Clean up tags for memory storage
            clean_text = re.sub(r'<[^>]+>', '', scripture).strip()
            matches[(book, chapter, verse)] = clean_text
    return matches

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_retriever.py [versions] [search_expression]")
        print("Example: python3 search_retriever.py NET CUV love*God")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:])
    available_versions = get_available_versions()
    versions, search_expr = parse_query(query_str)
    
    if not search_expr:
        print("Error: No search expression specified.")
        sys.exit(1)
        
    matcher = make_matcher(search_expr)
    
    # Store matches per version
    # version_matches[ver] = {(book, chapter, verse): text}
    version_matches = {}
    all_matching_coords = set()
    
    for ver in versions:
        db_path = available_versions[ver]
        matches = search_db(db_path, matcher)
        version_matches[ver] = matches
        all_matching_coords.update(matches.keys())
        
    if not all_matching_coords:
        print(f"No matches found for search expression: '{search_expr}'")
        sys.exit(0)
        
    # Compile statistics
    version_counts = {ver: len(version_matches[ver]) for ver in versions}
    
    book_counts = {}
    for (b, c, v) in all_matching_coords:
        book_counts[b] = book_counts.get(b, 0) + 1
        
    # Sort matching coordinates
    sorted_coords = sorted(list(all_matching_coords))
    
    # Print summary header
    print(f"## Search Results for: \"{search_expr}\"\n")
    print("### Summary")
    print(f"- **Total unique matching verses:** {len(sorted_coords)}")
    print("- **Matches by Version:**")
    for ver in versions:
        print(f"  - **{ver}:** {version_counts[ver]} matches")
    print("- **Matches by Book:**")
    for b in sorted(book_counts.keys()):
        print(f"  - **{OFFICIAL_BOOK_NAMES[b]}:** {book_counts[b]} matches")
    print("\n---\n")
    
    # Display matches section by section per version
    for ver in versions:
        matches = version_matches[ver]
        sorted_ver_coords = sorted(matches.keys())
        print(f"## Version: {ver} ({len(sorted_ver_coords)} matches)\n")
        
        if not sorted_ver_coords:
            print("No matches found in this version.\n")
            print("---\n")
            continue
            
        display_limit = 100
        display_coords = sorted_ver_coords[:display_limit]
        
        current_book = None
        current_chapter = None
        
        for (b, c, v) in display_coords:
            if b != current_book or c != current_chapter:
                current_book = b
                current_chapter = c
                print(f"\n### {OFFICIAL_BOOK_NAMES[b]} {c}\n")
                
            text = matches[(b, c, v)]
            print(f"**{OFFICIAL_BOOK_NAMES[b]} {c}:{v}**")
            print(f"- **[{ver}]** {text}\n")
            
        if len(sorted_ver_coords) > display_limit:
            print(f"*Showing first {display_limit} matches for {ver}. Use more specific terms to refine your search.*\n")
            
        print("---\n")

if __name__ == "__main__":
    main()
