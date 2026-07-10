import os
import sys
import urllib.request
import zipfile

def main():
    # Get workspace root dynamically
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
    
    # 1. Condition 1: If device os is macOS or Linux
    current_os = sys.platform
    if not (current_os.startswith('linux') or current_os == 'darwin'):
        print(f"Error: Operating system '{current_os}' is not supported. This command only runs on macOS or Linux.")
        sys.exit(1)
        
    # 2. Condition 2: If the workspace folder is NOT `antigravity-biblemate-workspace`
    repo_name = os.path.basename(os.path.normpath(repo_root))
    if repo_name == 'antigravity-biblemate-workspace':
        print("Error: The workspace folder is 'antigravity-biblemate-workspace'. Update command is not allowed to run in the source repository to prevent overwriting files.")
        sys.exit(1)
        
    print(f"Conditions met. Running update in workspace: {repo_root}")
    
    url = "https://github.com/eliranwong/antigravity-biblemate-workspace/raw/main/manual_setup.zip"
    zip_path = os.path.join(repo_root, 'manual_setup.zip')
    
    try:
        # Download
        print(f"Downloading setup archive from {url}...")
        urllib.request.urlretrieve(url, zip_path)
        print("Download complete.")
        
        # Extract using python's built-in zipfile to prevent wrapping folder issues and ensure silent overwrite
        print(f"Extracting archive to {repo_root}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(repo_root)
        print("Extraction complete. Existing configuration files overwritten successfully.")
        
        # Create necessary directories
        print("Creating workspace directories...")
        for folder in ['biblemate', 'notes', 'images', 'export']:
            folder_path = os.path.join(repo_root, folder)
            os.makedirs(folder_path, exist_ok=True)
        print("Workspace directories created/verified.")
        print("Update completed successfully!")
        
    except Exception as e:
        print(f"Error during update process: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up zip file if it exists
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
                print("Cleaned up manual_setup.zip.")
            except Exception as clean_err:
                print(f"Warning: Could not remove temporary zip file: {clean_err}", file=sys.stderr)

if __name__ == '__main__':
    main()
