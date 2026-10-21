#!/usr/bin/env python3
import os
import sys
import re

# Stop words to exclude from keyword splitting
STOP_WORDS = {
    'when', 'was', 'were', 'the', 'in', 'of', 'to', 'a', 'an', 'is', 'are', 
    'on', 'at', 'for', 'who', 'what', 'where', 'how', 'did', 'does', 'do', 
    'which', 'about', 'around', 'during', 'and', 'with', 'or', 'by', 'from',
    'meaning', 'meanings', 'mean', 'means', 'name', 'names', 'bible'
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

def get_all_database_names(filepath):
    words = set()
    if not os.path.exists(filepath):
        return words
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if ' - ' in line:
                    name_part = line.split(' - ')[0].strip().lower()
                    # Find all alphanumeric words of length >= 2 in the name part
                    found = re.findall(r'\b[a-z]{2,}\b', name_part)
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

def search_names_file(filepath, groups):
    file_matches = []
    if not os.path.exists(filepath):
        print(f"Error: Database file '{filepath}' not found.", file=sys.stderr)
        return file_matches
        
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
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        
    return file_matches

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 names_query.py <query>")
        print("Example: python3 names_query.py \"Abigail\"")
        sys.exit(1)
        
    query_str = " ".join(sys.argv[1:])
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, 'data', 'Bible Names.txt')
    
    # Extract words in query, excluding stop words
    words_in_query = [w for w in re.findall(r'\b\w+\b', query_str.lower()) if w not in STOP_WORDS]
    
    if not words_in_query:
        print("No search keywords provided.")
        sys.exit(0)
        
    # Get all names vocabulary from file to perform fuzzy matching
    data_names = get_all_database_names(filepath)
    
    # Build search groups (original keyword + fuzzy spelling aliases)
    groups = []
    for w in words_in_query:
        group = {w}
        
        # Add fuzzy spelling aliases
        fuzzy_aliases = get_fuzzy_aliases(w, data_names)
        group.update(fuzzy_aliases)
        
        groups.append(group)
        
    matches = search_names_file(filepath, groups)
    
    if not matches:
        print("No direct matching records found in the local Bible Names data file.")
        sys.exit(0)
        
    print("### Direct Matches from Bible Names:")
    for line in matches:
        print(f"- {line}")

if __name__ == "__main__":
    main()
