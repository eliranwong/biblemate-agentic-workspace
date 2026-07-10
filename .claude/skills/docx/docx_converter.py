import os
import sys
import glob
import json
import re
import subprocess
import datetime

# Get workspace root dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))

def slugify(text):
    # Remove XML/HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    text_clean = text.strip()
    
    # Check if there is any slash command anywhere in the text
    slash_match = re.search(r'/([a-zA-Z0-9_]+)', text_clean)
    if slash_match:
        cmd = slash_match.group(1)
        # Extract everything after the slash command
        rest = text_clean[slash_match.end():]
        rest = re.sub(r'[^a-zA-Z0-9\s-]', '', rest)
        rest_words = rest.split()[:3]
        if rest_words:
            slug = cmd + "_" + "_".join(rest_words)
        else:
            slug = cmd
        return slug.lower()[:35]
        
    # If no slash command, clean and take the first 4 words
    text_cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', text_clean)
    words = text_cleaned.split()[:4]
    if not words:
        return "export"
    slug = "_".join(words)
    return slug.lower()[:35]


def convert_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        sys.exit(1)
        
    dir_name = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Redirect output to export/docx if the source file is located within the export structure
    normalized_dir = os.path.abspath(dir_name)
    normalized_export = os.path.abspath(os.path.join(REPO_ROOT, "export"))
    if normalized_dir == normalized_export or normalized_dir.startswith(normalized_export + os.sep):
        export_docx_dir = os.path.join(REPO_ROOT, "export", "docx")
        os.makedirs(export_docx_dir, exist_ok=True)
        output_file = os.path.join(export_docx_dir, f"{base_name}.docx")
    else:
        output_file = os.path.join(dir_name, f"{base_name}.docx")
        
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.docx':
        print(f"File '{file_path}' is already in Word document format.")
        sys.exit(0)
        
    print(f"Converting '{file_path}' to docx...")
    
    if ext == '.pdf':
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text_parts = []
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"## Page {idx + 1}\n\n{text}")
            
            temp_md = os.path.join(dir_name, f"temp_pdf_{base_name}.md")
            with open(temp_md, "w", encoding="utf-8") as f:
                f.write("\n\n".join(text_parts))
                
            cmd = ["/opt/homebrew/bin/pandoc", "-f", "markdown", "-t", "docx", "-o", output_file, temp_md]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists(temp_md):
                os.remove(temp_md)
                
            if res.returncode == 0:
                print(f"Successfully converted PDF text to Word: {output_file}")
            else:
                print(f"Error converting extracted PDF text to Word: {res.stderr}")
                sys.exit(1)
                
        except ImportError:
            print("Error: The 'pypdf' package is required to convert PDF files. Run 'pip install pypdf'.")
            sys.exit(1)
        except Exception as e:
            print(f"Error converting PDF file to docx: {e}")
            sys.exit(1)
            
    else:
        # Standard pandoc conversion (works for md, html, rst, txt, etc.)
        cmd = ["/opt/homebrew/bin/pandoc", "-t", "docx", "-o", output_file, file_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Successfully converted file to Word: {output_file}")
        else:
            # Try markdown input compile fallback
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                temp_md = os.path.join(dir_name, f"temp_conv_{base_name}.md")
                with open(temp_md, "w", encoding="utf-8") as f:
                    f.write(content)
                    
                cmd = ["/opt/homebrew/bin/pandoc", "-f", "markdown", "-t", "docx", "-o", output_file, temp_md]
                res_fb = subprocess.run(cmd, capture_output=True, text=True)
                
                if os.path.exists(temp_md):
                    os.remove(temp_md)
                    
                if res_fb.returncode == 0:
                    print(f"Successfully converted file to Word via markdown fallback: {output_file}")
                else:
                    print(f"Failed to convert file '{file_path}' to docx: {res_fb.stderr}")
                    sys.exit(1)
            except Exception as e:
                print(f"Failed to convert file '{file_path}' to docx: {e}")
                sys.exit(1)

def export_conversation(is_whole):
    brain_dir = os.path.expanduser("~/.gemini/antigravity-ide/brain")
    transcript_pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    transcripts = glob.glob(transcript_pattern)
    
    if not transcripts:
        print("Error: Could not find any active conversation transcripts.")
        sys.exit(1)
        
    transcripts.sort(key=os.path.getmtime, reverse=True)
    latest_transcript = transcripts[0]
    
    steps = []
    with open(latest_transcript, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    steps.append(json.loads(line))
                except Exception:
                    pass
                    
    turns = []
    current_turn = None
    
    for step in steps:
        step_type = step.get("type")
        source = step.get("source")
        content = step.get("content", "")
        created_at = step.get("created_at", "")
        
        if step_type == "USER_INPUT":
            if current_turn:
                turns.append(current_turn)
            current_turn = {
                "user": content,
                "created_at": created_at,
                "assistant_steps": []
            }
        elif source == "MODEL" and current_turn is not None:
            if step_type == "PLANNER_RESPONSE":
                current_turn["assistant_steps"].append(step)
            
    if current_turn:
        turns.append(current_turn)
        
    for turn in turns:
        final_content = ""
        for s in reversed(turn["assistant_steps"]):
            content = s.get("content", "").strip()
            if content:
                final_content = content
                break
        turn["assistant"] = final_content
        
    export_dir = os.path.join(REPO_ROOT, "export", "docx")
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_md_path = os.path.join(export_dir, f"temp_export_{timestamp}.md")
    
    if is_whole:
        # Filter out current turn if it was the export command itself
        valid_turns = [t for t in turns if t.get("user") and not t.get("user", "").strip().startswith("/docx")]
        if not valid_turns:
            valid_turns = turns
            
        first_query = valid_turns[0].get("user", "")
        title_slug = slugify(first_query) if first_query else "conversation"
        if not title_slug:
            title_slug = "conversation"
            
        filename = f"{title_slug}_conversation_{timestamp}.docx"
        output_path = os.path.join(export_dir, filename)
        
        lines = []
        lines.append(f"# Conversation: {title_slug.replace('_', ' ').title()}")
        lines.append(f"*Exported on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        lines.append("---")
        
        for idx, turn in enumerate(valid_turns):
            user_text = turn["user"]
            if "<USER_REQUEST>" in user_text:
                user_text = user_text.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
            
            lines.append(f"\n## Turn {idx + 1} - User\n")
            lines.append(user_text)
            lines.append(f"\n## Turn {idx + 1} - Assistant\n")
            lines.append(turn["assistant"])
            lines.append("\n---")
            
        with open(temp_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
    else:
        # Find the last assistant response before this command
        target_turn = None
        for turn in reversed(turns):
            if turn.get("assistant") and not turn.get("user", "").strip().startswith("/docx"):
                target_turn = turn
                break
                
        if not target_turn:
            for turn in reversed(turns):
                if turn.get("assistant"):
                    target_turn = turn
                    break
                    
        if not target_turn:
            print("Error: Could not find any assistant response to export.")
            sys.exit(1)
            
        first_query = target_turn.get("user", "")
        title_slug = slugify(first_query) if first_query else "response"
        if not title_slug:
            title_slug = "response"
            
        filename = f"{title_slug}_last_response_{timestamp}.docx"
        output_path = os.path.join(export_dir, filename)
        
        with open(temp_md_path, "w", encoding="utf-8") as f:
            f.write(target_turn["assistant"])
            
    # Compile temp markdown file to docx using pandoc
    cmd = ["/opt/homebrew/bin/pandoc", "-f", "markdown", "-t", "docx", "-o", output_path, temp_md_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(temp_md_path):
        os.remove(temp_md_path)
        
    if res.returncode == 0:
        if is_whole:
            print(f"Successfully saved whole conversation to: {output_path}")
        else:
            print(f"Successfully saved last response to: {output_path}")
    else:
        print(f"Error compiling conversation to docx via pandoc: {res.stderr}")
        sys.exit(1)

def main():
    # Filter out empty arguments and workflow placeholders
    args = [a for a in sys.argv[1:] if a.strip() and not (a.startswith('$') or a == '""')]
    
    if not args:
        # No arguments: export last response
        export_conversation(is_whole=False)
        return
        
    input_str = " ".join(args).strip()
    
    # Check if input matches an existing file
    possible_paths = [
        input_str,
        os.path.abspath(input_str),
        os.path.join(REPO_ROOT, input_str)
    ]
    
    found_file = None
    for p in possible_paths:
        if os.path.isfile(p):
            found_file = p
            break
            
    if found_file:
        convert_file(found_file)
    else:
        # Check if they specify exporting the conversation
        is_whole = any(kw in input_str.lower() for kw in ["whole", "conversation", "all", "history", "--whole"])
        if is_whole:
            export_conversation(is_whole=True)
        elif input_str.lower() in ["last", "response", "last_response", "--last"]:
            export_conversation(is_whole=False)
        else:
            print(f"Error: Specified input '{input_str}' is neither an existing file path nor a valid export keyword (like 'whole', 'conversation', or 'last').")
            sys.exit(1)

if __name__ == "__main__":
    main()
