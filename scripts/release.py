#!/usr/bin/env python3
import sys
import subprocess
import fileinput
import os

def run_command(cmd, shell=False):
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.check_call(cmd, shell=shell)

def update_version(new_version):
    """Updates version in pyproject.toml using simple string replacement to preserve formatting."""
    file_path = "pyproject.toml"
    found = False
    
    # Read all lines
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    with open(file_path, 'w') as f:
        for line in lines:
            if line.strip().startswith("version =") and not found:
                # Assuming first "version =" is the project version
                f.write(f'version = "{new_version}"\n')
                found = True
            else:
                f.write(line)
    
    if not found:
        print("Error: Could not find 'version =' in pyproject.toml")
        sys.exit(1)
    
    print(f"Updated pyproject.toml to version {new_version}")

def get_current_version():
    """Reads version from pyproject.toml"""
    with open("pyproject.toml", "r") as f:
        for line in f:
            if line.strip().startswith("version ="):
                # Extract version string: version = "0.3.0" -> 0.3.0
                return line.split('=')[1].strip().strip('"\'')
    print("Error: Could not find current version in pyproject.toml")
    sys.exit(1)

def increment_patch_version(version):
    parts = version.split('.')
    if len(parts) >= 3:
        # standard semantic versioning
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except ValueError:
            pass # Non-integer patch version
            
    print(f"Error: Could not auto-increment version '{version}'. It doesn't look like x.y.z")
    sys.exit(1)

def main():
    if len(sys.argv) == 2:
        new_version = sys.argv[1]
    else:
        current = get_current_version()
        new_version = increment_patch_version(current)
        print(f"Auto-detected current version: {current}")
        print(f"Bumping to new version: {new_version}")
        
        confirm = input("Continue? [Y/n] ")
        if confirm.lower() == 'n':
            sys.exit(0)
    
    # Validate version format (simple check)
    if not new_version.replace('.', '').isdigit():
        print("Warning: Version doesn't look like x.y.z")
        
    tag = f"v{new_version}"
    
    print(f"Preparing release {tag}...")
    
    # 1. Update pyproject.toml
    update_version(new_version)
    
    # 2. Add file
    run_command(["git", "add", "pyproject.toml"])
    
    # 3. Commit
    msg = f"chore: release {tag}"
    run_command(["git", "commit", "-m", msg])
    
    # 4. Tag
    # Check if tag exists locally
    try:
        subprocess.check_call(["git", "rev-parse", tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Tag {tag} already exists. Deleting local tag to overwrite...")
        run_command(["git", "tag", "-d", tag])
    except subprocess.CalledProcessError:
        pass # Tag doesn't exist, good.
        
    run_command(["git", "tag", tag])
    
    # 5. Push
    print("\nReady to push. Executing: git push origin main --tags")
    try:
        run_command(["git", "push", "origin", "main", "--tags"])
    except subprocess.CalledProcessError:
        print("\nPush failed. Maybe the tag exists on remote? Trying force push for tags...")
        run_command(["git", "push", "origin", "main", "--tags", "--force"])
        
    print(f"\nSUCCESS! Release {tag} triggered.")

if __name__ == "__main__":
    main()
