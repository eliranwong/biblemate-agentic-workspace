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

def find_best_person_id(cursor, code, name):
    try:
        code_num = int(code[2:])
    except ValueError:
        return None

    # First check if code_num has the matching name in PEOPLE
    cursor.execute("SELECT distinct Name FROM PEOPLE WHERE PersonID = ?", (code_num,))
    row = cursor.fetchone()
    if row and name.lower() in row[0].lower():
        return code_num

    # Otherwise, search PEOPLE for all PersonIDs with the matching name
    names_to_try = [name]
    if '/' in name:
        names_to_try.extend([n.strip() for n in name.split('/')])
    
    candidates = set()
    for n in names_to_try:
        cursor.execute("SELECT distinct PersonID FROM PEOPLE WHERE Name LIKE ?", (f"%{n}%",))
        for r in cursor.fetchall():
            candidates.add(r[0])
            
    if not candidates:
        return code_num
        
    best_id = min(candidates, key=lambda x: abs(x - code_num))
    return best_id

def get_relationship_tree(people_db_path, code, name):
    if not code.startswith('BP'):
        return ""
    if not os.path.exists(people_db_path):
        return ""
        
    try:
        conn = sqlite3.connect(people_db_path)
        c = conn.cursor()
        
        person_id = find_best_person_id(c, code, name)
        if not person_id:
            conn.close()
            return ""
            
        c.execute("SELECT distinct Name, Sex FROM PEOPLE WHERE PersonID = ?", (person_id,))
        p_row = c.fetchone()
        if not p_row:
            conn.close()
            return ""
        main_name, main_sex = p_row
        
        def get_person_info(pid):
            c.execute("SELECT distinct Name, Sex FROM PEOPLE WHERE PersonID = ?", (pid,))
            r = c.fetchone()
            if r:
                return r[0], r[1]
            return None, None
            
        def get_direct_relations(pid):
            c.execute("SELECT RelatedPersonID, Relationship FROM PEOPLERELATIONSHIP WHERE PersonID = ? AND Relationship != '[Reference]'", (pid,))
            relations = []
            for r_id, rel_label in c.fetchall():
                r_name, r_sex = get_person_info(r_id)
                if not r_name:
                    continue
                
                c.execute("SELECT Relationship FROM PEOPLERELATIONSHIP WHERE PersonID = ? AND RelatedPersonID = ?", (r_id, pid))
                rev_row = c.fetchone()
                if rev_row and rev_row[0] != '[Reference]':
                    label = rev_row[0]
                else:
                    label = get_fallback_label(r_sex, rel_label)
                
                relations.append({
                    'id': r_id,
                    'name': r_name,
                    'sex': r_sex,
                    'label': label
                })
            return relations
            
        def get_fallback_label(sex, rel):
            rel = rel.lower()
            if 'father' in rel or 'mother' in rel:
                return 'Son' if sex == 'M' else 'Daughter'
            if 'son' in rel or 'daughter' in rel:
                return 'Father' if sex == 'M' else 'Mother'
            if 'husband' in rel:
                return 'Wife'
            if 'wife' in rel or 'concubine' in rel:
                return 'Husband'
            if 'brother' in rel or 'sister' in rel:
                return 'Brother' if sex == 'M' else 'Sister'
            return rel.capitalize()
            
        rel1 = get_direct_relations(person_id)
        if not rel1:
            conn.close()
            return ""
            
        categories = {
            'Parents': [],
            'Spouse': [],
            'Siblings': [],
            'Children': [],
            'Others': []
        }
        
        for r in rel1:
            lbl = r['label'].lower()
            if 'father' in lbl or 'mother' in lbl:
                categories['Parents'].append(r)
            elif 'wife' in lbl or 'husband' in lbl or 'spouse' in lbl or 'concubine' in lbl:
                categories['Spouse'].append(r)
            elif 'brother' in lbl or 'sister' in lbl:
                categories['Siblings'].append(r)
            elif 'son' in lbl or 'daughter' in lbl or 'child' in lbl:
                categories['Children'].append(r)
            else:
                categories['Others'].append(r)
                
        lines = []
        lines.append(f"\n### Family & Relationship Tree\n")
        lines.append("```")
        lines.append(f"{main_name} ({main_sex}, Code: `BP{person_id}`)")
        
        visited = {person_id}
        
        non_empty_cats = [(k, v) for k, v in categories.items() if v]
        for idx, (cat_name, members) in enumerate(non_empty_cats):
            is_last_cat = (idx == len(non_empty_cats) - 1)
            cat_prefix = "└── " if is_last_cat else "├── "
            lines.append(f"{cat_prefix}{cat_name}")
            
            child_indent = "    " if is_last_cat else "│   "
            for m_idx, m in enumerate(members):
                is_last_member = (m_idx == len(members) - 1)
                member_prefix = "└── " if is_last_member else "├── "
                lines.append(f"{child_indent}{member_prefix}{m['label']}: {m['name']} ({m['sex']}, Code: `BP{m['id']}`)")
                visited.add(m['id'])
                
                rel2 = get_direct_relations(m['id'])
                rel2 = [r2 for r2 in rel2 if r2['id'] not in visited]
                if rel2:
                    sub_indent = child_indent + ("    " if is_last_member else "│   ")
                    for r2_idx, r2 in enumerate(rel2):
                        is_last_r2 = (r2_idx == len(rel2) - 1)
                        r2_prefix = "└── " if is_last_r2 else "├── "
                        lines.append(f"{sub_indent}{r2_prefix}{r2['label']}: {r2['name']} ({r2['sex']}, Code: `BP{r2['id']}`)")
                        visited.add(r2['id'])
                        
        lines.append("```")
        conn.close()
        return "\n".join(lines) + "\n"
        
    except Exception as e:
        print(f"Warning building relationship tree: {e}", file=sys.stderr)
        return ""

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
            
            db_dir = os.path.dirname(db_path)
            people_db_path = os.path.join(db_dir, 'biblePeople.data')
            tree_md = get_relationship_tree(people_db_path, code, best_match)
            if tree_md:
                md.append(tree_md)
            
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
