#!/usr/bin/env python3
import os
import sys
import re
import sqlite3
import datetime

# Load self-contained bible_locations.py dynamically via direct file reading
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
locations_file = os.path.join(SCRIPT_DIR, 'data', 'bible_locations.py')
allLocations = {}

try:
    with open(locations_file, 'r', encoding='utf-8') as f:
        file_content = f.read()
    local_vars = {}
    exec(file_content, {}, local_vars)
    allLocations = local_vars.get('allLocations', {})
except Exception as e:
    print(f"Error loading location database content: {e}", file=sys.stderr)
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

def get_best_match(query, locations_dict):
    query_clean = query.strip().lower()
    
    # 1. Check exact match (case-insensitive)
    for loc_name in locations_dict:
        if loc_name.lower() == query_clean:
            return loc_name
            
    # 2. Check for substring/partial match
    partials = []
    for loc_name in locations_dict:
        loc_lower = loc_name.lower()
        if query_clean in loc_lower:
            partials.append(loc_name)
        elif loc_lower in query_clean:
            query_words = re.split(r'[\s\-/]', query_clean)
            if loc_lower in query_words or len(loc_lower) >= 4:
                partials.append(loc_name)
    if len(partials) == 1:
        return partials[0]
        
    # 3. Fuzzy match using Levenshtein distance
    best_name = None
    min_distance = 9999
    
    for loc_name in locations_dict:
        # Split names by slashes/hyphens for sub-parts matching (e.g. Abel-Beth-Maachah)
        parts = re.split(r'[-/]', loc_name.lower())
        for part in [loc_name.lower()] + parts:
            if not part:
                continue
            dist = levenshtein_distance(query_clean, part)
            if dist < min_distance:
                min_distance = dist
                best_name = loc_name
                
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

def html_to_markdown(html, name, code, lat, lon):
    # Extract map link
    map_link = ""
    map_match = re.search(r"website\('([^']+)'\)", html)
    if map_match:
        map_url = map_match.group(1)
        map_link = f"[Click HERE for a Live Google Map]({map_url})"
    else:
        # Construct fallback link using coordinates
        map_link = f"[Click HERE for a Live Google Map](https://maps.google.com/?q={lat},{lon}&z=10)"

    # Strip script tags completely
    html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
    # Strip map divs completely
    html = re.sub(r'<div\s+id="map"\b[^>]*>.*?</div>', '', html, flags=re.DOTALL)
    # Strip style tags completely
    html = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html, flags=re.IGNORECASE)
    # Strip small/large map image refs
    html = re.sub(r'<ref onclick="openHtmlImage\([^)]+\)">.*?</ref>', '', html)
    
    # Process formatting tags
    html = re.sub(r'</?(?:b|strong)>', '**', html)
    html = re.sub(r'</?(?:i|em)>', '*', html)
    
    # Extract dictionary table description
    desc_text = ""
    table_match = re.search(r'<table[^>]*>.*?<td[^>]*>(.*?)</td>.*?</table>', html, re.DOTALL)
    if table_match:
        desc_text = table_match.group(1)
    else:
        # Fallback: clean all tags after title
        desc_text = html
        
    # Clean description HTML tags
    desc_text = re.sub(r'<p\b[^>]*>', '\n\n', desc_text)
    desc_text = re.sub(r'<br\s*/?>', '\n', desc_text)
    desc_text = re.sub(r'<[^>]+>', '', desc_text)
    desc_text = desc_text.strip()
    
    # Extract occurrences
    occ_text = ""
    occ_match = re.search(r'<div class="occ">(.*?)</div>', html, re.DOTALL)
    if occ_match:
        occ_content = occ_match.group(1)
        occ_content = re.sub(r'<ref[^>]*>(.*?)</ref>', r'\1', occ_content)
        occ_content = re.sub(r'<br\s*/?>', '\n', occ_content)
        occ_content = re.sub(r'<p\b[^>]*>', '\n\n', occ_content)
        occ_content = re.sub(r'<[^>]+>', '', occ_content)
        lines = [line.strip() for line in occ_content.split('\n') if line.strip()]
        if lines:
            occ_text = "\n".join(f"- {line}" for line in lines)

    # Format the complete markdown output
    md = []
    md.append(f"# Location Study: {name}")
    md.append(f"\n**Entry Code**: `{code}`")
    md.append(f"**Coordinates**: Latitude `{lat}`, Longitude `{lon}`")
    if map_link:
        md.append(f"**Map**: {map_link}")
    
    if desc_text:
        md.append("\n## Etymology & Historical Description\n")
        md.append(desc_text)
        
    if occ_text:
        md.append("\n## Scriptural Occurrences\n")
        md.append(occ_text)
        
    return "\n".join(md)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 locations_query.py <location_name>")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    best_match = get_best_match(query, allLocations)
    
    if not best_match:
        print(f"Error: Could not locate a matching Bible location for '{query}'.", file=sys.stderr)
        sys.exit(1)
        
    code, lat, lon = allLocations[best_match]
    
    db_path = find_db_path()
    if not db_path:
        print("Error: exlb3.data database file not found.", file=sys.stderr)
        sys.exit(1)
        
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT content FROM exlbl WHERE path = ?", (code,))
        row = c.fetchone()
        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)
        
    if not row or not row[0]:
        # Fallback if entry has no HTML content: construct basic info page
        md_content = f"# Location Study: {best_match}\n\n**Entry Code**: `{code}`\n**Coordinates**: Latitude `{lat}`, Longitude `{lon}`\n**Map**: [Click HERE for a Live Google Map](https://maps.google.com/?q={lat},{lon}&z=10)"
    else:
        md_content = html_to_markdown(row[0], best_match, code, lat, lon)
        
    # Save complete study output to biblemate/ in accordance with saving rule
    workspace_root = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
    biblemate_dir = os.path.join(workspace_root, 'biblemate')
    os.makedirs(biblemate_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', best_match.replace(' ', '_')).lower()
    filename = f"{timestamp}_location_{clean_name}.md"
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
