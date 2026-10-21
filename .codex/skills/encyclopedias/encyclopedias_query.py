#!/usr/bin/env python3
import os
import sys
import re
import sqlite3
import datetime

# Load encyclopedia_dict.py dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
dict_file = os.path.join(SCRIPT_DIR, 'data', 'encyclopedia_dict.py')
ENCYCLOPEDIA = {}

try:
    with open(dict_file, 'r', encoding='utf-8') as f:
        file_content = f.read()
    local_vars = {}
    exec(file_content, {}, local_vars)
    ENCYCLOPEDIA = local_vars.get('ENCYCLOPEDIA', {})
except Exception as e:
    print(f"Error loading encyclopedia database dictionary: {e}", file=sys.stderr)
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

def clean_key(key):
    # Decode html entities
    k = key.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&').replace('&quot;', '"')
    k = re.sub(r'<br\s*/?>', ' ', k, flags=re.IGNORECASE)
    return k.strip()

def is_word_boundary_match(key_str, query_str):
    try:
        pattern = r'\b' + re.escape(key_str) + r'\b'
        return bool(re.search(pattern, query_str))
    except Exception:
        return key_str in query_str

def get_matches(query, dict_keys):
    query_clean = query.strip().lower()
    
    # 1. Exact match (case-insensitive) of key
    exact_matches = []
    for key in dict_keys:
        cleaned = clean_key(key).lower()
        if cleaned == query_clean:
            exact_matches.append(key)
    if exact_matches:
        return exact_matches[:10]
        
    # 2. Check if query is an exact part of a slash or hyphen separated name
    part_matches = []
    for key in dict_keys:
        cleaned = clean_key(key).lower()
        parts = [p.strip() for p in re.split(r'[\-/]', cleaned) if p.strip()]
        if query_clean in parts:
            part_matches.append(key)
    if part_matches:
        return part_matches[:10]
        
    # 3. Check for substring/partial matches
    partials = []
    for key in dict_keys:
        cleaned = clean_key(key).lower()
        parts = [p.strip() for p in re.split(r'[\-/]', cleaned) if p.strip()]
        
        # Forward containment (query is inside key/parts)
        if query_clean in cleaned or any(query_clean in part for part in parts):
            partials.append(key)
        # Reverse containment (key/parts is inside query as whole word/phrase)
        elif is_word_boundary_match(cleaned, query_clean) and len(cleaned) >= 4:
            partials.append(key)
        else:
            for part in parts:
                if len(part) >= 4 and is_word_boundary_match(part, query_clean):
                    partials.append(key)
                    break
                
    if partials:
        # Sort partials to put best ones first (sorting by length of clean key)
        partials.sort(key=lambda k: len(clean_key(k)))
        # Remove duplicates while keeping order
        seen = set()
        unique_partials = []
        for p in partials:
            if p not in seen:
                seen.add(p)
                unique_partials.append(p)
        return unique_partials[:10]
        
    # 4. Word-based flexible search for multi-word queries
    q_words = [w for w in re.split(r'[\s\-/]', query_clean) if w]
    stop_words = {"the", "a", "an", "of", "and"}
    q_words_filtered = [w for w in q_words if w not in stop_words]
    
    if len(q_words_filtered) >= 2:
        scored_matches = []
        for key in dict_keys:
            cleaned = clean_key(key).lower()
            k_words = [w for w in re.split(r'[\s\-/]', cleaned) if w]
            k_words_filtered = [w for w in k_words if w not in stop_words]
            
            matched_count = 0
            for qw in q_words_filtered:
                for kw in k_words_filtered:
                    dist = levenshtein_distance(qw, kw)
                    limit = 1 if len(qw) <= 5 else 2
                    if dist <= limit:
                        matched_count += 1
                        break
            if matched_count >= len(q_words_filtered) - 1:
                penalty = len(cleaned)
                scored_matches.append((key, matched_count, penalty))
                
        if scored_matches:
            scored_matches.sort(key=lambda x: (-x[1], x[2]))
            return [x[0] for x in scored_matches[:10]]
            
    # 5. Fuzzy match using Levenshtein distance
    fuzzy_matches = []
    for key in dict_keys:
        cleaned = clean_key(key).lower()
        parts = [p.strip() for p in re.split(r'[\-/]', cleaned) if p.strip()]
        best_dist = 9999
        for target in [cleaned] + parts:
            if not target:
                continue
            dist = levenshtein_distance(query_clean, target)
            if dist < best_dist:
                best_dist = dist
                
        # Determine threshold for this match
        threshold = 2
        if len(query_clean) <= 4:
            threshold = 1
        elif len(query_clean) > 8:
            threshold = 3
            
        if best_dist <= threshold:
            fuzzy_matches.append((key, best_dist))
            
    if fuzzy_matches:
        # Sort by distance
        fuzzy_matches.sort(key=lambda x: x[1])
        return [x[0] for x in fuzzy_matches[:10]]
        
    return []

def find_db_path():
    # 1. Check user home
    home = os.path.expanduser('~')
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    p = os.path.join(base, 'data', 'data', 'encyclopedia.data')
    if os.path.exists(p):
        return p
    # 2. Check workspace relative
    repo_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    p2 = os.path.join(repo_root, 'biblemate', 'data', 'data', 'encyclopedia.data')
    if os.path.exists(p2):
        return p2
    return None

def get_table_name(path):
    if path.startswith("ISBE"):
        return "ISB"
    return path[:3]

def html_to_markdown(html):
    if not html:
        return ""
    
    # Strip script, style, hide tags completely
    html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<hide\b[^<]*(?:(?!<\/hide>)<[^<]*)*<\/hide>', '', html, flags=re.IGNORECASE)
    
    # Convert header tags to md headers
    html = re.sub(r'<h[1-6]\b[^>]*>(.*?)</h[1-6]>', r'\n\n## \1\n\n', html, flags=re.IGNORECASE)
    
    # Convert paragraph, line break, and block element tags
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</?p\b[^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</?div\b[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Convert formatting
    html = re.sub(r'</?(?:b|strong)>', '**', html)
    html = re.sub(r'</?(?:i|em)>', '*', html)
    
    # Convert lists
    html = re.sub(r'<li\b[^>]*>', '\n- ', html, flags=re.IGNORECASE)
    html = re.sub(r'</li>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</?ul\b[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</?ol\b[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Clean references like <ref onclick="searchEntry('AMT', 'Zion')">Zion</ref> to just the text
    html = re.sub(r'<ref\s+onclick="[^"]+">(.*?)</ref>', r'\1', html, flags=re.IGNORECASE)
    html = re.sub(r"<ref\s+onclick='[^']+']'>(.*?)</ref>", r'\1', html, flags=re.IGNORECASE)
    html = re.sub(r'<ref[^>]*>(.*?)</ref>', r'\1', html, flags=re.IGNORECASE)
    
    # Clean up standard anchor tags
    html = re.sub(r'<a\s+href="[^"]+">(.*?)</a>', r'\1', html, flags=re.IGNORECASE)
    
    # Horizontal rules
    html = re.sub(r'<hr\s*/?>', '\n\n---\n\n', html, flags=re.IGNORECASE)
    
    # Strip any other remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Normalize spacing
    lines = [line.strip() for line in html.split('\n')]
    cleaned_lines = []
    for line in lines:
        if line:
            cleaned_lines.append(line)
        elif not cleaned_lines or cleaned_lines[-1] != "":
            cleaned_lines.append("")
            
    return "\n".join(cleaned_lines).strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 encyclopedias_query.py <encyclopedia_entry>", file=sys.stderr)
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    matches = get_matches(query, ENCYCLOPEDIA.keys())
    
    if not matches:
        print(f"Error: Could not locate any matching encyclopedia entries for '{query}'.", file=sys.stderr)
        sys.exit(1)
        
    db_path = find_db_path()
    if not db_path:
        print("Error: encyclopedia.data database file not found.", file=sys.stderr)
        sys.exit(1)
        
    md = []
    if len(matches) == 1:
        md.append(f"# Encyclopedia Entry: {clean_key(matches[0])}")
    else:
        md.append(f"# Encyclopedia Search Results for '{query}' (Found {len(matches)} matches)")
        
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        for m_idx, match in enumerate(matches):
            paths = ENCYCLOPEDIA[match]
            if len(matches) > 1:
                md.append(f"\n# Entry: {clean_key(match)}")
                
            for p_idx, path in enumerate(paths):
                table_name = get_table_name(path)
                c.execute(f"SELECT content FROM \"{table_name}\" WHERE path = ?", (path,))
                row = c.fetchone()
                
                if not row or not row[0]:
                    content_md = f"*(No database record content found in table `{table_name}` for path `{path}`)*"
                else:
                    content_md = html_to_markdown(row[0])
                    
                if len(paths) > 1:
                    md.append(f"\n## Definition {p_idx+1} (Source Code: `{path}`)\n")
                elif len(matches) > 1:
                    md.append("")
                else:
                    md.append("")
                md.append(content_md)
                
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)
        
    md_content = "\n".join(md).strip() + "\n"
    
    # Save study output to biblemate/ in workspace under the Universal Study Output Saving Rule
    workspace_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    biblemate_dir = os.path.join(workspace_root, 'biblemate')
    os.makedirs(biblemate_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # Clean the query or first match name for filename
    base_name = query if len(matches) > 1 else matches[0]
    decoded_name = clean_key(base_name)
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', decoded_name.replace(' ', '_')).lower()
    clean_name = re.sub(r'_{2,}', '_', clean_name).strip('_')
    filename = f"{timestamp}_encyclopedia_{clean_name}.md"
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
