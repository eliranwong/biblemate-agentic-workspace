import os
import sys
import subprocess
import tempfile

WORKSPACE = "/Users/admin/dev/antigravity-biblemate-workspace"
FOLDER = "/Users/admin/dev/antigravity-biblemate-workspace/biblemate/2026-06-21-17-34-29_super_john_3_16_exegetical_and_theological_study"
ORCHESTRATOR = os.path.join(WORKSPACE, ".agents", "skills", "biblemate-super", "biblemate_super_orchestrator.py")

# Paths to retrievers
BIBLE_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "bible", "bible_retriever.py")
ORIGINAL_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "original", "original_retriever.py")
INTERLINEAR_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "interlinear", "interlinear_retriever.py")
MORPHOLOGY_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "morphology", "morphology_retriever.py")
XREFS_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "xrefs", "xrefs_retriever.py")
COMMENTARY_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "commentary", "commentary_retriever.py")
LEXICON_SCRIPT = os.path.join(WORKSPACE, ".agents", "skills", "lexicon", "lexicon_retriever.py")

def run_cmd(args):
    res = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    return res.stdout

def save_step(step_num, skill_name, content, sub_skill=None):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
        f.write(content)
        tmp_path = f.name
    
    cmd = [sys.executable, ORCHESTRATOR, "--save-step", FOLDER, str(step_num).zfill(3), skill_name, tmp_path]
    if sub_skill:
        cmd += ["--sub-skill", sub_skill]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp_path)
    print(res.stdout, res.stderr)

def main():
    print("Starting retrieval execution...")
    
    # Step 1: bible
    print("Step 1: bible")
    out = run_cmd([sys.executable, BIBLE_SCRIPT, "NASB2020", "ESV2016", "KJV", "CUV", "John 3:1-21"])
    save_step(1, "bible", out)
    
    # Step 2: original
    print("Step 2: original")
    out = run_cmd([sys.executable, ORIGINAL_SCRIPT, "John 3:16"])
    save_step(2, "original", out)
    
    # Step 3: interlinear
    print("Step 3: interlinear")
    out = run_cmd([sys.executable, INTERLINEAR_SCRIPT, "John 3:16"])
    save_step(3, "interlinear", out)
    
    # Step 4: morphology
    print("Step 4: morphology")
    out = run_cmd([sys.executable, MORPHOLOGY_SCRIPT, "John 3:16"])
    save_step(4, "morphology", out)
    
    # Step 5: xrefs
    print("Step 5: xrefs")
    out = run_cmd([sys.executable, XREFS_SCRIPT, "John 3:16"])
    save_step(5, "xrefs", out)
    
    # Step 6: commentary (calvin)
    print("Step 6: commentary (CALVIN)")
    out = run_cmd([sys.executable, COMMENTARY_SCRIPT, "CALVIN", "John 3:16"])
    save_step(6, "commentary", out, "calvin")
    
    # Step 7: commentary (jfb)
    print("Step 7: commentary (JFB)")
    out = run_cmd([sys.executable, COMMENTARY_SCRIPT, "JFB", "John 3:16"])
    save_step(7, "commentary", out, "jfb")
    
    # Step 8: commentary (henry)
    print("Step 8: commentary (HENRY)")
    out = run_cmd([sys.executable, COMMENTARY_SCRIPT, "HENRY", "John 3:16"])
    save_step(8, "commentary", out, "henry")
    
    # Step 9: commentary (constable)
    print("Step 9: commentary (CONSTABLE)")
    out = run_cmd([sys.executable, COMMENTARY_SCRIPT, "CONSTABLE", "John 3:16"])
    save_step(9, "commentary", out, "constable")
    
    # Step 10: commentary (barnes)
    print("Step 10: commentary (BARNES)")
    out = run_cmd([sys.executable, COMMENTARY_SCRIPT, "BARNES", "John 3:16"])
    save_step(10, "commentary", out, "barnes")
    
    # Step 11: commentary (lange)
    print("Step 11: commentary (LANGE)")
    out = run_cmd([sys.executable, COMMENTARY_SCRIPT, "LANGE", "John 3:16"])
    save_step(11, "commentary", out, "lange")
    
    # Step 12: lexicon
    print("Step 12: lexicon")
    # G3439, G4100, G2222, G166, G156, G243
    out = run_cmd([sys.executable, LEXICON_SCRIPT, "THAYER", "G3439 G4100 G2222 G166 G156 G243"])
    save_step(12, "lexicon", out)
    
    print("Retrieval execution complete!")

if __name__ == "__main__":
    main()
