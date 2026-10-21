#!/usr/bin/env python3
import os
import sys
import glob

def get_resources(resource_type):
    home = os.path.expanduser('~')
    base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')
    
    if resource_type == 'bible':
        subpath = 'bibles'
        pattern = '*.bible'
    elif resource_type == 'commentary':
        subpath = 'commentaries'
        pattern = 'c*.commentary'
    elif resource_type == 'lexicon':
        subpath = 'lexicons'
        pattern = '*.lexicon'
    else:
        return None, None
        
    std_dir = os.path.join(base, 'data', subpath)
    cust_dir = os.path.join(base, 'data_custom', subpath)
    
    std_list = []
    if os.path.exists(std_dir):
        for filepath in glob.glob(os.path.join(std_dir, pattern)):
            filename = os.path.basename(filepath)
            if resource_type == 'bible':
                ver = os.path.splitext(filename)[0].upper()
            elif resource_type == 'commentary':
                ver = filename[1:-11].upper() # strip 'c' prefix and '.commentary' suffix
            elif resource_type == 'lexicon':
                ver = os.path.splitext(filename)[0].upper()
            std_list.append(ver)
            
    cust_list = []
    if os.path.exists(cust_dir):
        for filepath in glob.glob(os.path.join(cust_dir, pattern)):
            filename = os.path.basename(filepath)
            if resource_type == 'bible':
                ver = os.path.splitext(filename)[0].upper()
            elif resource_type == 'commentary':
                ver = filename[1:-11].upper()
            elif resource_type == 'lexicon':
                ver = os.path.splitext(filename)[0].upper()
            cust_list.append(ver)
            
    return sorted(list(set(std_list))), sorted(list(set(cust_list)))

def main():
    if len(sys.argv) < 2:
        print("Error: Please specify resource type.")
        print("Usage: python3 data_lister.py [bible|commentary|lexicon] ...")
        sys.exit(1)
        
    # Gather all tokens from all command line arguments
    raw_args = []
    for arg in sys.argv[1:]:
        raw_args.extend(arg.lower().strip().split())
        
    # Filter out duplicates while preserving order
    res_types = []
    for r in raw_args:
        r = r.strip()
        if r in ('bible', 'commentary', 'lexicon') and r not in res_types:
            res_types.append(r)
            
    if not res_types:
        print(f"Error: No valid resource types specified in: {sys.argv[1:]}")
        print("Usage: python3 data_lister.py [bible|commentary|lexicon] ...")
        sys.exit(1)
        
    first = True
    for res_type in res_types:
        if not first:
            print("\n---\n")
        first = False
        
        std_res, cust_res = get_resources(res_type)
        
        title_map = {
            'bible': 'Bible Versions',
            'commentary': 'Commentary Versions',
            'lexicon': 'Lexicon Versions'
        }
        
        folder_map = {
            'bible': 'bibles',
            'commentary': 'commentaries',
            'lexicon': 'lexicons'
        }
        
        display_title = title_map[res_type]
        folder_name = folder_map[res_type]
        
        print(f"## Available {display_title}\n")
        
        print(f"### Standard {display_title} (stored in `~/biblemate/data/{folder_name}`)")
        if std_res:
            for r in std_res:
                print(f"- **{r}**")
        else:
            print("*No standard versions found.*")
        print()
        
        print(f"### Custom {display_title} (stored in `~/biblemate/data_custom/{folder_name}`)")
        if cust_res:
            for r in cust_res:
                print(f"- **{r}**")
        else:
            print("*No custom versions found.*")

if __name__ == '__main__':
    main()
