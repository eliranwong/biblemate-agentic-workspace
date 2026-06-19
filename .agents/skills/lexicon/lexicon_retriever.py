#!/usr/bin/env python3
import os
import sys
import sqlite3
import re
import glob

def get_available_lexicons():
    home = os.path.expanduser('~')
    paths = [
        os.path.join(home, 'biblemate', 'data', 'lexicons'),
        os.path.join(home, 'biblemate', 'data_custom', 'lexicons')
    ]
    lexicons = {}
    for p in paths:
        if os.path.exists(p):
            for filepath in glob.glob(os.path.join(p, '*.lexicon')):
                filename = os.path.basename(filepath)
                lex_name = os.path.splitext(filename)[0].upper()
                lexicons[lex_name] = filepath
    return lexicons

def parse_query(query_str):
    available = get_available_lexicons()
    tokens = query_str.strip().split()
    if not tokens:
        return [], []
        
    versions = []
    ref_start_idx = 0
    
    for i, token in enumerate(tokens):
        clean_token = token.strip(',;').upper()
        if clean_token in available:
            if clean_token not in versions:
                versions.append(clean_token)
            ref_start_idx = i + 1
        else:
            break
            
    if not versions:
        if 'SECE' in available:
            versions = ['SECE']
        elif available:
            versions = [sorted(available.keys())[0]]
        else:
            print("Error: No lexicon databases found in ~/biblemate/data/lexicons or ~/biblemate/data_custom/lexicons.")
            sys.exit(1)
            
    entry_expr = " ".join(tokens[ref_start_idx:])
    return versions, entry_expr

def parse_entries(entry_str):
    clean_str = entry_str.replace(';', ' ').replace(',', ' ')
    tokens = clean_str.strip().split()
    
    parsed_topics = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if '-' in token:
            parts = token.split('-')
            if len(parts) == 2:
                start_part, end_part = parts[0].strip(), parts[1].strip()
                m_start = re.match(r'^([A-Za-z]+)(\d+)$', start_part)
                m_end = re.match(r'^([A-Za-z]+)(\d+)$', end_part)
                if m_start and m_end and m_start.group(1).upper() == m_end.group(1).upper():
                    prefix = m_start.group(1)
                    num_start = int(m_start.group(2))
                    num_end = int(m_end.group(2))
                    num_len = len(m_start.group(2))
                    step = 1 if num_start <= num_end else -1
                    for n in range(num_start, num_end + step, step):
                        parsed_topics.append(f"{prefix}{n:0{num_len}d}")
                    continue
        parsed_topics.append(token)
    return parsed_topics

def get_lexicon_definition(db_path, topic):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT Definition FROM Lexicon WHERE UPPER(Topic) = UPPER(?)", (topic,))
        row = cursor.fetchone()
        conn.close()
        if row:
            clean_def = re.sub(r'<[^>]+>', '', row[0]).strip()
            return clean_def
        else:
            return None
    except Exception as e:
        return f"Error reading definition: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lexicon_retriever.py [versions] [entries]")
        print("Example: python3 lexicon_retriever.py BDB SECE H148")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:])
    available = get_available_lexicons()
    versions, entry_expr = parse_query(query_str)
    
    if not entry_expr:
        print("Error: No lexicon entries specified.")
        sys.exit(1)
        
    topics = parse_entries(entry_expr)
    
    if not topics:
        print("Error: No valid lexicon entries found after parsing.")
        sys.exit(1)
        
    # Print results grouped by entry/topic
    first_printed = False
    for topic in topics:
        if first_printed:
            print("\n---\n")
        first_printed = True
        
        print(f"## Topic: {topic}\n")
        for ver in versions:
            db_path = available[ver]
            definition = get_lexicon_definition(db_path, topic)
            print(f"### [{ver}]")
            if definition:
                print(definition)
            else:
                print("*Entry not found in this lexicon.*")
            print()

if __name__ == "__main__":
    main()
