import os
import sys
import zipfile
import subprocess


# Get workspace root dynamically
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))

def main():
    zip_path = os.path.join(REPO_ROOT, 'manual_setup.zip')
    
    # 1. Remove the old zip if it exists
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
            print(f"Removed existing manual_setup.zip at {zip_path}")
        except Exception as e:
            print(f"Error removing existing manual_setup.zip: {e}")
            sys.exit(1)
            
    print("Creating manual_setup.zip...")
    
    # Folders to zip
    folders_to_zip = ['.agents', 'preferences', '.claude', '.grok']
    files_to_zip = ['AGENTS.md', 'CLAUDE.md']
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in folders_to_zip:
                folder_path = os.path.join(REPO_ROOT, folder)
                if not os.path.exists(folder_path):
                    print(f"Warning: Folder '{folder}' does not exist, skipping.")
                    continue
                # Walk through the folder
                for root, dirs, files in os.walk(folder_path):
                    # Sort dirs and files to ensure deterministic zip order
                    dirs.sort()
                    files.sort()
                    for file in files:
                        file_path = os.path.join(root, file)
                        # The relative path within the zip archive
                        arcname = os.path.relpath(file_path, REPO_ROOT)
                        zipf.write(file_path, arcname)
            for rel in files_to_zip:
                file_path = os.path.join(REPO_ROOT, rel)
                if not os.path.isfile(file_path):
                    print(f"Warning: File '{rel}' does not exist, skipping.")
                    continue
                zipf.write(file_path, rel)
                        
        print(f"Successfully created manual_setup.zip at: {zip_path}")
        print("This zip file includes the '.agents/', 'preferences/', '.claude/', and '.grok/' folders, and the 'AGENTS.md' and 'CLAUDE.md' files, offering users an easy way to set up manually.")
        
        # Git integration: Add, commit, and push if it's a git repository
        git_dir = os.path.join(REPO_ROOT, '.git')
        if os.path.exists(git_dir):
            try:
                # Verify if git is inside a worktree
                res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=REPO_ROOT, capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip() == "true":
                    # Check if manual_setup.zip has any modifications/additions/deletions compared to HEAD
                    status_res = subprocess.run(["git", "status", "--porcelain", "manual_setup.zip"], cwd=REPO_ROOT, capture_output=True, text=True)
                    if status_res.stdout.strip():
                        print("Git repository detected. Staging manual_setup.zip...")
                        subprocess.run(["git", "add", "manual_setup.zip"], cwd=REPO_ROOT, check=True)
                        
                        print("Committing manual_setup.zip...")
                        subprocess.run(["git", "commit", "-m", "Update manual_setup.zip with latest configurations"], cwd=REPO_ROOT, check=True)
                        
                        # Check if a remote origin is configured
                        remote_check = subprocess.run(["git", "config", "--get", "remote.origin.url"], cwd=REPO_ROOT, capture_output=True, text=True)
                        if remote_check.stdout.strip():
                            print("Pushing manual_setup.zip to remote repository...")
                            subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True)
                            print("Successfully pushed manual_setup.zip to remote.")
                        else:
                            print("No remote origin configured, skipping git push.")
                    else:
                        print("manual_setup.zip has no changes. Skipping git stage/commit/push.")
            except subprocess.CalledProcessError as e:
                print(f"Git command failed: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error during git integration: {e}", file=sys.stderr)
                
    except Exception as e:
        print(f"Error creating zip file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
