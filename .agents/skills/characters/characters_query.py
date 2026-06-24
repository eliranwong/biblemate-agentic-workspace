#!/usr/bin/env python3
import os
import sys
import re
import sqlite3
import datetime

# Load exlbp_dict.py dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
dict_file = os.path.join(SCRIPT_DIR, 'data', 'exlbp_dict.py')
EXLBP = {}

try:
    with open(dict_file, 'r', encoding='utf-8') as f:
        file_content = f.read()
    local_vars = {}
    exec(file_content, {}, local_vars)
    EXLBP = local_vars.get('EXLBP', {})
except Exception as e:
    print(f"Error loading character database dictionary: {e}", file=sys.stderr)
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

def get_best_match(query, EXLBP_dict):
    query_clean = query.strip().lower()
    
    # 1. Check exact match (case-insensitive) of key
    for name in EXLBP_dict:
        if name.lower() == query_clean:
            return name
            
    # 2. Check if query is an exact part of a slash-separated name
    for name in EXLBP_dict:
        parts = [p.strip().lower() for p in name.split('/')]
        if query_clean in parts:
            return name
            
    # 3. Check for substring/partial matches
    partials = []
    for name in EXLBP_dict:
        name_lower = name.lower()
        parts = [p.strip().lower() for p in name.split('/')]
        if any(query_clean in part for part in parts) or query_clean in name_lower:
            partials.append(name)
        elif any(part in query_clean for part in parts) or name_lower in query_clean:
            if len(name_lower) >= 4:
                partials.append(name)
                
    if len(partials) == 1:
        return partials[0]
    elif len(partials) > 1:
        partials.sort(key=len)
        return partials[0]
        
    # 4. Fuzzy match using Levenshtein distance
    best_name = None
    min_distance = 9999
    
    for name in EXLBP_dict:
        # Split names by slashes/hyphens for sub-parts matching
        parts = re.split(r'[-/]', name.lower())
        for part in [name.lower()] + parts:
            part = part.strip()
            if not part:
                continue
            dist = levenshtein_distance(query_clean, part)
            if dist < min_distance:
                min_distance = dist
                best_name = name
                
    # Thresholds:
    # Length <= 4: max dist 1
    # Length 5-8: max dist 2
    # Length > 8: max dist 3
    threshold = 2
    if len(query_clean) <= 4:
        threshold = 1
    elif len(query_clean) > 8:
        threshold = 3
        
    if min_distance <= threshold:
        return best_name
        
    return None

def find_db_path():
    # 1. Check user home
    home = os.path.expanduser('~')
    p = os.path.join(home, 'biblemate', 'data', 'data', 'exlb3.data')
    if os.path.exists(p):
        return p
    # 2. Check workspace relative
    repo_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    p2 = os.path.join(repo_root, 'biblemate', 'data', 'data', 'exlb3.data')
    if os.path.exists(p2):
        return p2
    return None

def parse_tables(html):
    def replace_table(match):
        table_html = match.group(0)
        # Split by <tr> to be robust against missing/typoed </tr> tags in the DB
        parts = re.split(r'<tr\b[^>]*>', table_html, flags=re.IGNORECASE)
        markdown_rows = []
        for row_data in parts[1:]:
            cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row_data, re.DOTALL | re.IGNORECASE)
            clean_cells = []
            for cell in cells:
                clean_cells.append(cell.strip())
            if not any(clean_cells):
                continue
            markdown_rows.append(clean_cells)
            
        if not markdown_rows:
            return ""
            
        num_cols = max(len(r) for r in markdown_rows)
        
        if num_cols == 1:
            content_parts = []
            for row in markdown_rows:
                for cell in row:
                    content_parts.append(cell)
            return "\n\n" + "\n\n".join(content_parts) + "\n\n"
            
        formatted_rows = []
        for row in markdown_rows:
            formatted_row = []
            for cell in row:
                c = re.sub(r'<[^>]+>', '', cell).strip()
                c = re.sub(r'\s+', ' ', c)
                formatted_row.append(c)
            while len(formatted_row) < num_cols:
                formatted_row.append("")
            formatted_rows.append(formatted_row)
            
        lines = []
        # Header row
        lines.append("| " + " | ".join(formatted_rows[0]) + " |")
        # Divider row
        lines.append("| " + " | ".join(["---"] * num_cols) + " |")
        # Data rows
        for row in formatted_rows[1:]:
            lines.append("| " + " | ".join(row) + " |")
        return "\n\n" + "\n".join(lines) + "\n\n"
        
    return re.sub(r'<table\b[^>]*>(.*?)</table>', replace_table, html, flags=re.DOTALL)

def html_to_markdown(html):
    # Strip script, style, hide tags, and redundant sm tag
    html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<hide\b[^<]*(?:(?!<\/hide>)<[^<]*)*<\/hide>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</?sm[^>]*>', '', html, flags=re.IGNORECASE)
    
    # Strip the header H2 tag with name to avoid duplication
    html = re.sub(r'<h2\b[^>]*>.*?</h2>', '', html, flags=re.IGNORECASE)
    
    # Format Section Headers
    def replace_h(match):
        title = match.group(1).strip()
        if title.lower() == "paternal ancestory":
            title = "Paternal Ancestry"
        elif title.lower() == "occurences in authorized version":
            title = "Occurrences in Authorized Version (KJV)"
        return f"\n\n### {title}\n\n"
    html = re.sub(r'<font color="brown"><b>(.*?)</b></font>', replace_h, html, flags=re.IGNORECASE)
    
    # Parse tables
    html = parse_tables(html)
    
    # Replace references like <ref onclick="bcv(...)">TEXT</ref> with just TEXT
    html = re.sub(r'<ref\s+onclick="[^"]+">(.*?)</ref>', r'\1', html, flags=re.IGNORECASE)
    html = re.sub(r"<ref\s+onclick='[^']+']'>(.*?)</ref>", r'\1', html, flags=re.IGNORECASE)
    html = re.sub(r'<ref[^>]*>(.*?)</ref>', r'\1', html, flags=re.IGNORECASE)
    
    # Process bold and italics formatting
    html = re.sub(r'</?(?:b|strong)>', '**', html)
    html = re.sub(r'</?(?:i|em)>', '*', html)
    
    # Clean up standard block element tags
    html = re.sub(r'</?div\b[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</?p\b[^>]*>', '\n\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</?font\b[^>]*>', '', html, flags=re.IGNORECASE)
    
    # Strip any other leftover tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Clean entities
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    
    # Clean blank lines
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
        print("Usage: python3 characters_query.py <character_name>", file=sys.stderr)
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    best_match = get_best_match(query, EXLBP)
    
    if not best_match:
        print(f"Error: Could not locate a matching Bible character/person for '{query}'.", file=sys.stderr)
        sys.exit(1)
        
    codes = EXLBP[best_match]
    db_path = find_db_path()
    
    if not db_path:
        print("Error: exlb3.data database file not found.", file=sys.stderr)
        sys.exit(1)
        
    md = []
    md.append(f"# Bible Character Study: {best_match}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        for i, code in enumerate(codes):
            c.execute("SELECT content FROM exlbp WHERE path = ?", (code,))
            row = c.fetchone()
            
            if not row or not row[0]:
                entry_md = f"*(No database record content found for `{code}`)*"
            else:
                entry_md = html_to_markdown(row[0])
                
            if len(codes) > 1:
                md.append(f"\n## Individual {i+1} (Code: `{code}`)\n")
            else:
                md.append(f"\n**Entry Code**: `{code}`\n")
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
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', best_match.replace(' ', '_')).lower()
    filename = f"{timestamp}_character_{clean_name}.md"
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
