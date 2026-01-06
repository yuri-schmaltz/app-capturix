#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Config
APP_NAME = "linsnipper"
VERSION = "0.2.0"
ARCH = "all"
MAINTAINER = "Your Name <you@example.com>"
DESC = "Screenshot and snipping tool for Linux"
DEPENDS = "python3, python3-pyside6"

BUILD_DIR = Path("build_deb")
PKG_DIR = BUILD_DIR / f"{APP_NAME}_{VERSION}_{ARCH}"
DEBIAN_DIR = PKG_DIR / "DEBIAN"
USR_DIR = PKG_DIR / "usr"
LIB_DIR = USR_DIR / "lib" / "python3" / "dist-packages"
BIN_DIR = USR_DIR / "bin"

def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    PKG_DIR.mkdir(parents=True)
    DEBIAN_DIR.mkdir()
    LIB_DIR.mkdir(parents=True)
    BIN_DIR.mkdir(parents=True)

    print(f"Building {APP_NAME} v{VERSION}...")

    # 1. Install app into build dir
    print("Installing application to build directory...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", ".", 
        f"--target={LIB_DIR}", 
        "--no-deps",  # We rely on system packages or other means
        "--upgrade"
    ])

    # 2. Create Launcher Script (since pip install -t doesn't create bin scripts nicely for us in this structure sometimes, or we want a custom one)
    # Actually, standard pip install usually creates bin scripts if not --target, but with --target it puts them in bin inside target? No.
    # Let's verify where entry points go. with --target, bin scripts might not be generated standardly.
    # Safe bet: Write our own shim.
    
    shim_path = BIN_DIR / APP_NAME
    with open(shim_path, "w") as f:
        f.write(f"""#!/usr/bin/python3
import sys
from pathlib import Path

# Ensure our local lib is found (standard debian paths are typically in path, but just in case)
sys.path.insert(0, "/usr/lib/python3/dist-packages")

from linsnipper.__main__ import main
if __name__ == '__main__':
    sys.exit(main())
""")
    shim_path.chmod(0o755)

    # 3. Create Control File
    control_content = f"""Package: {APP_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {ARCH}
Depends: {DEPENDS}
Maintainer: {MAINTAINER}
Description: {DESC}
 Inspired by Windows Snipping Tool.
"""
    with open(DEBIAN_DIR / "control", "w") as f:
        f.write(control_content)

    # 4. Build .deb
    print("running dpkg-deb...")
    subprocess.check_call(["dpkg-deb", "--build", str(PKG_DIR)])
    
    deb_file = BUILD_DIR / f"{APP_NAME}_{VERSION}_{ARCH}.deb"
    if deb_file.exists():
        print(f"SUCCESS: Package created at {deb_file}")
    else:
        print("ERROR: .deb file not found after build.")
        sys.exit(1)

if __name__ == "__main__":
    main()
