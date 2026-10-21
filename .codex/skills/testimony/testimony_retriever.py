#!/usr/bin/env python3
import os
import sys
import json
import re
import datetime

# Stop words to exclude from keyword splitting
STOP_WORDS = {
    'when', 'was', 'were', 'the', 'in', 'of', 'to', 'a', 'an', 'is', 'are', 
    'on', 'at', 'for', 'who', 'what', 'where', 'how', 'did', 'does', 'do', 
    'which', 'about', 'around', 'during', 'and', 'with', 'or', 'by', 'from',
    'testimony', 'testimonies', 'story', 'stories', 'real', 'missionary', 'history'
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

def load_testimonies(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Testimony database '{filepath}' not found.", file=sys.stderr)
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading testimonies: {e}", file=sys.stderr)
        return []

def search_testimonies(testimonies, query_str):
    # Extract query terms
    terms = [w for w in re.findall(r'\b\w+\b', query_str.lower()) if w not in STOP_WORDS]
    if not terms:
        return []
    
    matches_with_score = []
    
    for t in testimonies:
        score = 0
        searchable_text = " ".join([
            t['title'], t['person'], t['summary'], t['narrative'], t['background'],
            " ".join(t['themes']), t['bible_verses']
        ]).lower()
        
        # Check exact and fuzzy matches for each term
        for term in terms:
            if term in searchable_text:
                score += 10  # High score for exact substring match
            else:
                # Check fuzzy match against individual words in the searchable text
                words_in_text = re.findall(r'\b[a-z]{3,}\b', searchable_text)
                fuzzy_matched = False
                for w in words_in_text:
                    if is_fuzzy_match(term, w):
                        score += 3
                        fuzzy_matched = True
                        break
        
        if score > 0:
            matches_with_score.append((t, score))
            
    # Sort by score descending
    matches_with_score.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches_with_score]

def format_testimony_markdown(t):
    md = []
    md.append(f"# Real Testimony: {t['title']}")
    md.append(f"\n**Key Person(s)**: {t['person']}")
    md.append(f"**Era**: {t['era']}")
    md.append(f"**Location**: {t['location']}")
    md.append(f"**Key Themes**: {', '.join(t['themes'])}")
    
    md.append("\n## The Testimony Story\n")
    md.append(t['narrative'])
    
    md.append("\n## Historical Context & Biography\n")
    md.append(t['background'])
    
    md.append("\n## Theological & Biblical Themes\n")
    md.append(f"This testimony demonstrates the principles found in these passages:")
    md.append(f"- **Scriptural Connection**: {t['bible_verses']}")
    md.append("\n> [!NOTE]\n> *Please use the local bible skill (`/bible`) to retrieve and quote the exact scripture text in the final report to ensure accuracy.*")
    
    md.append("\n## Verification & Sources (Fact-Checking)\n")
    md.append("You can verify the historical details of this testimony through these sources:")
    for source in t['sources']:
        md.append(f"- **{source['title']}** by {source['author']}")
        md.append(f"  - Resource Link: [{source['url']}]({source['url']})")
        md.append(f"  - Verification Notes: {source['verification_notes']}")
        
    return "\n".join(md)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'data', 'testimonies.json')
    testimonies = load_testimonies(db_path)
    
    if len(sys.argv) < 2:
        print("### Available Historical Testimonies in Local Database:")
        for t in testimonies:
            print(f"- **{t['person']}**: {t['title']} (Themes: {', '.join(t['themes'])})")
        print("\nUsage: python3 testimony_retriever.py <search_query>")
        sys.exit(0)
        
    query_str = " ".join(sys.argv[1:])
    matches = search_testimonies(testimonies, query_str)
    
    if not matches:
        print("No direct matching testimony found in the local database.")
        print("Please search online using available web search tools to find real, verified testimonies matching your request. Do not fabricate a testimony.")
        sys.exit(0)
        
    # Get the best match
    best_match = matches[0]
    md_content = format_testimony_markdown(best_match)
    
    # Save complete study output to biblemate/
    workspace_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
    biblemate_dir = os.path.join(workspace_root, 'biblemate')
    os.makedirs(biblemate_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', best_match['person'].replace(' ', '_')).lower()
    filename = f"{timestamp}_testimony_{clean_name}.md"
    file_path = os.path.join(biblemate_dir, filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    except Exception as e:
        print(f"Warning: Failed to save study output to {file_path}: {e}", file=sys.stderr)
        
    # Output to stdout for user/agent reading
    print(md_content)
    print(f"\n---")
    print(f"Study output saved to: biblemate/{filename}")

if __name__ == "__main__":
    main()
