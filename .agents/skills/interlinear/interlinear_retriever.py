import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIBLE_RETRIEVER = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'bible', 'bible_retriever.py'))

def main():
    args = sys.argv[1:]
    # Prepend OHGBi as the first parameter
    cmd = [sys.executable, BIBLE_RETRIEVER, "OHGBi"] + args
    res = subprocess.run(cmd, capture_output=False)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
