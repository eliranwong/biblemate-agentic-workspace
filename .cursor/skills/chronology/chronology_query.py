#!/usr/bin/env python3
import os
import sys
import re

# Stop words to exclude from keyword splitting
STOP_WORDS = {
    'when', 'was', 'were', 'the', 'in', 'of', 'to', 'a', 'an', 'is', 'are', 
    'on', 'at', 'for', 'who', 'what', 'where', 'how', 'did', 'does', 'do', 
    'which', 'about', 'around', 'during', 'and', 'with', 'or', 'by', 'from'
}

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

def is_fuzzy_match(w1, w2):
    if abs(len(w1) - len(w2)) > 2:
        return False
    dist = levenshtein_distance(w1, w2)
    if len(w1) <= 4:
        return dist <= 1
    else:
        return dist <= 2

def get_all_database_words(data_dir):
    words = set()
    if not os.path.exists(data_dir):
        return words
    for filename in os.listdir(data_dir):
        if not filename.endswith('.txt'):
            continue
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                # Find all alphanumeric words of length >= 2
                found = re.findall(r'\b[a-z]{2,}\b', content)
                words.update(found)
        except Exception:
            pass
    return words

def get_fuzzy_aliases(keyword, data_words):
    if keyword.isdigit():
        return []
    aliases = []
    for dw in data_words:
        if is_fuzzy_match(keyword, dw):
            aliases.append(dw)
    return aliases

def search_chronology_files(data_dir, groups):
    results = {}
    if not os.path.exists(data_dir):
        print(f"Error: Data directory '{data_dir}' not found.", file=sys.stderr)
        return results
        
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith('.txt'):
            continue
        filepath = os.path.join(data_dir, filename)
        file_matches = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line_lower = line.lower()
                    
                    # A line matches if it contains at least one word from each group
                    matched_all_groups = True
                    for g in groups:
                        if not any(item in line_lower for item in g):
                            matched_all_groups = False
                            break
                            
                    if matched_all_groups:
                        file_matches.append(line.strip())
        except Exception as e:
            print(f"Error reading file {filename}: {e}", file=sys.stderr)
            
        if file_matches:
            clean_name = os.path.splitext(filename)[0]
            results[clean_name] = file_matches
            
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 chronology_query.py <query>")
        print("Example: python3 chronology_query.py \"Abram born\"")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:])
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    
    # Extract words in query, excluding stop words
    words_in_query = [w for w in re.findall(r'\b\w+\b', query_str.lower()) if w not in STOP_WORDS]
    
    if not words_in_query:
        print("No search keywords provided.")
        sys.exit(0)
        
    # Get vocabulary from all data files to allow fuzzy matching
    data_words = get_all_database_words(data_dir)
    
    # Build search groups (original keyword + explicit aliases + fuzzy spelling aliases)
    groups = []
    for w in words_in_query:
        group = {w}
        
        # 1. Add explicit synonyms
        if w == 'abraham' or w == 'abram':
            group.update({'abraham', 'abram'})
        elif w == 'paul' or w == 'saul':
            group.update({'paul', 'saul'})
        elif w == 'bc' or w == 'bce':
            group.update({'bc', 'bce'})
            
        # 2. Add fuzzy spelling aliases from database vocabulary
        fuzzy_aliases = get_fuzzy_aliases(w, data_words)
        group.update(fuzzy_aliases)
        
        groups.append(group)
        
    results = search_chronology_files(data_dir, groups)
    
    if not results:
        print("No direct matching records found in the local chronology data files.")
        sys.exit(0)
        
    for category, lines in results.items():
        print(f"### Direct Matches from {category}:")
        for line in lines:
            print(f"- {line}")
        print()

if __name__ == "__main__":
    main()
