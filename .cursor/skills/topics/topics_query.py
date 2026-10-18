#!/usr/bin/env python3
import os
import sys
import re
import sqlite3
import datetime

# Load exlbt_dict.py dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
dict_file = os.path.join(SCRIPT_DIR, 'data', 'exlbt_dict.py')
EXLBT = {}

try:
    with open(dict_file, 'r', encoding='utf-8') as f:
        file_content = f.read()
    local_vars = {}
    exec(file_content, {}, local_vars)
    EXLBT = local_vars.get('EXLBT', {})
except Exception as e:
    print(f"Error loading topic database dictionary: {e}", file=sys.stderr)
    sys.exit(1)

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

def decode_key(key):
    return key.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&').replace('&quot;', '"')

def get_best_match(query, EXLBT_dict):
    query_clean = query.strip().lower()
    
    # 1. Exact match (case-insensitive) of decoded key or leaf part
    for raw_key in EXLBT_dict:
        decoded = decode_key(raw_key).lower()
        if decoded == query_clean:
            return raw_key
        # Check leaf part
        parts = [p.strip() for p in decoded.split('>')]
        if parts and parts[-1] == query_clean:
            return raw_key
            
    # 2. Check for substring/partial match in decoded key or leaf part
    partials = []
    for raw_key in EXLBT_dict:
        decoded = decode_key(raw_key).lower()
        parts = [p.strip() for p in decoded.split('>')]
        leaf = parts[-1] if parts else ""
        
        if query_clean in decoded or query_clean in leaf:
            partials.append(raw_key)
        elif decoded in query_clean or (leaf and leaf in query_clean):
            if len(leaf) >= 4 or len(decoded) >= 4:
                partials.append(raw_key)
                
    if len(partials) == 1:
        return partials[0]
    elif len(partials) > 1:
        # Sort by length of decoded key to get the most specific/shortest one
        partials.sort(key=lambda k: len(decode_key(k)))
        return partials[0]
        
    # 3. Fuzzy match using Levenshtein distance on decoded key or leaf part
    best_key = None
    min_distance = 9999
    
    for raw_key in EXLBT_dict:
        decoded = decode_key(raw_key).lower()
        parts = [p.strip() for p in decoded.split('>')]
        leaf = parts[-1] if parts else ""
        
        for target in [decoded, leaf]:
            if not target:
                continue
            dist = levenshtein_distance(query_clean, target)
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
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    p = os.path.join(base, 'data', 'data', 'exlb3.data')
    if os.path.exists(p):
        return p
    # 2. Check workspace relative
    repo_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    p2 = os.path.join(repo_root, 'biblemate', 'data', 'data', 'exlb3.data')
    if os.path.exists(p2):
        return p2
    return None

def html_to_markdown(html):
    # Decode basic entities in HTML
    html = html.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&').replace('&quot;', '"')
    
    # Convert <h2>...</h2> to a nice title
    title_match = re.search(r'<h2\b[^>]*>(.*?)</h2>', html, re.IGNORECASE)
    title = ""
    if title_match:
        title = title_match.group(1).strip()
        # Remove h2 block from HTML to avoid duplicate rendering
        html = re.sub(r'<h2\b[^>]*>.*?</h2>', '', html, flags=re.IGNORECASE)
        
    # Replace list items: <li> to -
    html = re.sub(r'<li\b[^>]*>', '\n- ', html, flags=re.IGNORECASE)
    html = re.sub(r'</li>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</?ul\b[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Strip redundant div tags
    html = re.sub(r'<div\b[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
    
    # Replace references like <ref onclick="bcv(...)">TEXT</ref> with just TEXT
    html = re.sub(r'<ref\s+onclick="[^"]+">(.*?)</ref>', r'\1', html, flags=re.IGNORECASE)
    html = re.sub(r"<ref\s+onclick='[^']+']'>(.*?)</ref>", r'\1', html, flags=re.IGNORECASE)
    html = re.sub(r'<ref[^>]*>(.*?)</ref>', r'\1', html, flags=re.IGNORECASE)
    
    # Bold/italic tags
    html = re.sub(r'</?(?:b|strong)>', '**', html)
    html = re.sub(r'</?(?:i|em)>', '*', html)
    
    # Strip font tags
    html = re.sub(r'</?font\b[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    
    # Strip any other leftover tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Clean blank lines and format lines
    lines = [line.strip() for line in html.split('\n')]
    cleaned_lines = []
    for line in lines:
        if line:
            cleaned_lines.append(line)
        elif not cleaned_lines or cleaned_lines[-1] != "":
            cleaned_lines.append("")
            
    md_body = "\n".join(cleaned_lines).strip()
    
    md = []
    if title:
        md.append(f"# Topic Study: {title}\n")
    md.append(md_body)
    
    return "\n".join(md)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 topics_query.py <topic_name>", file=sys.stderr)
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    best_match = get_best_match(query, EXLBT)
    
    if not best_match:
        print(f"Error: Could not locate a matching Bible topic for '{query}'.", file=sys.stderr)
        sys.exit(1)
        
    codes = EXLBT[best_match]
    db_path = find_db_path()
    
    if not db_path:
        print("Error: exlb3.data database file not found.", file=sys.stderr)
        sys.exit(1)
        
    md = []
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        for i, code in enumerate(codes):
            c.execute("SELECT content FROM exlbt WHERE path = ?", (code,))
            row = c.fetchone()
            
            if not row or not row[0]:
                entry_md = f"*(No database record content found for `{code}`)*"
            else:
                entry_md = html_to_markdown(row[0])
                
            if len(codes) > 1:
                md.append(f"\n## Subtopic {i+1} (Code: `{code}`)\n")
            md.append(entry_md)
            
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)
        
    md_content = "\n".join(md)
    
    # Save study output to biblemate/ in workspace
    workspace_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    biblemate_dir = os.path.join(workspace_root, 'biblemate')
    os.makedirs(biblemate_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # Clean the topic name for filename
    decoded_name = decode_key(best_match)
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', decoded_name.replace(' ', '_')).lower()
    # Strip double underscores
    clean_name = re.sub(r'_{2,}', '_', clean_name).strip('_')
    filename = f"{timestamp}_topic_{clean_name}.md"
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
